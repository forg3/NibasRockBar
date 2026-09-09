#!/usr/bin/env python3
"""Gerador do board da pulseira — variante A (módulo certificado E73).

Board circular Ø32 mm em (100,100), 2 camadas, 0,8 mm. Roteamento em L
(com checagem de colisão, inflate 0,3 mm) — sem A*.

NOTA 4 do esquemático: keep-out de cobre sob a antena PCB integrada do
módulo é y < -8,85 mm DA ORIGEM DO FOOTPRINT RF_Module:E73-2G4M04S, ou
seja, no frame LOCAL do footprint (a extremidade sem pads, local
y = -14,35, é a antena). Com U1 em (0,0) rot 90, o mapeamento verificado
pelos pads no board é rel = (y_local, -x_local): o eixo longo fica em X
e a antena na extremidade x = -14,35 (oeste). Keepout no frame do board:
x∈[-15,5,-8,85], y∈[-9,9]. A versão anterior (x∈[-9,9],
y∈[-15,5,-8,85]) assumia eixo longo em Y — refutado pelas posições reais
dos pads (U1.16 em rel (14.35, 6.985), U1.37 em (1.17, -8.75)).

BT1 (holder CR2032, rot 90) SOBREPÕE o módulo U1: impossibilidade física do
Ø32 mm (holder 15,24×30,48 + módulo 17,5×28,7 não cabem lado a lado no
disco). Documentado; os pads reais do holder ficam nas laterais e é neles
que o roteamento colide — o courtyard não é obstáculo de rota.
"""
import math
import re
import sys
from pathlib import Path

import pcbnew

sys.path.append("/home/forg3/projetos/NibasRockBar/hardware/kicad/tools")
import board_builder as bb

HERE = Path(__file__).resolve().parent              # .../wristband_modulo
REPO = HERE.parents[2]
CUSTOM_LIBS_DIR = REPO / "hardware" / "kicad" / "libs"
SCH_FILE = HERE / "wristband_modulo.kicad_sch"
NET_FILE = HERE / "exports" / "wristband_modulo.net"
OUT_FILE = HERE / "wristband_modulo.kicad_pcb"
bb.FP_LIB_ROOTS.insert(0, str(CUSTOM_LIBS_DIR))


# ---------------------------------------------------------------------------
# Parsers (copiados de wristband_discreto/gen_board_v2.py)
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
        nodes = re.findall(r'\(ref "([^"]+)"\)\s*\n\s*\(pin "([^"]+)"', chunk)
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
# Placement (mm relativos ao centro do disco)
# ---------------------------------------------------------------------------
CENTER_X, CENTER_Y = 100.0, 100.0

# (dx, dy, rot_deg, flip) — flip = footprint em B.Cu.
PLACEMENT = {
    # Módulo E73 17,5×28,7 rot 90: eixo longo em Y, corpo x∈[-8.75,8.75],
    # y∈[-14.35,14.35]. Antena na extremidade y negativa (NOTA 4).
    "U1": (0.0, 0.0, 90.0, False),
    # Holder CR2032 rot 90 (courtyard 15,24×30,48 rotacionado) — sobrepõe o
    # módulo (impossibilidade física Ø32, documentada no docstring).
    "BT1": (0.0, 0.0, 90.0, False),
    # Decoupling VDD: bolsa norte (fora dos courtyards U1/BT1, dentro do
    # disco r=16); rotas em L descem do corredor y=+10.16 (centro do BT1.1).
    # C1/C2 rebaixados/reposicionados: o canto do pad GND (C1.2/C2.2)
    # encostava na margem de 0,5 mm da borda r=16 (copper_edge_clearance) e
    # as 8 direções de via de costura ficavam bloqueadas. C1 y=10.7 / C2
    # (7.0,11.7): cantos a r<=15,48, via de costura livre e courtyards de
    # C1×C2 sem sobreposição (folga 0,11 mm).
    "C1": (9.5, 10.7, 0.0, False),
    "C2": (7.0, 11.7, 0.0, False),
    # Verso: contato negativo da bateria (GND) e ferrite sob a bateria.
    # J1 em y=-11: pad de 8 mm (meia-largura 4,0) alcançava r=17 em y=-13 —
    # 1 mm FORA do disco (DRC copper_edge_clearance). Em y=-11 o pad chega a
    # r=15,52 (clearance 0,48 < 0,5 — ainda violação); y=-10.9 dá canto em
    # r=15,43 (clearance 0,57) sem courtyard próprio (J1 não tem CrtYd).
    "J1": (0.0, -10.9, 0.0, True),
    "SHLD1": (0.0, 0.0, 0.0, True),
    # Test pads: TP1 (VDD) na bolsa nordeste (x > 7.62 do courtyard do BT1,
    # y > 9.1 do courtyard do U1); TP2-4 na faixa sul (y < -9.95, livre do
    # muro de pads do módulo; TP4 fora do corredor y=-12 do TP3).
    "TP1": (-9.5, 9.9, 0.0, False),
    "TP2": (9.0, -12.0, 0.0, False),
    "TP3": (10.5, -10.0, 0.0, False),
    "TP4": (6.0, -13.5, 0.0, False),
    # TAG1 NÃO vai no board: inlay NTAG213 é adesivo na cápsula.
}

