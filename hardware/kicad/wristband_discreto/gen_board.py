#!/usr/bin/env python3
"""gen_board.py — gera wristband_discreto.kicad_pcb (variante discreta nRF52810).

Fluxo determinístico (sem input do usuário):
  1. Parse do netlist exports/wristband_discreto.net (S-expr, regex manual).
  2. Mapa ref->footprint do wristband_discreto.kicad_sch.
  3. Board circular Ø32 mm, centro (100,100), 2 camadas, 0,8 mm.
  4. Placement fixo (tabela abaixo), footprints embutidos no .kicad_pcb.
  5. Nets atribuídas pad a pad; rotas em L no F.Cu; GND = zona B.Cu + vias.
  6. Validação validate_pads_inside_edges + resumo + pendências.

TAG1 NÃO vai no board: o inlay NTAG213 é adesivo na cápsula (pendência
documentada — footprint só existe para o esquemático).

Requer: python3 + pcbnew (KiCad 10). pcbnew imprime asserts inofensivos
de PROPERTY_ENUM no stderr no import — ignorar.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

import pcbnew

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent              # .../hardware/kicad/wristband_discreto
REPO = HERE.parents[2]                              # raiz do repositório
TOOLS_DIR = REPO / "hardware" / "kicad" / "tools"
CUSTOM_LIBS_DIR = REPO / "hardware" / "kicad" / "libs"

NET_FILE = HERE / "exports" / "wristband_discreto.net"
SCH_FILE = HERE / "wristband_discreto.kicad_sch"
OUT_FILE = HERE / "wristband_discreto.kicad_pcb"

sys.path.append(str(TOOLS_DIR))
import board_builder as bb  # noqa: E402  (após sys.path)

# Raiz das libs custom primeiro: resolve 'nibas_wristband:...' por caminho
# completo; libs padrão caem para /usr/share/kicad/footprints (primeiro hit).
bb.FP_LIB_ROOTS.insert(0, str(CUSTOM_LIBS_DIR))

# ---------------------------------------------------------------------------
# Constantes do board
# ---------------------------------------------------------------------------
CENTER_X, CENTER_Y = 100.0, 100.0   # centro do disco (mm)
RADIUS_MM = 16.0                    # raio Edge.Cuts (Ø32 mm)
TRACK_W_MM = 0.2                    # largura padrão de rota
TRACK_W_VDD_MM = 0.5                # largura da rede de alimentação
ZONE_SEGMENTS = 48                  # aproximação poligonal do círculo GND

# Placement em mm relativos ao centro (dx, dy). Ajustes de fino ±2 mm onde a
# tabela original colidia com o Edge.Cuts (ANT1, C8, J1 — pads escapavam do
# raio de 16 mm segundo validate_pads_inside_edges).
PLACEMENT_MM = {
    "BT1": (0.0, 0.0),
    "U1": (0.0, 10.5),
    "ANT1": (9.5, 9.5),      # era (10.5,10.5); pad 2 escapava do círculo
    "L1": (5.2, 10.5),
    "C3": (7.2, 10.5),
    "X1": (-7.0, 10.5),
    "C1": (-5.0, 12.5),
    "C2": (-5.0, 8.5),
    "C5": (2.0, 13.5),
    "C6": (4.0, 13.5),
    "C7": (-2.0, 13.5),
    "C10": (6.0, 13.5),
    "C4": (-7.0, 13.5),
    "C8": (-8.5, 12.5),      # era (-9,13.5); pad escapava do círculo
    "C9": (-9.0, 11.0),
    "L2": (-2.0, 7.5),
    "L3": (-4.0, 7.5),
    "R1": (-10.0, -10.0),
    "TP1": (-12.0, -8.0),
    "TP2": (-12.0, -4.0),
    "TP3": (-12.0, 0.0),
    "TP4": (-12.0, 4.0),
    "J1": (0.0, -11.0),      # era (0,-12); pad 8x8 escapava do círculo
    "SHLD1": (0.0, 0.0),     # escudo de ferrite sobre a bateria (mesmo centro)
}

# Footprints com pad em B.Cu (conectam direto na zona GND de baixo).
B_SIDE_REFS = {"J1", "SHLD1"}
# Pad EP do QFN32 recebe malha de vias própria (não duplicar via no centro).
EP_REF_PIN = ("U1", "33")
EP_VIA_GRID_MM = (-1.2, 0.0, 1.2)   # 3x3 sob o die pad (3,6 mm)


# ---------------------------------------------------------------------------
# Parsers (regex manual, sem lib externa)
# ---------------------------------------------------------------------------
def parse_netlist(path: Path) -> dict[str, list[tuple[str, str]]]:
    """Netlist KiCad (S-expr) -> {nome: [(ref, pin), ...]}.

    - Remove prefixo hierárquico '/' dos nomes (/NET_ANT -> NET_ANT).
    - Descarta redes 'unconnected-...' (sem roteamento).
    """
    txt = path.read_text(encoding="utf-8")
    start = txt.find("(nets")
    if start < 0:
        raise ValueError(f"seção (nets ...) não encontrada em {path}")
    section = txt[start:]

    nets: dict[str, list[tuple[str, str]]] = {}
    # Blocos (net ... ) ficam a 2 tabs; (node ...) aninha dentro.
    for chunk in re.split(r"\n\t{2}\(net\n", section)[1:]:
        m = re.search(r'\(name "([^"]+)"', chunk)
        if not m:
            continue
        name = m.group(1)
        if name.startswith("unconnected-"):
            continue
        name = name.lstrip("/")
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\n\s*\(pin "([^"]+)"', chunk)
        nets.setdefault(name, []).extend((ref, pin) for ref, pin in nodes)
    if not nets:
        raise ValueError(f"nenhuma rede parseada de {path}")
    return nets


def parse_footprints(path: Path) -> dict[str, str]:
    """Esquemático .kicad_sch -> {ref: 'Lib:Footprint'} (instâncias only).

    Instâncias de símbolo abrem com '  (symbol' sozinho na linha (2 espaços,
    sem nome); símbolos de biblioteca (lib_symbols) têm o nome na mesma linha
    e não casam. O split tolera '  )  (symbol' na mesma linha (blocos colados).
    """
    txt = path.read_text(encoding="utf-8")
    out: dict[str, str] = {}
    for chunk in re.split(r" {2}\(symbol\n", txt)[1:]:
        if "(lib_id" not in chunk:
            continue
        ref = re.search(r'\(property "Reference" "([^"]+)"', chunk)
        fp = re.search(r'\(property "Footprint" "([^"]*)"', chunk)
        if not ref or not fp:
            continue
        ref_id, fp_id = ref.group(1), fp.group(1)
        if not fp_id or ref_id.startswith("#"):  # power symbols / flags
            continue
        out[ref_id] = fp_id
    if not out:
        raise ValueError(f"nenhuma instância com Footprint parseada de {path}")
    return out


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_board() -> tuple["pcbnew.BOARD", dict[str, "pcbnew.FOOTPRINT"], list[str]]:
    """Cria board, posiciona footprints e atribui nets. Retorna (board, fps, pendências)."""
    nets = parse_netlist(NET_FILE)
    fp_map = parse_footprints(SCH_FILE)
    pendencias: list[str] = []

    board = bb.create_board(shape="circle", diameter_mm=2 * RADIUS_MM, layers=2, thickness_mm=0.8)
    # create_board centra na origem; move o círculo Edge.Cuts p/ (100,100).
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            d.SetCenter(pcbnew.VECTOR2I(bb._nm(CENTER_X), bb._nm(CENTER_Y)))
            break

    # --- Placement ---------------------------------------------------------
    placed: dict[str, "pcbnew.FOOTPRINT"] = {}
    for ref in sorted(PLACEMENT_MM):
        if ref not in fp_map:
            raise RuntimeError(f"ref {ref!r} da tabela de placement sem Footprint no esquemático")
        dx, dy = PLACEMENT_MM[ref]
        x, y = CENTER_X + dx, CENTER_Y + dy
        layer = "B.Cu" if ref in B_SIDE_REFS else "F.Cu"
        placed[ref] = bb.place_footprint(board, fp_map[ref], x, y, ref=ref, layer=layer)
    # TAG1 deliberadamente fora do board (inlay adesivo na cápsula).

    # --- Atribuição de nets ------------------------------------------------
    for net_name in sorted(nets):
        for ref, pin in nets[net_name]:
            if ref not in placed:
                pendencias.append(f"{net_name}: {ref}.{pin} — footprint não posicionado")
                continue
            try:
                bb.assign_pad_net(placed[ref], pin, board, net_name)
            except Exception as exc:  # pad inexistente etc.
                pendencias.append(f"{net_name}: {ref}.{pin} — falha ao atribuir net ({exc})")

    # --- Rotas F.Cu (exceto GND) -------------------------------------------
    for net_name in sorted(nets):
        if net_name == "GND":
            continue  # GND fecha pela zona B.Cu + vias
        nodes = [(r, p) for r, p in nets[net_name] if r in placed]
        if len(nodes) < 2:
            pendencias.append(f"{net_name}: só {len(nodes)} pad(s) posicionado(s) — não fecha")
            continue
        width = TRACK_W_VDD_MM if net_name == "VDD_BAT" else TRACK_W_MM
        for (ra, pa), (rb, pb) in zip(nodes, nodes[1:]):
            try:
                x1, y1 = bb.pad_position_mm(placed[ra], pa)
                x2, y2 = bb.pad_position_mm(placed[rb], pb)
                # Rota em L: horizontal primeiro, depois vertical.
                bb.add_route(board, net_name, [(x1, y1), (x2, y1), (x2, y2)], width_mm=width)
            except Exception as exc:
                pendencias.append(f"{net_name}: rota {ra}.{pa}->{rb}.{pb} falhou ({exc})")

    # --- GND: zona B.Cu + vias ---------------------------------------------
    pts = [
        (
            CENTER_X + RADIUS_MM * math.cos(2 * math.pi * i / ZONE_SEGMENTS),
            CENTER_Y + RADIUS_MM * math.sin(2 * math.pi * i / ZONE_SEGMENTS),
        )
        for i in range(ZONE_SEGMENTS)
    ]
    bb.add_zone(board, "GND", pts, layer="B.Cu")

    # Via em cada pad GND do F.Cu (capacitores, TP4, U1.20/29, ANT1.2) para
    # descer à zona; pads de B.Cu/ambos (J1, SHLD1) já tocam a zona.
    for ref, pin in nets.get("GND", []):
        if ref not in placed or (ref, pin) == EP_REF_PIN or ref in B_SIDE_REFS:
            continue
        try:
            x, y = bb.pad_position_mm(placed[ref], pin)
            bb.add_via(board, "GND", x, y)
        except Exception as exc:
            pendencias.append(f"GND: via em {ref}.{pin} falhou ({exc})")

    # Malha 3x3 de vias sob o die pad U1.33.
    ux, uy = CENTER_X + PLACEMENT_MM["U1"][0], CENTER_Y + PLACEMENT_MM["U1"][1]
    for ddx in EP_VIA_GRID_MM:
        for ddy in EP_VIA_GRID_MM:
            bb.add_via(board, "GND", ux + ddx, uy + ddy)

    bb.fill_zones(board)
    return board, placed, pendencias


def main() -> int:
    try:
        board, placed, pendencias = build_board()

        # Validação: todos os pads dentro do círculo Edge.Cuts.
        problemas = bb.validate_pads_inside_edges(board)
        if problemas:
            for p in problemas:
                print(f"ERRO validate_pads_inside_edges: {p}", file=sys.stderr)
            return 1

        out = bb.save_board(board, OUT_FILE)

        tracks = [t for t in board.GetTracks() if t.GetClass() == "PCB_TRACK"]
        vias = [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]
        print(f"Board salvo em: {out}")
        print(f"footprints={len(placed)} tracks={len(tracks)} vias={len(vias)} "
              f"zones={len(board.Zones())}")
        print(f"validate_pads_inside_edges: OK (0 problemas)")
        print(bb.board_summary(board))
        if pendencias:
            print(f"PENDÊNCIAS ({len(pendencias)}):", file=sys.stderr)
            for p in pendencias:
                print(f"  - {p}", file=sys.stderr)
            return 1
        print("pendências: nenhuma — todas as nets fecham")
        return 0
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
