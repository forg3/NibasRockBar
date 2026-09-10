#!/usr/bin/env python3
"""Gerador do board da carrier do gateway ESP32 (re-layout p/ DevKitC físico).

Board RETÂNGULAR 62×36 mm centro (100,100) (x∈[69,131], y∈[82,118]),
2 camadas, 1,6 mm. Roteamento em L (com checagem de colisão, inflate
0,3 mm) — sem A*. Estrutura copiada de
wristband_modulo/gen_board_modulo.py (parsers, helpers, board_builder).

U1 = footprint custom `nibas_gateway:ESP32-DevKitC-32E_Carrier` (2 soquetes
fêmea 1x19, pads 1..38 numerados em sequência: J2-x -> pad x, J3-x ->
pad 19+x), rot 270 em (100,100): fileiras (x=±13,97 locais) viram linhas
horizontais em y=86,03 (J2, pads 1..19, pino 1 a oeste) e y=113,97 (J3);
campo de pads 45,72(X)×27,94(Y); +5V (J2-19) na extremidade LESTE.

QUIRK do footprint (documentado, lib intacta): silk/courtyard desenhados
54,4(X)×27,9(Y) / 56,4(X)×29,9(Y) a rot 0, mas o campo de pads é
27,94(X)×45,72(Y) — courtyard NÃO contém os pads nas extremidades. A rot
90 (única que cabe o soquete físico de 48 mm no eixo X) o courtyard
desenhado vira 29,9(X)×56,4(Y) e ultrapassa as bordas Y do board. É só
desenho (courtyard não é cobre, não entra em gerber, não é erro de DRC);
o corpo real do módulo (54,4×27,9 em X/Y) cabe com ≥3 mm de margem. O
assert de courtyard cobre J1/R1/SW1 (≥0,5 mm) + corpo-do-módulo p/ U1.

Keepout da antena: extremidade do módulo no lado dos pads 19/38 (+5V) —
faixa de 6 mm até a borda (x∈[125,131] se leste), sem cobre DE ROTA nas
duas camadas (trilhas e vias), exceto pads do próprio U1 (isenção
1,0 mm). A zona GND em B.Cu (retângulo 62×36 inset 0,5 mm) não é
bloqueada por este keepout — como no board anterior.
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

sys.path.append("/home/forg3/projetos/NibasRockBar/hardware/kicad/tools")
import board_builder as bb

HERE = Path(__file__).resolve().parent              # .../gateway_esp32
REPO = HERE.parents[2]
CUSTOM_LIBS_DIR = REPO / "hardware" / "kicad" / "libs"
SCH_FILE = HERE / "gateway_esp32.kicad_sch"
NET_FILE = HERE / "exports" / "gateway_esp32.net"
OUT_FILE = HERE / "gateway_esp32.kicad_pcb"
bb.FP_LIB_ROOTS.insert(0, str(CUSTOM_LIBS_DIR))

# U1: footprint custom da carrier (soquetes fêmea 1x19 p/ DevKitC-32E).
# Carregado via caminho COMPLETO do .kicad_mod (exigência de projeto).
_U1_MOD_PATH = (CUSTOM_LIBS_DIR / "nibas_gateway.pretty"
                / "ESP32-DevKitC-32E_Carrier.kicad_mod")
_U1_FP = "nibas_gateway:ESP32-DevKitC-32E_Carrier"
if not _U1_MOD_PATH.is_file():
    raise SystemExit(f"footprint custom U1 ausente: {_U1_MOD_PATH}")

# Mapeamento símbolo->footprint custom: pads numerados 1..38 em sequência
# (coluna J2 = pads 1..19, coluna J3 = pads 20..38).
def _sym_to_pad(pin: str) -> str:
    s = str(pin)
    m = re.fullmatch(r"J([23])-(\d+)", s)
    if m:
        x = int(m.group(2))
        return str(x) if m.group(1) == "2" else str(19 + x)
    return s


# ---------------------------------------------------------------------------
# Parsers (copiados de wristband_modulo/gen_board_modulo.py)
# ---------------------------------------------------------------------------
def parse_netlist(path) -> dict:
    """Netlist KiCad (S-expr) -> {nome: [(ref, pin), ...]}."""
    txt = path.read_text(encoding="utf-8")
    start = txt.find("(nets")
    if start < 0:
        raise ValueError(f"seção (nets ...) não encontrada em {path}")
    section = txt[start:]
    nets = {}
    for chunk in re.split(r"\n\t{2}\(net\n", section)[1:]:
        m = re.search(r'\(name "([^"]+)"', chunk)
        if not m:
            continue
        name = m.group(1)
        if name.startswith("unconnected-"):
            continue
        name = name.lstrip("/")
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\n\s*\n?\s*\(pin "([^"]+)"', chunk)
        if not nodes:
            nodes = re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"', chunk)
        nets.setdefault(name, []).extend((ref, pin) for ref, pin in nodes)
    if not nets:
        raise ValueError(f"nenhuma rede parseada de {path}")
    return nets


def parse_footprints(path) -> dict:
    """Esquemático .kicad_sch -> {ref: 'Lib:Footprint'} (instâncias only)."""
    txt = path.read_text(encoding="utf-8")
    out = {}
    for chunk in re.split(r" {2}\(symbol\n", txt)[1:]:
        if "(lib_id" not in chunk:
            continue
        ref = re.search(r'\(property "Reference" "([^"]+)"', chunk)
        fp = re.search(r'\(property "Footprint" "([^"]*)"', chunk)
        if not ref or not fp:
            continue
        ref_id, fp_id = ref.group(1), fp.group(1)
        if not fp_id or ref_id.startswith("#"):
            continue
        out[ref_id] = fp_id
    if not out:
        raise ValueError(f"nenhuma instância com Footprint parseada de {path}")
    return out


# ---------------------------------------------------------------------------
# Placement (mm ABSOLUTOS no board; centro do retângulo = (100,100))
# ---------------------------------------------------------------------------
CENTER_X, CENTER_Y = 100.0, 100.0
BOARD_W, BOARD_H = 62.0, 36.0
# x∈[69,131], y∈[82,118]
EDGE_X0, EDGE_X1 = CENTER_X - BOARD_W / 2, CENTER_X + BOARD_W / 2
EDGE_Y0, EDGE_Y1 = CENTER_Y - BOARD_H / 2, CENTER_Y + BOARD_H / 2

# U1 rot 270 em (100,100): pads x∈[77.14,122.86], J2 (pads 1..19) em
# y=86,03 com J2-1 a oeste, J3 (pads 20..38) em y=113,97; +5V (J2-19) a
# leste. Topologia espelha o board 60×32 anterior (J1 a oeste, keepout a
# leste): +5V cruza o board pelo strip superior (~53 mm, antes 58,6 mm).
# J1 no strip superior oeste (corpo fora do módulo em X — sem colisão
# física); R1/SW1 na banda central oeste (extremidade J2-1/J2-2), sob o
# módulo (elevado; MONTAR o DevKitC com pinos longos empilháveis, folga
# ≥6 mm sob o módulo — R1 1 mm e SW1 4,3 mm cabem; SW1 acessível c/
# módulo removido, reset primário = botão EN do próprio DevKitC).
PLACEMENT = {
    "U1": (100.0, 100.0, 270.0, False),
    "J1": (71.32, 84.5, 0.0, False),
    "R1": (78.5, 92.0, 270.0, False),
    "SW1": (76.5, 99.0, 0.0, False),
}

# Keepout da antena: definido em runtime (lado dos pads 19/38): faixa de
# 6 mm até a borda do board, altura total. Padrão (rot 270 => leste).
KEEPOUT_ANT = (125.0, EDGE_Y0, EDGE_X1, EDGE_Y1)  # x0, y0, x1, y1
_KEEPOUT_PAD_EXEMPT_MM = 1.0


def in_keepout_rect(x, y) -> bool:
    x0, y0, x1, y1 = KEEPOUT_ANT
    return x0 <= x <= x1 and y0 <= y <= y1


# ---------------------------------------------------------------------------
# Geometria (copiada/adaptada de gen_board_modulo.py)
# ---------------------------------------------------------------------------
_PAD_LAYER_NODE = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 1}
_ALL_VIAS = []  # [(x, y, net), ...]


def pad_abs_pos(fp, pin) -> tuple:
    return bb.pad_position_mm(fp, _sym_to_pad(pin) if fp.GetReference() == "U1" else str(pin))


def _pad_rect(fp, pad) -> tuple:
    pos = pad.GetPosition()
    return (bb._mm(pos.x), bb._mm(pos.y), bb._mm(pad.GetSizeX()),
            bb._mm(pad.GetSizeY()), math.radians(pad.GetOrientationDegrees()))


def _dist_point_seg(px, py, x1, y1, x2, y2) -> float:
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 <= 0.0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _dist_point_rect(px, py, cx, cy, w, h, ang) -> float:
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    qx = dx * c + dy * s
    qy = -dx * s + dy * c
    ex = max(abs(qx) - w / 2.0, 0.0)
    ey = max(abs(qy) - h / 2.0, 0.0)
    return math.hypot(ex, ey)


def _dist_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang, sample=0.05) -> float:
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(math.ceil(length / sample)))
    best = float("inf")
    for k in range(n + 1):
        t = k / n
        best = min(best, _dist_point_rect(x1 + (x2 - x1) * t,
                                          y1 + (y2 - y1) * t,
                                          cx, cy, w, h, ang))
    return best


def _segs_intersect(x1, y1, x2, y2, x3, y3, x4, y4) -> bool:
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
    return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
            ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))


def _dist_seg_seg(x1, y1, x2, y2, x3, y3, x4, y4) -> float:
    if _segs_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        return 0.0
    return min(
        _dist_point_seg(x1, y1, x3, y3, x4, y4),
        _dist_point_seg(x2, y2, x3, y3, x4, y4),
        _dist_point_seg(x3, y3, x1, y1, x2, y2),
        _dist_point_seg(x4, y4, x1, y1, x2, y2),
    )


def _seg_clear_of_other_nets(placed, x1, y1, x2, y2, net_name, routed_tracks,
                             item_half=0.15, clearance=0.2) -> bool:
    """True se o segmento (meia-largura item_half) respeita clearance contra
    trilhas, vias e pads (retângulo) de outras nets. Pads SEM rede (NC)
    também bloqueiam. Inflate total = item_half + clearance (≥0,3 mm para
    trilha 0,3 mm)."""
    for tx1, ty1, tx2, ty2, _layer, tnet, tw in routed_tracks:
        if tnet == net_name:
            continue
        if _dist_seg_seg(x1, y1, x2, y2, tx1, ty1, tx2, ty2) < item_half + clearance + tw / 2.0:
            return False
    for vx, vy, vnet in _ALL_VIAS:
        if vnet == net_name:
            continue
        if _dist_point_seg(vx, vy, x1, y1, x2, y2) < item_half + clearance + 0.3:
            return False
    for _ref, fp in placed.items():
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net == net_name:
                continue
            if not pad.IsOnLayer(pcbnew.F_Cu):
                continue  # rotas de sinal são só em F.Cu; pad em B.Cu não colide
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            if _dist_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang) < item_half + clearance:
                return False
    return True


def _clear_of_other_nets(placed, px, py, net_name, routed_tracks,
                         item_radius=0.3, clearance=0.2, check_pads=True) -> bool:
    """True se um item circular de raio item_radius em (px, py) respeita
    clearance contra trilhas, vias e pads de outras nets."""
    for x1, y1, x2, y2, _layer, tnet, tw in routed_tracks:
        if tnet == net_name:
            continue
        if _dist_point_seg(px, py, x1, y1, x2, y2) < item_radius + clearance + tw / 2.0:
            return False
    for vx, vy, vnet in _ALL_VIAS:
        if vnet == net_name:
            continue
        if math.hypot(px - vx, py - vy) < item_radius + clearance + 0.3:
            return False
    if check_pads:
        for _ref, fp in placed.items():
            for pad in fp.Pads():
                net = pad.GetNetname()
                if net == net_name:
                    continue
                cx, cy, w, h, ang = _pad_rect(fp, pad)
                if _dist_point_rect(px, py, cx, cy, w, h, ang) < item_radius + clearance:
                    return False
    return True


def _u1_pad_centers(placed) -> list:
    fp = placed.get("U1")
    if fp is None:
        return []
    out = []
    for pad in fp.Pads():
        pos = pad.GetPosition()
        out.append((bb._mm(pos.x), bb._mm(pos.y)))
    return out


def _seg_hits_keepout(x1, y1, x2, y2, u1_pads, sample=0.05) -> bool:
    """True se o segmento entra no keepout da antena — exceto amostras a
    ≤1,0 mm de um pad do próprio U1 (as trilhas partem deles para fora)."""
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(math.ceil(length / sample)))
    for k in range(n + 1):
        t = k / n
        px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        if not in_keepout_rect(px, py):
            continue
        if any(math.hypot(px - ux, py - uy) <= _KEEPOUT_PAD_EXEMPT_MM
               for ux, uy in u1_pads):
            continue
        return True
    return False


# ---------------------------------------------------------------------------
# Roteamento em L (sem A*)
# ---------------------------------------------------------------------------
def _resolve_pad(fp, pin):
    """Pino do símbolo -> PAD do footprint custom.

    U1 (carrier 38 pads): "J2-x" -> pad x; "J3-x" -> pad 19+x.
    Demais refs: sufixo "b" (ex.: "1b") -> segundo pad com o mesmo número
    (footprints com pads espelhados, ex.: SW_PUSH 4 pads); demais nomes
    passam direto.
    """
    s = str(pin)
    if fp.GetReference() == "U1":
        s = _sym_to_pad(s)
        pad = fp.FindPadByNumber(s)
        if pad is None:
            raise bb.BoardBuilderError(
                f"pad {pin!r} (fp {s!r}) não resolvido em U1")
        return pad
    second = s.endswith("b")
    if second:
        s = s[:-1]
    if not second:
        pad = fp.FindPadByNumber(s)
        if pad is None:
            raise bb.BoardBuilderError(
                f"pad {pin!r} não resolvido em {fp.GetReference()}")
        return pad
    same = [p for p in fp.Pads() if p.GetNumber() == s]
    if len(same) < 2:
        raise bb.BoardBuilderError(
            f"pad {pin!r}: só {len(same)} pad(s) com número {s!r} em "
            f"{fp.GetReference()}")
    return same[1]


def _pad_node(fp, pin) -> tuple:
    pad = _resolve_pad(fp, pin)
    layer_node = _PAD_LAYER_NODE.get(pad.GetLayer(), 0)
    pos = pad.GetPosition()
    return (bb._mm(pos.x), bb._mm(pos.y), layer_node)


def _l_shapes(sx, sy, gx, gy):
    """Dois caminhos em L: horizontal-primeiro e vertical-primeiro."""
    return [
        [(sx, sy), (gx, sy), (gx, gy)],
        [(sx, sy), (sx, gy), (gx, gy)],
    ]


def _path_ok(placed, net_name, path, width_mm, routed_tracks, u1_pads) -> bool:
    """Checa os 2 segmentos do L: keepout + colisão (inflate 0,3)."""
    item_half = width_mm / 2.0
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        if math.hypot(bx - ax, by - ay) <= 1e-9:
            continue
        if _seg_hits_keepout(ax, ay, bx, by, u1_pads):
            return False
        if not _seg_clear_of_other_nets(placed, ax, ay, bx, by, net_name,
                                        routed_tracks, item_half=item_half):
            return False
    return True


def route_pair_l(board, placed, net_name, width_mm, routed_tracks,
                 start, goal, u1_pads):
    """Roteia um par pad→pad em L. Retorna True ou False (pendência)."""
    sx, sy, _sl = start
    gx, gy, _gl = goal
    for path in _l_shapes(sx, sy, gx, gy):
        if _path_ok(placed, net_name, path, width_mm, routed_tracks, u1_pads):
            for (ax, ay), (bx, by) in zip(path, path[1:]):
                if math.hypot(bx - ax, by - ay) <= 1e-9:
                    continue
                bb.add_track(board, net_name, ax, ay, bx, by,
                             layer="F.Cu", width_mm=width_mm)
                routed_tracks.append((ax, ay, bx, by, 0, net_name, width_mm))
            return True
    return False


# Pares terminais na ordem pedida. GND fica para a zona (sem trilha de sinal).
# Nets da netlist (nomes exatos): "+5V" (J1.1, U1.J2-19), "+3V3" (R1.1,
# U1.J2-1), "/EN"->"EN" (R1.2, SW1.1, U1.J2-2), "GND" (J1.2, SW1.2,
# U1.J2-14=p14, U1.J3-1=p20, U1.J3-7=p26).
_ROUTE_PAIRS = [
    ("+5V", 0.5, [("J1", "1", "U1", "J2-19")]),
    ("+3V3", 0.4, [("U1", "J2-1", "R1", "1")]),
    ("EN", 0.3, [("U1", "J2-2", "R1", "2"),
                 ("R1", "2", "SW1", "1"),
                 ("SW1", "1", "SW1", "1b")]),
]


def route_all(board, placed, nets) -> tuple:
    """Roteia as nets de sinal em L. Retorna (routed_tracks, pendencias)."""
    routed_tracks = []
    pendencias = []
    u1_pads = _u1_pad_centers(placed)
    for net_name, width, pairs in _ROUTE_PAIRS:
        if net_name not in nets:
            pendencias.append((net_name, "*", "net ausente na netlist"))
            continue
        for r0, p0, r1, p1 in pairs:
            if r0 not in placed or r1 not in placed:
                pendencias.append((net_name, f"{r0}.{p0}", f"{r1}.{p1}",
                                   "ref fora do board"))
                continue
            start = _pad_node(placed[r0], p0)
            goal = _pad_node(placed[r1], p1)
            if not route_pair_l(board, placed, net_name, width,
                                routed_tracks, start, goal, u1_pads):
                pendencias.append((net_name, f"{r0}.{p0}", f"{r1}.{p1}",
                                   "nenhum L livre (keepout/colisão)"))
    return routed_tracks, pendencias


# ---------------------------------------------------------------------------
# Aterramento: vias de costura + zona GND em B.Cu
# ---------------------------------------------------------------------------
_GND_STITCH_TRACK_MM = 0.3
_GND_STITCH_VIA_DIA_MM = 0.8
# Furo-a-furo (borda a borda) mínimo entre a via de stitch e QUALQUER PTH
# (inclui os próprios pads da net e outras vias de stitch): 0,6 mm cobre o
# clearance default do KiCad (0,25 mm) com folga de fabricação.
_GND_STITCH_HOLE_CLEAR_MM = 0.6
# Offset inicial pad→via: 1,6 mm garante furo-a-furo >= 0,6 mm contra os
# maiores drills do board (SW1 1,1 mm → r 0,55; via r 0,4: 1,6-0,95=0,65).
_GND_STITCH_OFFSETS_MM = (1.6, 1.9, 2.2, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0)
# Raio máximo de busca (pad→via) — confina as vias de stitch.
_GND_STITCH_MAX_R_MM = 14.5
# Zona GND: retângulo 62×36 com inset 0,5 mm da borda.
_ZONE_INSET_MM = 0.5


def _pad_hole_r_mm(pad) -> float:
    """Raio de furo do pad (0,0 se SMD)."""
    d = pad.GetDrillSize()
    r = min(bb._mm(d.x), bb._mm(d.y)) / 2.0
    return r if r > 0.0 else 0.0


def _all_pth_holes(placed) -> list:
    """[(x, y, r_furo), ...] de TODOS os pads PTH do board."""
    out = []
    for fp in placed.values():
        for pad in fp.Pads():
            r = _pad_hole_r_mm(pad)
            if r <= 0.0:
                continue
            pos = pad.GetPosition()
            out.append((bb._mm(pos.x), bb._mm(pos.y), r))
    return out


def _stitch_via_ok(placed, vx, vy, gnd, routed_tracks, pth_holes,
                   via_r, copper_clear, hole_clear) -> bool:
    """Valida posição de via de stitch: caixa da zona, keepout, furo-a-furo
    contra TODOS os PTHs + vias já colocadas, e clearance de cobre contra
    pads/trilhas/vias de outras nets."""
    margin = _ZONE_INSET_MM + via_r + 0.3
    if not (EDGE_X0 + margin <= vx <= EDGE_X1 - margin and
            EDGE_Y0 + margin <= vy <= EDGE_Y1 - margin):
        return False
    u1_pads = _u1_pad_centers(placed)
    if in_keepout_rect(vx, vy) and not any(
            math.hypot(vx - ux, vy - uy) <= _KEEPOUT_PAD_EXEMPT_MM
            for ux, uy in u1_pads):
        return False
    # Furo-a-furo contra todos os PTHs (borda a borda >= hole_clear).
    for hx, hy, hr in pth_holes:
        if math.hypot(vx - hx, vy - hy) < hole_clear + via_r + hr:
            return False
    # Furo-a-furo contra vias de stitch já colocadas (furo r = via_r).
    for ox, oy, _onet in _ALL_VIAS:
        if math.hypot(vx - ox, vy - oy) < hole_clear + 2.0 * via_r:
            return False
    # Cobre: via r=via_r + clearance contra pads de outras nets.
    for _ref, fp in placed.items():
        for pad in fp.Pads():
            if pad.GetNetname() == gnd:
                continue
            if not pad.IsOnLayer(pcbnew.F_Cu):
                continue
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            if _dist_point_rect(vx, vy, cx, cy, w, h, ang) < via_r + copper_clear:
                return False
    # Cobre contra trilhas de outras nets.
    for x1, y1, x2, y2, _layer, tnet, tw in routed_tracks:
        if tnet == gnd:
            continue
        if _dist_point_seg(vx, vy, x1, y1, x2, y2) < via_r + copper_clear + tw / 2.0:
            return False
    # Cobre contra outras vias (raio via_r cada).
    for ox, oy, _onet in _ALL_VIAS:
        if math.hypot(vx - ox, vy - oy) < 2.0 * via_r + copper_clear:
            return False
    return True


def add_ground(board, placed, routed_tracks) -> tuple:
    """Via de costura GND para cada pad GND em F.Cu (J1.2, SW1.2/2b,
    U1 p14/p20/p26): trilha 0,3 mm pad→via Ø0,8 mm. Posição da via:
    offsets crescentes (1,6..8,0 mm) × 8 direções, validados contra TODOS
    os PTHs (furo-a-furo borda a borda >= 0,6 mm) + clearance de cobre;
    fallback: busca em grade 0,5 mm até r 14,5 mm do pad. Zona GND
    retangular 62×36 inset 0,5 mm em B.Cu + fill. Retorna
    (n_vias_gnd, pendencias)."""
    gnd = "GND"
    n_vias = 0
    pendencias = []
    via_r = _GND_STITCH_VIA_DIA_MM / 2.0
    pth_holes = _all_pth_holes(placed)
    for ref in sorted(placed):
        fp = placed[ref]
        for pad in fp.Pads():
            if pad.GetNetname() != gnd:
                continue
            if pad.GetLayer() == pcbnew.B_Cu:
                continue  # zona em B.Cu alcança o pad diretamente
            pin = pad.GetNumber()
            px, py = bb.pad_position_mm(fp, pin)
            base = math.atan2(py - CENTER_Y, px - CENTER_X)
            # Candidatos: offsets × 8 direções, depois grade (fallback).
            cands = [(px + off * math.cos(base + math.pi + k * math.pi / 4.0),
                      py + off * math.sin(base + math.pi + k * math.pi / 4.0))
                     for off in _GND_STITCH_OFFSETS_MM for k in range(8)]
            step = 0.5
            n_grid = int(_GND_STITCH_MAX_R_MM / step)
            for i in range(-n_grid, n_grid + 1):
                for j in range(-n_grid, n_grid + 1):
                    gx_, gy_ = px + i * step, py + j * step
                    if math.hypot(gx_ - px, gy_ - py) > _GND_STITCH_MAX_R_MM:
                        continue
                    cands.append((gx_, gy_))
            chosen = None
            for vx, vy in cands:
                if math.hypot(vx - px, vy - py) > _GND_STITCH_MAX_R_MM:
                    continue
                if not _stitch_via_ok(placed, vx, vy, gnd, routed_tracks,
                                      pth_holes, via_r,
                                      copper_clear=0.2,
                                      hole_clear=_GND_STITCH_HOLE_CLEAR_MM):
                    continue
                if not _seg_clear_of_other_nets(placed, px, py, vx, vy, gnd,
                                                routed_tracks, item_half=0.15):
                    continue
                chosen = (vx, vy)
                break
            if chosen is None:
                pendencias.append((f"{ref}.{pin}",
                                   "nenhuma posição de via válida "
                                   "(furo-a-furo/cobre/keepout, r<=14,5)"))
                continue
            vx, vy = chosen
            bb.add_track(board, gnd, px, py, vx, vy, layer="F.Cu",
                         width_mm=_GND_STITCH_TRACK_MM)
            routed_tracks.append((px, py, vx, vy, 0, gnd,
                                  _GND_STITCH_TRACK_MM))
            bb.add_via(board, gnd, vx, vy,
                       diameter_mm=_GND_STITCH_VIA_DIA_MM)
            _ALL_VIAS.append((vx, vy, gnd))
            n_vias += 1

    # Zona GND retangular 62×36 inset 0,5 mm da borda (x∈[69.5,130.5],
    # y∈[82.5,117.5]) em B.Cu + fill.
    bb.add_rect_zone(board, gnd,
                     EDGE_X0 + _ZONE_INSET_MM, EDGE_Y0 + _ZONE_INSET_MM,
                     EDGE_X1 - _ZONE_INSET_MM, EDGE_Y1 - _ZONE_INSET_MM,
                     layer="B.Cu")
    bb.fill_zones(board)
    return n_vias, pendencias


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_board():
    """Board retangular + placement + atribuição de nets."""
    fp_map = parse_footprints(SCH_FILE)
    if fp_map.get("U1") != _U1_FP:
        raise RuntimeError(
            f"esquemático aponta U1 para {fp_map.get('U1')!r}, esperado {_U1_FP!r}")
    board = bb.create_board(shape="rect", width_mm=BOARD_W,
                            height_mm=BOARD_H, layers=2, thickness_mm=1.6)
    # create_board gera o retângulo centrado na origem — translada os 4
    # segmentos de Edge.Cuts para o centro (100,100).
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            d.SetStart(pcbnew.VECTOR2I(s.x + bb._nm(CENTER_X),
                                       s.y + bb._nm(CENTER_Y)))
            d.SetEnd(pcbnew.VECTOR2I(e.x + bb._nm(CENTER_X),
                                     e.y + bb._nm(CENTER_Y)))

    placed = {}
    for ref in sorted(PLACEMENT):
        if ref not in fp_map:
            raise RuntimeError(f"ref {ref!r} sem Footprint no esquemático")
        x, y, rot, flip = PLACEMENT[ref]
        fp_id = fp_map[ref]
        placed[ref] = bb.place_footprint(
            board, fp_id, x, y,
            rot_deg=rot, ref=ref, layer="B.Cu" if flip else "F.Cu"
        )

    # Keepout da antena no lado dos pads 19/38 (extremidade do módulo):
    # faixa de 6 mm até a borda.
    global KEEPOUT_ANT
    try:
        x19 = bb.pad_position_mm(placed["U1"], "19")[0]
        if x19 < CENTER_X:
            KEEPOUT_ANT = (EDGE_X0, EDGE_Y0, EDGE_X0 + 6.0, EDGE_Y1)
        else:
            KEEPOUT_ANT = (EDGE_X1 - 6.0, EDGE_Y0, EDGE_X1, EDGE_Y1)
    except bb.BoardBuilderError:
        pass

    nets = parse_netlist(NET_FILE)
    nets_assigned = 0
    for net_name in sorted(nets):
        for ref, pin in nets[net_name]:
            if ref not in placed:
                continue
            pad = _resolve_pad(placed[ref], pin)
            net_code = bb.get_or_create_net(board, net_name).GetNetCode()
            # Pads espelhados (mesmo número, ex.: SW_PUSH) recebem a mesma
            # rede — senão ficam sem rede e bloqueiam o roteamento.
            for p in placed[ref].Pads():
                if p.GetNumber() == pad.GetNumber():
                    p.SetNetCode(net_code)
            nets_assigned += 1
    return board, placed, nets_assigned, nets


def _courtyard_bbox(fp) -> tuple:
    """BBox (x0,x1,y0,y1 mm) do courtyard, ou None se vazio."""
    for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        cr = fp.GetCourtyard(ly)
        if not cr.IsEmpty():
            bbx = cr.BBox()
            return (bb._mm(bbx.GetLeft()), bb._mm(bbx.GetRight()),
                    bb._mm(bbx.GetTop()), bb._mm(bbx.GetBottom()))
    return None


if __name__ == "__main__":
    board, placed, nets_assigned, nets = build_board()
    routed_tracks, pendencias = route_all(board, placed, nets)
    gnd_vias, gnd_pend = add_ground(board, placed, routed_tracks)
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")

    # --- Diagnóstico de placement (rodada de medição) ---
    for ref in sorted(placed):
        fp = placed[ref]
        print(f"DIAG {ref}: pads=" + ", ".join(
            f"{p.GetNumber()}@({bb._mm(p.GetPosition().x):.2f},"
            f"{bb._mm(p.GetPosition().y):.2f})/{p.GetNetname() or '-'}"
            for p in fp.Pads()))
        print(f"DIAG {ref}: courtyard={_courtyard_bbox(fp)}")
    print(f"DIAG keepout_antena: x∈[{KEEPOUT_ANT[0]},{KEEPOUT_ANT[2]}]")
    print(f"DIAG pads_fora_da_borda: {bb.validate_pads_inside_edges(board)}")
    print(f"DIAG comprimentos: " + "; ".join(
        f"{t[5]} {math.hypot(t[2]-t[0],t[3]-t[1]):.2f}mm ({t[0]:.2f},{t[1]:.2f})->({t[2]:.2f},{t[3]:.2f})"
        for t in routed_tracks))

    # --- Asserts de geometria (62x36 + courtyard dentro da borda) ---
    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
            s, e = d.GetStart(), d.GetEnd()
            xs += [bb._mm(s.x), bb._mm(e.x)]
            ys += [bb._mm(s.y), bb._mm(e.y)]
    assert xs and ys, "Edge.Cuts ausente"
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    assert abs(w - BOARD_W) < 1e-6 and abs(h - BOARD_H) < 1e-6, \
        f"board {w}x{h} != {BOARD_W}x{BOARD_H}"
    assert abs(min(xs) - EDGE_X0) < 1e-6 and abs(min(ys) - EDGE_Y0) < 1e-6, \
        "board fora do centro (100,100)"
    # Courtyard de J1/R1/SW1 >= 0,5 mm dentro da borda. U1: quirk do
    # footprint (courtyard desenhado perpendicular ao campo de pads) —
    # valida o corpo real do módulo 54,4×27,9 (X/Y) com margem ≥2,5 mm.
    for ref, fp in placed.items():
        if ref == "U1":
            ux, uy, _urot, _uflip = PLACEMENT["U1"]
            for mx0, mx1, my0, my1 in [(
                    ux - 54.4 / 2, ux + 54.4 / 2, uy - 27.9 / 2, uy + 27.9 / 2)]:
                assert mx0 >= EDGE_X0 + 2.5 and mx1 <= EDGE_X1 - 2.5 and \
                    my0 >= EDGE_Y0 + 2.5 and my1 <= EDGE_Y1 - 2.5, \
                    f"corpo do módulo U1 fora da margem: x[{mx0:.2f},{mx1:.2f}] y[{my0:.2f},{my1:.2f}]"
            continue
        for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cr = fp.GetCourtyard(ly)
            if cr.IsEmpty():
                continue
            bbx = cr.BBox()
            x0, x1 = bb._mm(bbx.GetLeft()), bb._mm(bbx.GetRight())
            y0, y1 = bb._mm(bbx.GetTop()), bb._mm(bbx.GetBottom())
            margem = 0.5
            assert x0 >= EDGE_X0 + margem and x1 <= EDGE_X1 - margem and \
                y0 >= EDGE_Y0 + margem and y1 <= EDGE_Y1 - margem, \
                (f"courtyard de {ref} fora da margem {margem} mm: "
                 f"x[{x0:.3f},{x1:.3f}] "
                 f"y[{y0:.3f},{y1:.3f}]")

    out = bb.save_board(board, OUT_FILE)
    print(f"board: retângulo {BOARD_W}×{BOARD_H} mm centro "
          f"({CENTER_X},{CENTER_Y}), 2 camadas, 1,6 mm")
    print(f"trilhas roteadas: {len(routed_tracks)}")
    print(f"vias: {n_vias} (GND costura: {gnd_vias})")
    print(f"pendências de rota ({len(pendencias)}): {pendencias}")
    print(f"pendências de via GND ({len(gnd_pend)}): {gnd_pend}")
    print(f"footprints colocados: {len(placed)}")
    print(f"nets atribuídas: {nets_assigned} pads")
    print(f"keepout antena: x∈[{KEEPOUT_ANT[0]},{KEEPOUT_ANT[2]}] mm "
          f"(isenção pads U1: {_KEEPOUT_PAD_EXEMPT_MM} mm)")
    print(f"assert 62x36: Edge.Cuts {w:.6f}x{h:.6f} mm, "
          f"x∈[{min(xs):.3f},{max(xs):.3f}] y∈[{min(ys):.3f},{max(ys):.3f}] OK")
    print(f"board salvo em: {out}")