# Keepout da antena (NOTA 4): sem cobre nas duas camadas, exceto os pads do
# próprio U1. Coordenadas mm RELATIVAS ao centro do disco. NOTA 4 é no frame
# local do footprint (y_local < -8,85); com rot 90 (rel = (y_local, -x_local),
# verificado nos pads) vira x∈[-15,5,-8,85], y∈[-9,9] — extremidade oeste,
# onde está o fim sem pads (antena).
KEEPOUT_ANT = (-15.5, -9.0, -8.85, 9.0)  # x0, y0, x1, y1


def in_keepout_rect(x, y) -> bool:
    x0, y0, x1, y1 = KEEPOUT_ANT
    return x0 <= x <= x1 and y0 <= y <= y1


# ---------------------------------------------------------------------------
# Geometria (copiada/adaptada de gen_board_v2.py)
# ---------------------------------------------------------------------------
_PAD_LAYER_NODE = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 1}
_ALL_VIAS = []  # [(x, y, net), ...]


def pad_abs_pos(fp, pin) -> tuple:
    return bb.pad_position_mm(fp, str(pin))


def _pad_rect(fp, pad) -> tuple:
    cx, cy = pad_abs_pos(fp, pad.GetNumber())
    return (cx, cy, bb._mm(pad.GetSizeX()), bb._mm(pad.GetSizeY()),
            math.radians(pad.GetOrientationDegrees()))


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
                             item_half=0.15, clearance=0.2,
                             layer=pcbnew.F_Cu) -> bool:
    """True se o segmento (meia-largura item_half) respeita clearance contra
    trilhas, vias e pads (retângulo) de outras nets NA CAMADA `layer`. Pads
    SEM rede (NC) também bloqueiam. Inflate = item_half + clearance."""
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
            if not pad.IsOnLayer(layer):
                continue  # pad em outra camada não colide com esta rota
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


def _seg_hits_keepout(x1, y1, x2, y2, sample=0.05) -> bool:
    """True se o segmento entra no keepout da antena (qualquer net — as
    trilhas externas nunca podem cruzar; os pads do próprio U1 ficam dentro
    mas as trilhas partem deles para fora)."""
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(math.ceil(length / sample)))
    for k in range(n + 1):
        t = k / n
        if in_keepout_rect(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t):
            return True
    return False


# ---------------------------------------------------------------------------
# Clearance cobre-borda (Edge.Cuts círculo r=16, restrição 0,5 mm)
# ---------------------------------------------------------------------------
_EDGE_CLEAR_MM = 0.5
_EDGE_R_MM = 16.0
_EDGE_EXEMPT_MM = 1.0  # raio de isenção em torno de pads físicos na periferia


def _seg_edge_ok(x1, y1, x2, y2, half_width, exempt_pts) -> bool:
    """True se todo ponto do segmento deixa >= _EDGE_CLEAR_MM entre o cobre
    (centro + half_width, radial) e a borda do disco r=16 — exceto pontos a
    <= _EDGE_EXEMPT_MM de pads fisicamente na periferia (U1.15/16/27/28:
    o cobre do PRÓPRIO pad já invade a margem; a trilha até ele herda a
    violação, documentada como física)."""
    limit = _EDGE_R_MM - _EDGE_CLEAR_MM - half_width
    length = math.hypot(x2 - x1, y2 - y1)
    n = max(1, int(math.ceil(length / 0.05)))
    for k in range(n + 1):
        t = k / n
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if math.hypot(x - CENTER_X, y - CENTER_Y) <= limit:
            continue
        if any(math.hypot(x - ex, y - ey) <= _EDGE_EXEMPT_MM
               for ex, ey in exempt_pts):
            continue
        return False
    return True


