#!/usr/bin/env python3
"""Gerador do board da carrier do gateway ESP32.

Board RETÂNGULAR 60×32 mm centro (100,100) (x∈[70,130], y∈[84,116]),
2 camadas, 1,6 mm. Roteamento em L (com checagem de colisão, inflate
0,3 mm) — sem A*. Estrutura copiada de
wristband_modulo/gen_board_modulo.py (parsers, helpers, board_builder).

U1 = ESP32-DevKitC-32E em soquete PinHeader 2x19 P2.54 (comprimento
48,26 mm), eixo longo em X: pads x∈[77.14,122.86], J2 (pads ímpares
1..37) em y=101,27 e J3 (pads pares 2..38) em y=98,73. Mapeamento
símbolo→footprint: pino "J2-x" -> pad 2x-1; "J3-x" -> pad 2x.

NOTA keepout da antena: a extremidade da antena PCB do DevKitC fica no
lado x>124 do board — sem cobre DE ROTA nessa faixa (x∈[124,130], ambas
as camadas), exceto os pads do próprio U1 (J2-19/J3-19 em x≈122,86, de
onde as trilhas saem para oeste). Amostras de segmento a ≤1,0 mm de um
pad do U1 são isentas. A zona GND em B.Cu (spec: retângulo 60×32 inset
0,5 mm) não é bloqueada por este keepout — a restrição vale para trilhas
de rota, como no board da pulseira.
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
BOARD_W, BOARD_H = 60.0, 32.0
# x∈[70,130], y∈[84,116]
EDGE_X0, EDGE_X1 = CENTER_X - BOARD_W / 2, CENTER_X + BOARD_W / 2
EDGE_Y0, EDGE_Y1 = CENTER_Y - BOARD_H / 2, CENTER_Y + BOARD_H / 2

# (x, y, rot_deg, flip) — flip = footprint em B.Cu. Posições ABSOLUTAS da
# ORIGEM do footprint (PinHeader/SW_PUSH têm origem no pad 1; R_0603 é
# centrado). U1 rot 90: pads x∈[77.14,122.86], J2 (ímpares) y=101,27,
# J3 (pares) y=98,73; J2-19/J3-19 no lado leste (antena).
PLACEMENT = {
    # Soquete do DevKitC: PinHeader 2x19 P2.54 (48,26 mm), eixo longo em X,
    # pads x∈[77.14,122.86], y=100±1.27. Antena na extremidade x>124.
    "U1": (77.14, 101.27, 90.0, False),
    # Entrada de alimentação 5V (USB-C power-only ou terminal 2p), rot 0.
    # y=112: courtyard chegava a y=116.365 — 0,365 mm FORA da borda y=116
    # (auditoria visual). y=110: courtyard y<=114.365 (1,635 dentro), mas o
    # +5V não tem L livre (y=110 cruza SW1.1 [108.5,110.5]; o L alternativo
    # corre na linha y=101.27 dos pads J2). y=111: courtyard y<=115.365
    # (0,635 >= 0,5 dentro da borda) e o L horizontal y=111 limpa SW1.1
    # com 0,25 mm.
    "J1": (75.0, 111.0, 0.0, False),
    # Pull-up +3V3 -> EN.
    "R1": (78.855, 108.0, 0.0, False),
    # Botão EN -> GND (reset), push 6 mm.
    "SW1": (84.0, 109.5, 0.0, False),
}

# Keepout da antena (frame do board): x∈[124,130], y∈[84,116] — sem cobre
# de rota nas duas camadas, exceto pads do próprio U1 (isenção 1,0 mm).
KEEPOUT_ANT = (124.0, EDGE_Y0, EDGE_X1, EDGE_Y1)  # x0, y0, x1, y1
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
    return bb.pad_position_mm(fp, str(pin))


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
    """Pino do símbolo -> PAD do footprint.

    "J2-x" -> pad ímpar 2x-1 (coluna J2); "J3-x" -> pad par 2x (coluna J3).
    Sufixo "b" (ex.: "1b") -> segundo pad com o mesmo número (footprints
    com pads espelhados, ex.: SW_PUSH 4 pads). Demais nomes passam direto.
    """
    s = str(pin)
    second = s.endswith("b")
    if second:
        s = s[:-1]
    m = re.fullmatch(r"J([23])-(\d+)", s)
    if m:
        x = int(m.group(2))
        s = str(2 * x - 1) if m.group(1) == "2" else str(2 * x)
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
# Nomes de net pós-parse (lstrip "/"): "/EN" -> "EN".
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
_GND_STITCH_OFFSET_MM = 0.8
_GND_STITCH_VIA_DIA_MM = 0.8
# Zona GND: retângulo 60×32 com inset 0,5 mm da borda.
_ZONE_INSET_MM = 0.5


def add_ground(board, placed, routed_tracks) -> tuple:
    """Via de costura (trilha 0,3 pad→via Ø0,8 mm a 0,8 mm, 8 direções) para
    cada pad GND em F.Cu (J1.2, SW1.2, U1.J2-14/J3-1/J3-7); zona GND
    retangular 60×32 inset 0,5 mm em B.Cu + fill. Via deve caber inteira
    dentro da zona (inset 0,5 + raio da via 0,4 + margem 0,3 da borda da
    zona). Retorna (n_vias_gnd, pendencias)."""
    gnd = "GND"
    n_vias = 0
    pendencias = []
    via_r = _GND_STITCH_VIA_DIA_MM / 2.0
    margin = _ZONE_INSET_MM + via_r + 0.3
    vx_min, vx_max = EDGE_X0 + margin, EDGE_X1 - margin
    vy_min, vy_max = EDGE_Y0 + margin, EDGE_Y1 - margin
    u1_pads = _u1_pad_centers(placed)
    for ref in sorted(placed):
        fp = placed[ref]
        for pad in fp.Pads():
            if pad.GetNetname() != gnd:
                continue
            if pad.GetLayer() == pcbnew.B_Cu:
                continue  # zona em B.Cu alcança o pad diretamente
            pin = pad.GetNumber()
            px, py = pad_abs_pos(fp, pin)
            base = math.atan2(py - CENTER_Y, px - CENTER_X)
            for k in range(8):
                ang = base + math.pi + k * math.pi / 4.0
                vx = px + _GND_STITCH_OFFSET_MM * math.cos(ang)
                vy = py + _GND_STITCH_OFFSET_MM * math.sin(ang)
                if not (vx_min <= vx <= vx_max and vy_min <= vy <= vy_max):
                    continue
                if in_keepout_rect(vx, vy) and not any(
                        math.hypot(vx - ux, vy - uy) <= _KEEPOUT_PAD_EXEMPT_MM
                        for ux, uy in u1_pads):
                    continue
                if not _clear_of_other_nets(placed, vx, vy, gnd, routed_tracks):
                    continue
                if not _seg_clear_of_other_nets(placed, px, py, vx, vy, gnd,
                                                routed_tracks, item_half=0.15):
                    continue
                bb.add_track(board, gnd, px, py, vx, vy, layer="F.Cu",
                             width_mm=_GND_STITCH_TRACK_MM)
                routed_tracks.append((px, py, vx, vy, 0, gnd,
                                      _GND_STITCH_TRACK_MM))
                bb.add_via(board, gnd, vx, vy,
                           diameter_mm=_GND_STITCH_VIA_DIA_MM)
                _ALL_VIAS.append((vx, vy, gnd))
                n_vias += 1
                break
            else:
                pendencias.append((f"{ref}.{pin}",
                                   "nenhuma das 8 direções livre (via+trilha)"))

    # Zona GND retangular 60×32 inset 0,5 mm da borda (x∈[70.5,129.5],
    # y∈[84.5,115.5]) em B.Cu + fill.
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
        placed[ref] = bb.place_footprint(
            board, fp_map[ref], x, y,
            rot_deg=rot, ref=ref, layer="B.Cu" if flip else "F.Cu"
        )

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


if __name__ == "__main__":
    board, placed, nets_assigned, nets = build_board()
    routed_tracks, pendencias = route_all(board, placed, nets)
    gnd_vias, gnd_pend = add_ground(board, placed, routed_tracks)
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")

    # --- Asserts de geometria (60x32 + courtyard dentro da borda) ---
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
    # Courtyard de cada footprint dentro da borda; J1 (item da correção)
    # exige >= 0,5 mm de margem (tocava/cruzava y=116 em y=112).
    for ref, fp in placed.items():
        for ly in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cr = fp.GetCourtyard(ly)
            if cr.IsEmpty():
                continue
            bbx = cr.BBox()
            x0, x1 = bb._mm(bbx.GetLeft()), bb._mm(bbx.GetRight())
            y0, y1 = bb._mm(bbx.GetTop()), bb._mm(bbx.GetBottom())
            margem = 0.5 if ref == "J1" else 0.0
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
    print(f"assert 60x32: Edge.Cuts {w:.6f}x{h:.6f} mm, "
          f"x∈[{min(xs):.3f},{max(xs):.3f}] y∈[{min(ys):.3f},{max(ys):.3f}] OK")
    print(f"assert courtyard: todos os footprints >= 0,5 mm dentro da borda OK")
    print(f"board salvo em: {out}")