# ---------------------------------------------------------------------------
# Roteamento em L (sem A*)
# ---------------------------------------------------------------------------
def _pad_node(fp, pin) -> tuple:
    pad = fp.FindPadByNumber(str(pin))
    layer_node = _PAD_LAYER_NODE.get(pad.GetLayer(), 0)
    x, y = bb.pad_position_mm(fp, pin)
    return (x, y, layer_node)


def _l_shapes(sx, sy, gx, gy):
    """Dois caminhos em L: horizontal-primeiro e vertical-primeiro."""
    return [
        [(sx, sy), (gx, sy), (gx, gy)],
        [(sx, sy), (sx, gy), (gx, gy)],
    ]


def _path_ok(placed, net_name, path, width_mm, routed_tracks, exempt_pts=()):
    """Checa os segmentos do caminho: borda + keepout + colisão (inflate 0,3)."""
    item_half = width_mm / 2.0
    for (ax, ay), (bx, by) in zip(path, path[1:]):
        if math.hypot(bx - ax, by - ay) <= 1e-9:
            continue
        if not _seg_edge_ok(ax, ay, bx, by, item_half, exempt_pts):
            return False
        if _seg_hits_keepout(ax, ay, bx, by):
            return False
        if not _seg_clear_of_other_nets(placed, ax, ay, bx, by, net_name,
                                        routed_tracks, item_half=item_half):
            return False
    return True


def route_pair_l(board, placed, net_name, width_mm, routed_tracks,
                 start, goal):
    """Roteia um par pad→pad em L. Retorna True ou False (pendência)."""
    sx, sy, _sl = start
    gx, gy, _gl = goal
    exempt = [(sx, sy), (gx, gy)]
    for path in _l_shapes(sx, sy, gx, gy):
        if _path_ok(placed, net_name, path, width_mm, routed_tracks, exempt):
            for (ax, ay), (bx, by) in zip(path, path[1:]):
                if math.hypot(bx - ax, by - ay) <= 1e-9:
                    continue
                bb.add_track(board, net_name, ax, ay, bx, by,
                             layer="F.Cu", width_mm=width_mm)
                routed_tracks.append((ax, ay, bx, by, 0, net_name, width_mm))
            return True
    return False


# Pares terminais na ordem pedida. GND fica para a zona (sem trilha).
# BT1.1->U1.16 NÃO está aqui: não existe corredor ortogonal em F.Cu até o
# pad (muro contínuo de pads do módulo + keepout da antena + borda r=16) —
# roteado por B.Cu em route_vdd_u116().
_ROUTE_PAIRS = [
    ("VDD_BAT", 0.5, [("BT1", "1", "C1", "1"),
                      ("C1", "1", "C2", "1"),
                      ("BT1", "1", "TP1", "1")]),
    ("NET_SWDIO", 0.2, [("TP2", "1", "U1", "38")]),
    ("NET_SWDCLK", 0.2, [("TP3", "1", "U1", "37")]),
]


def route_vdd_u116(board, placed, routed_tracks) -> bool:
    """VDD_BAT: BT1.1 -> U1.16 com desvio por B.Cu.

    O pad U1.16 (centro r=15,96; canto a r=16,68) fica encostado na borda do
    disco e atrás do muro de pads do módulo (linha y=8,75 e coluna x=14,35,
    pads de 1,8 mm com passo 1,27 — sem fresta ortogonal). Em F.Cu só dá
    para chegar com cobre FORA do disco (rota antiga: pico r=17,58). Rota
    adotada (desvio por B.Cu):
      F.Cu 0,5: BT1.1 (100,110.16) -> via1 (108,110.16)
      B.Cu  0,5: via1 -> via2 (108,106.985)
      F.Cu 0,2: via2 -> FACE OESTE do pad U1.16 (114.05,106.985).
    O stub termina 0,05 mm DENTRO do pad (face oeste x=114,0): o cobre da
    trilha fica a r<=15,80 — DENTRO do disco (r=16), sem cruzar o
    Edge.Cuts (auditoria visual: trilha cruzava a borda ao terminar no
    CENTRO do pad, r=16,06). A invasão da margem de 0,5 mm (rmax 15,8 >
    15,5) permanece — mesma causa física do pad U1.16 (centro r=15,96,
    inalcançável de dentro da margem); documentada, não é rota fora do
    disco. Corredor y=106.985 é o único limpo: U1.17 (topo y=106.615)
    fica 0,27 mm abaixo da face inferior da trilha; aproximação pelo sul
    ou norte colide com U1.17/U1.15.
    Retorna True ou False (pendência)."""
    start = _pad_node(placed["BT1"], "1")
    goal = _pad_node(placed["U1"], "16")
    sx, sy, _ = start
    gx, gy, _ = goal
    v1 = (CENTER_X + 8.0, CENTER_Y + 10.16)
    v2 = (CENTER_X + 8.0, CENTER_Y + 6.985)
    stub = (CENTER_X + 14.05, CENTER_Y + 6.985)  # 0,05 mm dentro do pad U1.16
    exempt = [(sx, sy), stub, (gx, gy)]
    segs = [
        (sx, sy, v1[0], v1[1], "F.Cu", 0.5),   # sai do BT1.1 para leste
        (v1[0], v1[1], v2[0], v2[1], "B.Cu", 0.5),  # desce por dentro
        (v2[0], v2[1], stub[0], stub[1], "F.Cu", 0.2),  # face oeste do pad
    ]
    for ax, ay, bx, by, layer, w in segs:
        if not _seg_edge_ok(ax, ay, bx, by, w / 2.0, exempt):
            return False
        if _seg_hits_keepout(ax, ay, bx, by):
            return False
        lyr = pcbnew.F_Cu if layer == "F.Cu" else pcbnew.B_Cu
        if not _seg_clear_of_other_nets(placed, ax, ay, bx, by, "VDD_BAT",
                                        routed_tracks, item_half=w / 2.0,
                                        layer=lyr):
            return False
    for vx, vy in (v1, v2):
        if not _clear_of_other_nets(placed, vx, vy, "VDD_BAT",
                                    routed_tracks):
            return False
    for ax, ay, bx, by, layer, w in segs:
        bb.add_track(board, "VDD_BAT", ax, ay, bx, by, layer=layer,
                     width_mm=w)
        ln = 0 if layer == "F.Cu" else 1
        routed_tracks.append((ax, ay, bx, by, ln, "VDD_BAT", w))
    for vx, vy in (v1, v2):
        bb.add_via(board, "VDD_BAT", vx, vy)
        _ALL_VIAS.append((vx, vy, "VDD_BAT"))
    return True


def route_all(board, placed, nets) -> tuple:
    """Roteia as nets de sinal em L. Retorna (routed_tracks, pendencias)."""
    routed_tracks = []
    pendencias = []
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
                                routed_tracks, start, goal):
                pendencias.append((net_name, f"{r0}.{p0}", f"{r1}.{p1}",
                                   "nenhum L livre (keepout/colisão)"))
    if not route_vdd_u116(board, placed, routed_tracks):
        pendencias.append(("VDD_BAT", "BT1.1", "U1.16",
                           "desvio B.Cu bloqueado (borda/keepout/colisão)"))
    return routed_tracks, pendencias


# ---------------------------------------------------------------------------
# Aterramento: vias de costura + zona GND em B.Cu
# ---------------------------------------------------------------------------
_GND_STITCH_TRACK_MM = 0.3
_GND_STITCH_OFFSET_MM = 0.8
_GND_VIA_R_MAX_MM = 14.8  # via r=0,3 -> cobre a r=15,1 (folga 0,9 da borda).
# Cap 14,7 (cobre a r=15,0) testado na iteração 1: o stitch GND de U1.15
# só abre a r=14,785 — com 14,7 fica sem nenhuma das 8 direções (pendência
# + pad GND desconectado). 14,8 mantém o stitch; via max rmax=15,085,
# 0,415 mm dentro do limite DRC (15,5) e não cruza o Edge.Cuts.


def add_ground(board, placed, routed_tracks) -> tuple:
    """Via de costura (trilha 0,3 pad→via a 0,8 mm, 8 direções) para cada pad
    GND em F.Cu; zona GND circular r=16 mm em B.Cu + fill. Pads já em B.Cu
    (J1, SHLD1) são alcançados diretamente pela zona. Malha sob die pad não
    se aplica: módulo sem die pad exposto.
    Retorna (n_vias_gnd, pendencias)."""
    gnd = "GND"
    n_vias = 0
    pendencias = []
    for ref in sorted(placed):
        fp = placed[ref]
        for pad in fp.Pads():
            if pad.GetNetname() != gnd:
                continue
            if pad.IsOnLayer(pcbnew.B_Cu) and not pad.IsOnLayer(pcbnew.F_Cu):
                continue  # pad só em B.Cu: zona alcança diretamente
            pin = pad.GetNumber()
            px, py = pad_abs_pos(fp, pin)
            base = math.atan2(py - CENTER_Y, px - CENTER_X)
            placed_stitch = False
            # Offsets decrescentes: pads encostados em obstáculos (C1.2/C2.2
            # contra pads do U1 e trilhas VDD de 0,5 mm) só abrem via com
            # braço mais curto — via continua a r<=14,8 e dentro da zona.
            for off in (_GND_STITCH_OFFSET_MM, 0.7, 0.6, 0.9):
                for k in range(8):
                    # para DENTRO do disco primeiro: via sempre dentro da
                    # zona GND de B.Cu (r=15,5) e longe da borda do Edge.Cuts.
                    # 8 direções (a cada 45°): pads na periferia (C1.2, C2.2,
                    # U1.15) têm a direção interna bloqueada por colisão —
                    # as diagonais dão alternativas dentro de r <= 14,8.
                    ang = base + math.pi + k * math.pi / 4.0
                    vx = px + off * math.cos(ang)
                    vy = py + off * math.sin(ang)
                    # via (r=0,3) com cobre a r<=15,1 -> centro <= 14,8
                    if math.hypot(vx - CENTER_X, vy - CENTER_Y) > _GND_VIA_R_MAX_MM:
                        continue
                    if not _clear_of_other_nets(placed, vx, vy, gnd, routed_tracks):
                        continue
                    if not _seg_clear_of_other_nets(placed, px, py, vx, vy, gnd,
                                                    routed_tracks, item_half=0.15):
                        continue
                    if not _seg_edge_ok(px, py, vx, vy, 0.15,
                                        [(px, py), (vx, vy)]):
                        continue
                    bb.add_track(board, gnd, px, py, vx, vy, layer="F.Cu",
                                 width_mm=_GND_STITCH_TRACK_MM)
                    routed_tracks.append((px, py, vx, vy, 0, gnd,
                                          _GND_STITCH_TRACK_MM))
                    bb.add_via(board, gnd, vx, vy)
                    _ALL_VIAS.append((vx, vy, gnd))
                    n_vias += 1
                    placed_stitch = True
                    break
                else:
                    continue
                break
            if not placed_stitch:
                pendencias.append((f"{ref}.{pin}",
                                   "nenhuma das 8 direções livre (via+trilha)"))

    # Zona GND r=15,5 (não 16): copper-to-edge clearance 0,5 mm do KiCad —
    # zona em r=16 encostava na borda (21 violações no DRC pós-fix do círculo).
    r = 15.5
    n_seg = 36
    circle = [(CENTER_X + r * math.cos(2.0 * math.pi * i / n_seg),
               CENTER_Y + r * math.sin(2.0 * math.pi * i / n_seg))
              for i in range(n_seg)]
    bb.add_zone(board, gnd, circle, layer="B.Cu")
    bb.fill_zones(board)
    return n_vias, pendencias


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def build_board():
    """Board circular + placement + atribuição de nets."""
    fp_map = parse_footprints(SCH_FILE)
    board = bb.create_board(shape="circle", diameter_mm=32.0, layers=2,
                            thickness_mm=0.8)
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            # Círculo KiCad = centro (start) + ponto na borda (end). SetCenter
            # move SÓ o centro — o end fica em (16,0) mm e o raio explode
            # (~130,6 mm). Replicar create_board: SetRadius via SetEnd na
            # MESMA escala (nm): centro (100,100), end (116,100) → r=16 mm.
            d.SetCenter(pcbnew.VECTOR2I(bb._nm(CENTER_X), bb._nm(CENTER_Y)))
            d.SetEnd(pcbnew.VECTOR2I(bb._nm(CENTER_X + 16.0), bb._nm(CENTER_Y)))
            break

    placed = {}
    for ref in sorted(PLACEMENT):
        if ref not in fp_map:
            raise RuntimeError(f"ref {ref!r} sem Footprint no esquemático")
        dx, dy, rot, flip = PLACEMENT[ref]
        placed[ref] = bb.place_footprint(
            board, fp_map[ref], CENTER_X + dx, CENTER_Y + dy,
            rot_deg=rot, ref=ref, layer="B.Cu" if flip else "F.Cu"
        )

    # SHLD1 (folha de ferrite, mecânica): o footprint traz dois círculos SEM
    # rede em F.Cu e B.Cu que encurtam contra ilhas GND e furam a zona — a
    # conexão GND é só pelo pad. Move os círculos para Fab (desenho
    # mecânico). (Footprint.Remove() corrompe o proxy SWIG dos pads — não usar.)
    shld = placed.get("SHLD1")
    if shld is not None:
        for g in shld.GraphicalItems():
            if g.GetLayer() == pcbnew.F_Cu:
                g.SetLayer(pcbnew.F_Fab)
            elif g.GetLayer() == pcbnew.B_Cu:
                g.SetLayer(pcbnew.B_Fab)

    nets = parse_netlist(NET_FILE)
    nets_assigned = 0
    for net_name in sorted(nets):
        for ref, pin in nets[net_name]:
            if ref not in placed:
                continue  # TAG1 (inlay na cápsula) fica fora do board
            bb.assign_pad_net(placed[ref], pin, board, net_name)
            nets_assigned += 1
    return board, placed, nets_assigned, nets


if __name__ == "__main__":
    board, placed, nets_assigned, nets = build_board()
    routed_tracks, pendencias = route_all(board, placed, nets)
    gnd_vias, gnd_pend = add_ground(board, placed, routed_tracks)
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")

    # --- Asserts de geometria (raio + cap radial de cobre) ---
    edge_r = None
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            c, e = d.GetCenter(), d.GetEnd()
            edge_r = math.hypot(bb._mm(e.x) - bb._mm(c.x),
                                bb._mm(e.y) - bb._mm(c.y))
            assert abs(bb._mm(c.x) - CENTER_X) < 1e-6 and \
                abs(bb._mm(c.y) - CENTER_Y) < 1e-6, "centro Edge.Cuts != (100,100)"
            break
    assert edge_r is not None, "Edge.Cuts circular ausente"
    assert abs(edge_r - 16.0) < 1e-6, f"raio Edge.Cuts {edge_r!r} != 16,0"

    max_trk_r, max_trk_desc = 0.0, ""
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            continue
        s, e = t.GetStart(), t.GetEnd()
        r = max(math.hypot(bb._mm(s.x) - CENTER_X, bb._mm(s.y) - CENTER_Y),
                math.hypot(bb._mm(e.x) - CENTER_X, bb._mm(e.y) - CENTER_Y))
        r += bb._mm(t.GetWidth()) / 2.0
        if r > max_trk_r:
            max_trk_r = r
            max_trk_desc = (f"{t.GetNetname()} F.Cu "
                            f"({bb._mm(s.x):.2f},{bb._mm(s.y):.2f})->"
                            f"({bb._mm(e.x):.2f},{bb._mm(e.y):.2f})")
    max_via_r, max_via_desc = 0.0, ""
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            continue
        p = t.GetPosition()
        r = math.hypot(bb._mm(p.x) - CENTER_X, bb._mm(p.y) - CENTER_Y)
        r += bb._mm(t.GetWidth()) / 2.0
        if r > max_via_r:
            max_via_r = r
            max_via_desc = (f"{t.GetNetname()} "
                            f"({bb._mm(p.x):.2f},{bb._mm(p.y):.2f})")
    # Nenhum cobre de trilha/via FORA do disco (r=16). O stub VDD_BAT->U1.16
    # fica DENTRO (r<=15,8) mas acima do cap 15,2 — causa física do pad
    # U1.16 (centro r=15,96), documentada em route_vdd_u116().
    assert max_trk_r <= 16.0, f"trilha com cobre FORA do disco: {max_trk_desc} r={max_trk_r:.3f}"
    assert max_via_r <= 15.1, f"via com cobre a r={max_via_r:.3f} > 15,1: {max_via_desc}"

    out = bb.save_board(board, OUT_FILE)
    print(f"trilhas roteadas: {len(routed_tracks)}")
    print(f"vias: {n_vias} (GND costura: {gnd_vias})")
    print(f"pendências de rota ({len(pendencias)}): {pendencias}")
    print(f"pendências de via GND ({len(gnd_pend)}): {gnd_pend}")
    print(f"footprints colocados: {len(placed)}")
    print(f"nets atribuídas: {nets_assigned} pads")
    print(f"keepout antena (NOTA 4): {KEEPOUT_ANT} mm rel. ao centro")
    print(f"assert raio: Edge.Cuts r={edge_r:.6f} em ({CENTER_X},{CENTER_Y}) OK")
    print(f"cap radial: trilha max r={max_trk_r:.3f} ({max_trk_desc}); "
          f"via max r={max_via_r:.3f} ({max_via_desc})")
    print(f"board salvo em: {out}")
