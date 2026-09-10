#!/usr/bin/env python3
import heapq
import itertools
import sys
import re
import math
import gc
from pathlib import Path

import pcbnew

sys.path.append("/home/forg3/projetos/NibasRockBar/hardware/kicad/tools")
import board_builder as bb

# Raiz das libs custom primeiro: resolve 'nibas_wristband:...' por caminho
# completo (<root>/<Lib>.pretty/<Fp>.kicad_mod); libs padrão caem para
# /usr/share/kicad/footprints (primeiro hit em FP_LIB_ROOTS).
HERE = Path(__file__).resolve().parent              # .../wristband_discreto
REPO = HERE.parents[2]                              # raiz do repositório
CUSTOM_LIBS_DIR = REPO / "hardware" / "kicad" / "libs"
SCH_FILE = HERE / "wristband_discreto.kicad_sch"
NET_FILE = HERE / "exports" / "wristband_discreto.net"
OUT_FILE = HERE / "wristband_discreto.kicad_pcb"
bb.FP_LIB_ROOTS.insert(0, str(CUSTOM_LIBS_DIR))


def parse_netlist(path) -> dict:
    """Netlist KiCad (S-expr) -> {nome: [(ref, pin), ...]}.

    - Remove prefixo hierárquico '/' dos nomes (/NET_ANT -> NET_ANT).
    - Descarta redes 'unconnected-...' (sem roteamento).
    """
    txt = path.read_text(encoding="utf-8")
    start = txt.find("(nets")
    if start < 0:
        raise ValueError(f"seção (nets ...) não encontrada em {path}")
    section = txt[start:]

    nets = {}
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


def parse_footprints(path) -> dict:
    """Esquemático .kicad_sch -> {ref: 'Lib:Footprint'} (instâncias only).

    Instâncias de símbolo abrem com '  (symbol' sozinho na linha (2 espaços,
    sem nome); símbolos de biblioteca (lib_symbols) têm o nome na mesma linha
    e não casam. O split tolera '  )  (symbol' na mesma linha (blocos colados).
    """
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
        if not fp_id or ref_id.startswith("#"):  # power symbols / flags
            continue
        out[ref_id] = fp_id
    if not out:
        raise ValueError(f"nenhuma instância com Footprint parseada de {path}")
    return out


# ---------------------------------------------------------------------------
# Placement (mm relativos ao centro do disco)
# ---------------------------------------------------------------------------
CENTER_X, CENTER_Y = 100.0, 100.0   # centro do disco Ø32 mm

# Rotação por ref (graus). BT1 = Keystone 1060 (3 pads): corpo 28,4×22 com
# abas em ±14,655 mm no eixo X nativo. Rot 270° põe a aba VDD (pad 1) no
# NORTE e a aba GND no SUL — com rot 90 a aba GND ficava a 0,11 mm dos pads
# 9-16 do U1 (violacao de clearance); com rot 270 o norte recebe a aba VDD
# (mesma rede de U1.9) e o sul fica livre (J1 DNP removido). Span de cobre
# 29,31+2,59 = 31,90 mm ≤ Ø32; borda externa da aba a r=15,95.
# NOTA FÍSICA: o bounding box do corpo (28,4×22) tem cantos a r≈17,97 —
# "ultrapassam" o disco no papel; a cesta do 1060 é abaulada (H 5,51 mm com
# pilha) e overhang sobre o circuito é prática padrão de suporte tipo cesta
# (componentes ≤1 mm cabem sob ela). Courtyard do footprint enxugado para o
# envelope dos pads (3 retângulos) por esse motivo.
ROTATION = {
    "BT1": 270.0,
    "C5": 90.0,   # vertical: encaixa no corredor oeste entre C2 e U1
}

PLACEMENT = {
    "BT1": (0.0, 0.0),
    # U1 em dy=10.3: topo dos pads da linha superior (0,8 mm de altura) em
    # 113,15 mm — folga 0,21 mm para a aba VDD do BT1 (y≥113,36). Em 10.8/10.4
    # a folga era negativa/0,11 mm (clearance U1.9-16 × aba do BT1).
    "U1": (0.0, 10.3),
    # ANT1 recuada de (11,11) para (9.4,9.4): pad 2 chegava a r=16,6 (fora do
    # disco r=16 após o fix do Edge.Cuts). Em (9.4,9.4) o canto extremo fica
    # a r=15,48 (folga de borda 0,52 mm ≥ 0,5).
    "ANT1": (9.4, 9.4),
    "L1": (6.0, 11.0),
    # C3 de (7.8,9.8) -> (6.0,8.5): em (7.8,9.8) o pad GND (C3.2) colidia com
    # o pad 1 da ANT1 reposicionada (overlap x 107,35..108,56).
    "C3": (6.0, 8.5),
    # X1 de (−6.5,11) -> (−6.2,11): afasta X1.4 (NC) de C8.2 (gap 0,39 mm).
    "X1": (-6.2, 11.0),
    "C1": (-4.5, 12.8),
    "C2": (-4.5, 9.2),
    # C5/C6/C7 saem de y=14.5 (a aba VDD do BT1 ocupa x −1,8..+1,8,
    # y 13,36..15,95 — colidia com os três). C5 vai para o corredor oeste
    # (junto de U1.1); C6/C7 para o corredor leste (x=5.5, deixando o
    # corredor N-S x=104 livre sob a coluna direita do U1).
    "C5": (-4.2, 10.6),
    "C6": (7.0, 12.4),
    "C7": (4.0, 14.4),
    # C10 de (4.5,14.5) -> (4.0,13.5): pad 2 chegava a r=16,03 (fora do disco).
    "C10": (4.5, 13.0),
    # C4 de (−8.5,12.8) -> (−8.0,12.3): pad 1 chegava a r=16,05 (fora do disco).
    "C4": (-6.8, 12.9),
    "C8": (-8.9, 10.5),
    "C9": (-10.5, 8.2),
    # L2 de (−3.5,8) -> (−4.3,8): L2.2 (NET_DCC) colidia com U1.1 (overlap
    # x 97,15..97,72). L3 de (−5.7,8) -> (−6.2,8): L3.2/L2.1 gap 0,05 mm.
    "L2": (-5.4, 8.0),
    "L3": (-8.0, 8.0),
    "R1": (-10.0, -10.0),
    "TP1": (-12.0, -8.0),
    "TP2": (-12.0, -4.0),
    "TP3": (-12.0, 0.0),
    "TP4": (-12.0, 4.0),
    # J1 REMOVIDO (DNP): o conceito de contato negativo no verso foi
    # invalidado pelo Keystone 1060 (pad central + aba GND já cobrem o
    # negativo). Pads sem rota.
    "SHLD1": (0.0, 0.0),
}
# Flip = footprint em B.Cu (place_footprint aplica fp.Flip quando layer="B.Cu").
# SHLD1 no verso: o cobre Ø22 do ferrite em B.Cu com net GND funde com a zona
# GND (mesma net) — em F.Cu ele cruzava trilhas/pads de sinais (shorting_items).
FLIP_REFS = {"SHLD1"}
# TAG1 NÃO vai no board: inlay NTAG213 é adesivo na cápsula.


# ---------------------------------------------------------------------------
# Grade de costura + keepout da antena
# ---------------------------------------------------------------------------
# Keepout da antena: retângulo sem cobre (exceto rede RF). Coordenadas em mm
# RELATIVAS ao centro do disco — mesmo sistema da tabela PLACEMENT.
KEEPOUT_ANT = (8.0, 8.0, 14.0, 14.0)  # x0, y0, x1, y1 mm

# Raio útil da grade (disco Ø32 mm -> r=15 mm).
GRID_R = 15.0

# Redes de RF = as que tocam U1 pino 19 ou qualquer pino de C3/L1/ANT1
# (determinado pela netlist parseada, não hardcoded por nome).
_RF_REFS = {"C3", "L1", "ANT1"}
_RF_PIN = ("U1", "19")
_rf_nets_cache = None


def rf_nets(nets=None) -> set:
    """Nomes das redes de RF a partir da netlist parseada.

    nets: dict de parse_netlist(); se None, parseia NET_FILE (com cache
    em _rf_nets_cache para não reparsear a cada chamada de in_keepout).
    """
    global _rf_nets_cache
    if nets is None:
        if _rf_nets_cache is None:
            _rf_nets_cache = parse_netlist(NET_FILE)
        nets = _rf_nets_cache
    return {
        name
        for name, nodes in nets.items()
        if _RF_PIN in nodes or any(ref in _RF_REFS for ref, _pin in nodes)
    }


def build_grid(step=0.5) -> list:
    """Grade alinhada ao centro (100,100), pontos dentro do círculo r=GRID_R.

    Retorna [(x, y), ...] em mm absolutos. Cada ponto vira 2 nós no
    consumidor: (x, y, 0) = F.Cu e (x, y, 1) = B.Cu.
    """
    n = int(math.floor(GRID_R / step))
    r2 = GRID_R * GRID_R
    eps = 1e-9  # tolera pontos exatamente na borda (float)
    return [
        (CENTER_X + i * step, CENTER_Y + j * step)
        for i in range(-n, n + 1)
        for j in range(-n, n + 1)
        if (i * step) ** 2 + (j * step) ** 2 <= r2 + eps
    ]


_GRID_CACHE = None


def _grid_pts(step=0.5) -> list:
    """build_grid() com cache — usada pelos obstáculos (chamada milhares de
    vezes por roteamento)."""
    global _GRID_CACHE
    if _GRID_CACHE is None or _GRID_CACHE[1] != step:
        _GRID_CACHE = (build_grid(step), step)
    return _GRID_CACHE[0]


def in_keepout(p, net_name) -> bool:
    """True se p=(x,y) mm está dentro de KEEPOUT_ANT e a rede não é RF.

    p usa coordenadas absolutas (mesmo sistema da grade); KEEPOUT_ANT é
    relativo ao centro. Rede RF é isenta — o cobre da antena pode cruzar
    o retângulo.
    """
    x0, y0, x1, y1 = KEEPOUT_ANT
    rx, ry = p[0] - CENTER_X, p[1] - CENTER_Y
    inside = (x0 <= rx <= x1) and (y0 <= ry <= y1)
    return inside and net_name not in rf_nets()


# ---------------------------------------------------------------------------
# Obstáculos para roteamento (nós bloqueados na grade)
# ---------------------------------------------------------------------------
# Nós da grade: (x, y, 0) = F.Cu, (x, y, 1) = B.Cu (ver build_grid).
_PAD_LAYER_NODE = {pcbnew.F_Cu: 0, pcbnew.B_Cu: 1}

# Margem de segurança dos obstáculos (mm): cobre o "mergulho" máximo de um
# segmento de 0,5 mm entre dois nós livres (≈ (step/2)²/(2·raio) ≈ 0,078 mm
# para raio 0,4). 0,08 mantém livre o corredor de 1,0 mm entre trilhas
# paralelas em linhas vizinhas da grade (0,4+0,08 = 0,48 < 0,50).
_OBST_SAFETY_MM = 0.03

# Todas as vias criadas (sinais + GND): [(x, y, net), ...]. Usadas como
# obstáculo no roteamento (círculo raio 0,3 + clearance 0,2 = 0,5 mm) — mata
# clearance/hole_clearance trilha×via.
_ALL_VIAS = []


def pad_abs_pos(fp, pin) -> tuple:
    """Posição ABSOLUTA (mm, coords do board) do pad `pin` do footprint fp.

    Usa bb.pad_position_mm (centro absoluto do pad em mm).
    """
    return bb.pad_position_mm(fp, str(pin))


def _inflate_point(px, py, layer_node, inflate, step=0.5) -> set:
    """Nós da GRADE DE ROTEAMENTO a ≤ inflate de (px, py), na camada dada.

    BUG (auditoria §1.1/§4 punch 2): a versão anterior gerava candidatos na
    rede ancorada em (px, py) — que pode estar fora da grade (centro de pad,
    via de costura) — e esses nós nunca coincidiam com os nós da grade
    ancorada em (100,100) usados pelo A*. Resultado: obstáculos "fantasma"
    que não bloqueavam nada e curtos/clearance em massa. Agora: testa a
    distância EXATA de cada nó da grade de roteamento ao ponto.
    """
    out = set()
    r2 = inflate * inflate
    for (gx, gy) in _grid_pts(step):
        dx, dy = gx - px, gy - py
        if dx * dx + dy * dy <= r2 + 1e-9:
            out.add((gx, gy, layer_node))
    return out


def _inflate_segment(x1, y1, x2, y2, layer_node, inflate, step=0.5) -> set:
    """Nós da GRADE DE ROTEAMENTO a ≤ inflate de um segmento, na camada dada.

    Distância EXATA ponto-segmento para cada nó da grade dentro do bbox
    (mesma correção de _inflate_point — antes, a malha de amostragem ficava
    ancorada no segmento e não na grade).
    """
    out = set()
    lo_x, hi_x = min(x1, x2) - inflate - step, max(x1, x2) + inflate + step
    lo_y, hi_y = min(y1, y2) - inflate - step, max(y1, y2) + inflate + step
    for (gx, gy) in _grid_pts(step):
        if gx < lo_x or gx > hi_x or gy < lo_y or gy > hi_y:
            continue
        if _dist_point_seg(gx, gy, x1, y1, x2, y2) <= inflate + 1e-9:
            out.add((gx, gy, layer_node))
    return out


def build_obstacles(board, placed, net_name, routed_tracks,
                    own_width_mm=0.2, step=0.5,
                    safety_mm=_OBST_SAFETY_MM) -> tuple:
    """SETs de nós (x, y, camada) bloqueados para a net `net_name`.

    Retorna (obstacles, via_obstacles):
    - obstacles: nós bloqueados para TRILHA (clearance 0,2);
    - via_obstacles: nós (ponto (x,y), ambas as camadas) onde NÃO se pode
      trocar de camada — uma via (cobre Ø0,6, furo Ø0,3) precisa de mais
      folga que uma trilha 0,2: cobre 0,3 + clearance 0,2 + margem. Sem isto,
      vias colocadas em nós "livres para trilha" geravam clearance/
      hole_clearance (auditoria iteração 2: 6 hole_clearance).

    - pads de refs cujo pad tem net DIFERENTE de net_name (INCLUSIVE pads SEM
      rede — pinos NC: net vazia != net_name — bloqueiam para TODAS as nets):
      bloqueia nós a ≤ (clearance 0,2 + própria_largura/2) do RETÂNGULO do pad;
    - trilhas já roteadas de OUTRAS nets (routed_tracks = lista de segmentos
      (x1, y1, x2, y2, camada, net, largura_mm)): inflar largura/2 + 0,2 +
      própria_largura/2 (distância real de centro a centro);
    - vias de outras nets (_ALL_VIAS): círculo raio 0,3 (via Ø0,6) + 0,2 +
      própria_largura/2, nas DUAS camadas (via through);
    - pontos em in_keepout(p, net_name) (ambas as camadas);
    - NÃO bloqueia pads da própria net_name.
    """
    obstacles = set()
    via_obstacles = set()
    own_half = own_width_mm / 2.0

    # --- pads de outras nets (distância ao retângulo do pad) ----------------
    # CORREÇÃO (mesma raiz de _inflate_point): testa cada NÓ DA GRADE de
    # roteamento contra o retângulo do pad (distância exata). Antes, os
    # candidatos ficavam na rede ancorada no centro do pad e não bloqueavam
    # nenhum nó real do A* — origem dos 83+ curtos da auditoria.
    for ref, fp in placed.items():
        for pad in fp.Pads():  # KiCad 10: GetPads() exige aPadNumber; Pads() é a lista completa
            net = pad.GetNetname()
            # BUG FIX: era `if not net or ...` — pads SEM rede (NC) eram
            # ignorados e viravam curto; agora bloqueiam todas as nets.
            if net == net_name:
                continue
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            layer_node = _PAD_LAYER_NODE.get(pad.GetLayer(), 0)
            block = 0.2 + own_half + safety_mm
            rmax = math.hypot(w, h) / 2.0 + block + 0.5
            for (gx, gy) in _grid_pts():
                if abs(gx - cx) > rmax or abs(gy - cy) > rmax:
                    continue
                d = _dist_point_rect(gx, gy, cx, cy, w, h, ang)
                if d <= block:
                    obstacles.add((gx, gy, layer_node))
                # via: cobre 0,3 + clearance 0,2 + margem mínima
                if d <= 0.3 + 0.2 + safety_mm + 0.05:
                    via_obstacles.add((gx, gy))
                    via_obstacles.add((gx, gy, layer_node))

    # --- trilhas de outras nets (w/2 + 0,2 + própria_largura/2) -------------
    for x1, y1, x2, y2, layer_node, tnet, tw in routed_tracks:
        if tnet == net_name:
            continue
        obstacles |= _inflate_segment(x1, y1, x2, y2, layer_node,
                                      tw / 2.0 + 0.2 + own_half
                                      + safety_mm)
        vobs = _inflate_segment(x1, y1, x2, y2, layer_node,
                                0.3 + 0.2 + tw / 2.0 + safety_mm)
        via_obstacles |= {(a, b) for a, b, _l in vobs}

    # --- vias de outras nets (raio 0,3 + 0,2 + própria/2, duas camadas) ------
    for vx, vy, vnet in _ALL_VIAS:
        if vnet == net_name:
            continue
        obstacles |= _inflate_point(vx, vy, 0, 0.5 + own_half + safety_mm)
        obstacles |= _inflate_point(vx, vy, 1, 0.5 + own_half + safety_mm)
        via_obstacles |= {(a, b) for a, b, _l in
                          _inflate_point(vx, vy, 0, 0.85)}

    # --- keepout da antena (ambas as camadas) --------------------------------
    for (gx, gy) in build_grid():
        if in_keepout((gx, gy), net_name):
            obstacles.add((gx, gy, 0))
            obstacles.add((gx, gy, 1))
            via_obstacles.add((gx, gy))

    return obstacles, via_obstacles


# ---------------------------------------------------------------------------
# Roteamento A* sobre a grade
# ---------------------------------------------------------------------------
def astar_route(grid, obstacles, start, goal, step=0.5, via_obstacles=None,
                via_cost=200):
    """A* sobre nós (x, y, camada) da grade de costura.

    grid: [(x, y), ...] de build_grid() (mm absolutos); cada ponto vira 2 nós
    no grafo: (x, y, 0) = F.Cu e (x, y, 1) = B.Cu.
    obstacles: set de nós (x, y, camada) bloqueados (build_obstacles).
    via_obstacles: set de pontos (x, y) onde trocar de camada é proibido —
    uma via precisa de mais folga que uma trilha (ver build_obstacles).
    start/goal: (x, y, camada) em posições absolutas — arredondados para o
    ponto da grade mais próximo. Se o nó mais próximo estiver em obstacles,
    é forçado livre (pad da própria net).
    Vizinhos: 4 direções na MESMA camada (custo 1 por passo de 0,5 mm) +
    troca de camada no MESMO ponto (custo 200 = via cara; minimiza B.Cu e
    mantém a zona GND em B.Cu contígua) — só em ponto via-seguro.
    Heurística: distância Manhattan 2D em passos de grade (ignora camada).
    Retorna [(x, y, camada), ...] do caminho (start→goal) ou None.
    """
    if via_obstacles is None:
        via_obstacles = set()
    pts = {(round(x, 6), round(y, 6)) for (x, y) in grid}

    def snap(node):
        gx = round((node[0] - CENTER_X) / step) * step + CENTER_X
        gy = round((node[1] - CENTER_Y) / step) * step + CENTER_Y
        sn = (round(gx, 6), round(gy, 6), node[2])
        if (sn[0], sn[1]) not in pts:
            # pad fora do raio da grade (ex.: C4/C9 a r>15 mm): usa o nó da
            # grade mais próximo, mesma camada; a extensão ao pad em
            # _path_to_tracks faz a ponte até o centro exato do pad.
            best = min(pts, key=lambda p: (p[0] - sn[0]) ** 2 + (p[1] - sn[1]) ** 2)
            sn = (best[0], best[1], sn[2])
        return sn

    start, goal = snap(start), snap(goal)

    # pads da própria net: força start/goal livres
    obstacles = set(obstacles) - {start, goal}

    def h(node):
        return (abs(node[0] - goal[0]) + abs(node[1] - goal[1])) / step

    open_heap = [(h(start), 0, start)]
    came_from = {}
    g_score = {start: 0}
    closed = set()

    while open_heap:
        _f, g, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        closed.add(current)
        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        x, y, layer = current
        neighbors = []
        for dx, dy in ((step, 0), (-step, 0), (0, step), (0, -step)):
            npt = (round(x + dx, 6), round(y + dy, 6))
            if npt in pts:
                neighbors.append((npt[0], npt[1], layer))
        if (x, y) in pts and (x, y) not in via_obstacles:
            neighbors.append((x, y, 1 - layer))
        for nb in neighbors:
            if nb in obstacles or nb in closed:
                continue
            step_cost = via_cost if nb[2] != layer else 1
            # meia-faixa (coord não inteira em mm): penalidade mínima —
            # rotas longas desviam para faixas inteiras, preservando as
            # meias-faixas para trilhas paralelas de outras redes.
            if ((nb[0] - CENTER_X) % 1.0) or ((nb[1] - CENTER_Y) % 1.0):
                step_cost += 0.15
            ng = g + step_cost
            if ng < g_score.get(nb, float("inf")):
                g_score[nb] = ng
                came_from[nb] = current
                heapq.heappush(open_heap, (ng + h(nb), ng, nb))
    return None


# ---------------------------------------------------------------------------
# Roteamento de todas as nets (ordem de prioridade)
# ---------------------------------------------------------------------------
# Grupos de roteamento em ordem de prioridade. Cada grupo é (pins, refs,
# nome): a net entra se tocar algum pin exato (ref, pin), qualquer pino de
# algum ref em refs, ou ter o nome exato. Os NOMES reais vêm da netlist
# parseada (nada hardcoded por nome, exceto VDD_BAT, grupo por nome).
# GND NÃO entra: fica para a zona de cobre, não para trilha.
_ROUTE_GROUPS = [
    # Bateria: por nome (trilha mais larga, 0,5 mm) — PRIMEIRA na ordem: é a
    # rede de maior extensão (BT1→C4→C8→TP1→R1→U1) e, se roteada tarde,
    # monopoliza os corredores norte/sul e starving todas as demais.
    ((), frozenset(), "VDD_BAT"),
    # RF: U1.19 / C3 / L1 / ANT1  (NET_ANT, NET_RF)
    ((("U1", "19"),), frozenset({"C3", "L1", "ANT1"}), None),
    # Cristal: U1.23 / U1.24 / X1 / C1 / C2  (NET_XC1, NET_XC2)
    ((("U1", "23"), ("U1", "24")), frozenset({"X1", "C1", "C2"}), None),
    # DC/DC: U1.31 / L2 / L3 / U1.30 / C10  (NET_DCC, NET_DEC4, NET_L2_L3)
    ((("U1", "31"), ("U1", "30")), frozenset({"L2", "L3", "C10"}), None),
    # DEC: U1.1/C5, U1.21/C7, U1.22/C6  (NET_DEC1, NET_DEC2, NET_DEC3)
    ((("U1", "1"), ("U1", "21"), ("U1", "22")),
     frozenset({"C5", "C7", "C6"}), None),
    # SWD: TP2/U1.18, TP3/U1.17  (NET_SWDIO, NET_SWDCLK)
    ((("U1", "18"), ("U1", "17")), frozenset({"TP2", "TP3"}), None),
    # RESET: R1/U1.16  (NET_RESET)
    ((("U1", "16"),), frozenset({"R1"}), None),
]


def _nets_touching(nets, pins, refs, name=None) -> list:
    """Nomes (na ordem da netlist) das nets que tocam as âncoras do grupo.

    pins: {(ref, pin), ...} exatos; refs: {ref, ...} (qualquer pino);
    name: nome exato da net (grupo por nome, com pins/refs vazios).
    GND é sempre excluído — senão seria pego pelos refs de RF/cristal/
    DC/DC/DEC (C3.2, C1.2, L2, C10, C5... são todos GND).
    """
    out = []
    for net_name, nodes in nets.items():
        if net_name == "GND":
            continue
        if name is not None:
            if net_name == name:
                out.append(net_name)
            continue
        if any((ref, pin) in pins or ref in refs for ref, pin in nodes):
            out.append(net_name)
    return out


def _pad_node(fp, pin) -> tuple:
    """Nó inicial/final do pad: (x, y, camada) — camada 0=F.Cu, 1=B.Cu."""
    pad = fp.FindPadByNumber(str(pin))
    layer_node = _PAD_LAYER_NODE.get(pad.GetLayer(), 0)
    x, y = bb.pad_position_mm(fp, pin)
    return (x, y, layer_node)


_PLACED_CACHE = {}


def _path_to_tracks(board, net_name, path, width_mm, routed_tracks,
                    start_pad=None, goal_pad=None, stub_start=None,
                    stub_goal=None) -> None:
    """Converte caminho A* [(x, y, camada), ...] em trilhas/vias no board.

    Pontos consecutivos na MESMA camada viram bb.add_track (largura
    width_mm); mudança de camada vira bb.add_via no ponto compartilhado.
    EXTENSÃO AO PAD: antes do primeiro nó e depois do último nó do caminho,
    um segmento reto liga o CENTRO EXATO do pad (start_pad/goal_pad,
    (x, y, camada)) ao primeiro/último ponto do caminho, na MESMA camada do
    nó — elimina o stub de até 0,5 mm que deixava o pad desconectado.
    Cada segmento criado é acrescentado a routed_tracks como
    (x1, y1, x2, y2, camada_nó, net, largura_mm); cada via criada entra em
    _ALL_VIAS como (x, y, net).
    """
    layer_name = {0: "F.Cu", 1: "B.Cu"}
    w_s = stub_start if stub_start is not None else width_mm
    w_g = stub_goal if stub_goal is not None else width_mm
    if path:
        # extensão: centro exato do pad inicial -> primeiro nó do caminho
        if start_pad is not None:
            sx, sy, _sl = start_pad
            px, py, pl = path[0]
            if math.hypot(px - sx, py - sy) > 1e-6:
                bb.add_track(board, net_name, sx, sy, px, py,
                             layer=layer_name[pl], width_mm=w_s)
                routed_tracks.append((sx, sy, px, py, pl, net_name, w_s))
        # extensão: último nó do caminho -> centro exato do pad final
        if goal_pad is not None:
            gx, gy, _gl = goal_pad
            px, py, pl = path[-1]
            if math.hypot(gx - px, gy - py) > 1e-6:
                bb.add_track(board, net_name, px, py, gx, gy,
                             layer=layer_name[pl], width_mm=w_g)
                routed_tracks.append((px, py, gx, gy, pl, net_name, w_g))
    for (x1, y1, l1), (x2, y2, l2) in zip(path, path[1:]):
        if l1 != l2:
            if not any(vx == x1 and vy == y1 for vx, vy, _vn in _ALL_VIAS):
                bb.add_via(board, net_name, x1, y1)
                _ALL_VIAS.append((x1, y1, net_name))
            continue
        w = width_mm
        if _seg_clear_of_other_nets(_PLACED_CACHE, x1, y1, x2, y2, net_name,
                                    routed_tracks, item_half=w / 2.0) is False:
            for w_alt in (0.2,):
                if w_alt >= w:
                    continue
                if _seg_clear_of_other_nets(_PLACED_CACHE, x1, y1, x2, y2,
                                            net_name, routed_tracks,
                                            item_half=w_alt / 2.0):
                    w = w_alt
                    break
        bb.add_track(board, net_name, x1, y1, x2, y2,
                     layer=layer_name[l1], width_mm=w)
        routed_tracks.append((x1, y1, x2, y2, l1, net_name, w))


def _ext_collides(placed, net_name, routed_tracks, sx, sy, node, width_mm,
                  step=0.5) -> bool:
    """True se o segmento reto pad(sx,sy)→nó fere clearance real.

    Checagem geométrica (sem dupla contagem de clearance): trilhas de outras
    nets (largura/2 por trilha), pads de outras nets (meia-maior-dimensão) e
    vias de outras nets (raio 0,3). Segmento de comprimento ~0 -> sem colisão.
    """
    nx, ny, _nl = node
    if math.hypot(nx - sx, ny - sy) <= 1e-6:
        return False
    if not _seg_clear_of_other_nets(placed, sx, sy, nx, ny, net_name,
                                    routed_tracks, item_half=width_mm / 2.0):
        return True
    for vx, vy, vnet in _ALL_VIAS:
        if vnet == net_name:
            continue
        if _dist_point_seg(vx, vy, sx, sy, nx, ny) < 0.3 + width_mm / 2.0 + 0.2:
            return True
    return False


def _free_anchor(grid, placed, net_name, routed_tracks, obstacles, pad_node,
                 width_mm, step=0.5):
    """Nó de grade livre mais próximo do pad (testa nó snapped + 8 vizinhos).

    Retorna (x, y, camada) ou None se nenhum candidato for livre com extensão
    sem colisão.
    """
    pts = {(round(x, 6), round(y, 6)) for (x, y) in grid}
    sx, sy, sl = pad_node
    gx = round((sx - CENTER_X) / step) * step + CENTER_X
    gy = round((sy - CENTER_Y) / step) * step + CENTER_Y
    base = (round(gx, 6), round(gy, 6), sl)
    # 2 anéis de candidatos: ±1 passo (9) e ±2 passos em cruz/diagonal —
    # pads de QFN (0,8 mm de largura) "boxam" o nó snapped e o anel 1 fica
    # todo bloqueado; o anel 2 alcança o corredor real (p.ex. x=103,5/104
    # para a coluna direita do U1).
    cands = [base]
    for r in (1, 2, 3):
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                if dx == 0 and dy == 0:
                    continue
                if max(abs(dx), abs(dy)) != r:
                    continue
                cands.append((round(base[0] + dx * step, 6),
                              round(base[1] + dy * step, 6), sl))
    livres = []
    for c in cands:
        if (c[0], c[1]) not in pts or c in obstacles:
            continue
        if _ext_collides(placed, net_name, routed_tracks, sx, sy, c, width_mm, step):
            continue
        livres.append(c)
    if not livres:
        return None
    return min(livres, key=lambda c: (c[0] - sx) ** 2 + (c[1] - sy) ** 2)


def _stub_width(placed, net_name, routed_tracks, sx, sy, node, width_mm) -> float:
    """Largura da extensão reta pad→nó: width_mm; ou neck-down 0,2 mm; ou
    0,15 mm (último recurso — stubs diagonais curtos entre pads de QFN pitch
    0,5 com pads de 0,8 mm de largura, p.ex. coluna direita do U1); ou None."""
    if not _ext_collides(placed, net_name, routed_tracks, sx, sy, node,
                         width_mm):
        return width_mm
    if width_mm > 0.2 and not _ext_collides(placed, net_name, routed_tracks,
                                            sx, sy, node, 0.2):
        return 0.2
    return None


def _route_pair(board, placed, grid, net_name, width_mm, routed_tracks,
                start, goal):
    """Roteia um par de pads com checagem de colisão da extensão ao pad.

    1. A* pad→pad; sem caminho -> None.
    2. Extensão reta pad→path[0]: largura width_mm; se colidir, tenta
       neck-down 0,2 mm; se nem 0,2 passar, ancora o caminho no nó de grade
       livre mais próximo do pad (8 vizinhos) e re-A* desse nó.
    3. Mesmo cheque para a extensão path[-1]→pad final.
    Retorna (path, largura_stub_start, largura_stub_goal) ou None (pendência).
    """
    obstacles, via_obstacles = build_obstacles(board, placed, net_name,
                                               routed_tracks,
                                               own_width_mm=width_mm)
    start_eff = start
    goal_eff = goal
    path = astar_route(grid, obstacles, start_eff, goal_eff,
                       via_obstacles=via_obstacles)
    if path is None:
        # pad inicial "boxado" (nó snapped cercado por pads vizinhos):
        # ancora o início no nó de grade livre mais próximo e re-A*.
        anchor = _free_anchor(grid, placed, net_name, routed_tracks,
                              obstacles, start, width_mm)
        if anchor is not None:
            start_eff = anchor
            path = astar_route(grid, obstacles, start_eff, goal_eff,
                               via_obstacles=via_obstacles)
    if path is None:
        # pad final boxado: ancora o fim e re-A* (start_eff→anchor).
        anchor = _free_anchor(grid, placed, net_name, routed_tracks,
                              obstacles, goal, width_mm)
        if anchor is not None:
            goal_eff = anchor
            path = astar_route(grid, obstacles, start_eff, goal_eff,
                               via_obstacles=via_obstacles)
    if path is None:
        return None
    sx, sy, _sl = start
    w_s = _stub_width(placed, net_name, routed_tracks, sx, sy, path[0], width_mm)
    if w_s is None:
        anchor = _free_anchor(grid, placed, net_name, routed_tracks,
                              obstacles, start, width_mm)
        if anchor is not None:
            path2 = astar_route(grid, obstacles, anchor, goal,
                                via_obstacles=via_obstacles)
            if path2 is not None:
                w2 = _stub_width(placed, net_name, routed_tracks, sx, sy,
                                 path2[0], width_mm)
                if w2 is not None:
                    path, w_s = path2, w2
        if w_s is None:
            return None
    gx, gy, _gl = goal
    w_g = _stub_width(placed, net_name, routed_tracks, gx, gy, path[-1], width_mm)
    if w_g is None:
        anchor = _free_anchor(grid, placed, net_name, routed_tracks,
                              obstacles, goal, width_mm)
        if anchor is not None:
            path2 = astar_route(grid, obstacles, start_eff, anchor,
                                via_obstacles=via_obstacles)
            if path2 is not None:
                w2 = _stub_width(placed, net_name, routed_tracks, gx, gy,
                                 path2[-1], width_mm)
                if w2 is not None:
                    path, w_g = path2, w2
        if w_g is None:
            return None
    return path, w_s, w_g


def route_all(board, placed, nets, grid, routed_tracks=None) -> tuple:
    """Roteia todas as nets (exceto GND) na ordem de _ROUTE_GROUPS.

    Para cada net, os pares terminais seguem a sequência dos pads na net
    (pad0→pad1, pad1→pad2, ...). Cada par é roteado com A* sobre a grade,
    com obstáculos recalculados (build_obstacles) contra as trilhas já
    roteadas. Sem caminho → par entra em pendências; com caminho → vira
    trilhas (0,2 mm; 0,5 mm para VDD_BAT) e vias nas trocas de camada.

    Retorna (routed_tracks, pendencias):
    - routed_tracks: [(x1, y1, x2, y2, camada_nó, net), ...];
    - pendencias: [(net, "REF.pin", "REF.pin"), ...] pares sem caminho.
    """
    routed_tracks = [] if routed_tracks is None else list(routed_tracks)
    pendencias = []
    selected = set()

    for pins, refs, name in _ROUTE_GROUPS:
        group_nets = _nets_touching(nets, pins, refs, name)
        # Redes que tocam os pinos da face SUL do U1 (linha inferior, y <
        # centro) por último no grupo: elas dependem do corredor y≈107 e
        # monopolizá-lo cedo starving as redes locais (L2_L3 etc.).
        def _south_key(net_name):
            u1y = bb.pad_position_mm(placed['U1'], '33')[1] if 'U1' in placed else 0.0
            for ref, pin in nets.get(net_name, []):
                if ref == 'U1':
                    try:
                        if bb.pad_position_mm(placed['U1'], pin)[1] < u1y:
                            return 1
                    except Exception:
                        pass
            return 0
        group_nets.sort(key=_south_key)
        for net_name in group_nets:
            if net_name in selected:
                continue
            selected.add(net_name)
            width = 0.5 if net_name == "VDD_BAT" else 0.2
            nodes = nets[net_name]
            for (r0, p0), (r1, p1) in zip(nodes, nodes[1:]):
                if r0 not in placed or r1 not in placed:
                    continue  # ref fora do board (não deve ocorrer aqui)
                start = _pad_node(placed[r0], p0)
                goal = _pad_node(placed[r1], p1)
                res = _route_pair(board, placed, grid, net_name, width,
                                  routed_tracks, start, goal)
                if res is None:
                    pendencias.append((net_name, f"{r0}.{p0}", f"{r1}.{p1}"))
                    continue
                path, w_s, w_g = res
                _path_to_tracks(board, net_name, path, width, routed_tracks,
                                start_pad=start, goal_pad=goal,
                                stub_start=w_s, stub_goal=w_g)
    return routed_tracks, pendencias


# ---------------------------------------------------------------------------
# SEGUNDA PASSADA: pares pendentes com via barata + corredores apertados
# ---------------------------------------------------------------------------
# Via custo 100 (em vez de 200) e obstáculos de trilha inflados com margem
# 0,05 (total trilha×trilha 0,2 mm: 0,1+0,2+0,1+0,05 = 0,45 em vez de 0,48 —
# corredores apertados). Via-obstáculos (0,88 / raio 0,5) NÃO afrouxam:
# hole_clearance/clearance trilha×via são violações reais de DRC.
_SECOND_PASS_VIA_COST = 100
_SECOND_PASS_SAFETY_MM = 0.02


def _try_route(board, placed, grid, net_name, width_mm, routed_tracks,
               start, goal, via_cost, safety_mm,
               force_start_layer=None) -> bool:
    """Uma tentativa de rotear start→goal; True se trilhas/vias foram ADICIONADAS.

    force_start_layer: se 1, o A* começa no nó B.Cu do ponto do pad inicial;
    o nó real do pad (camada nativa) é PREFIXADO ao caminho — o zip em
    _path_to_tracks vê a troca de camada no mesmo ponto e cria a via NO PAD
    (mesma net). A via no pad só é permitida se respeitar clearance contra
    cobre de outras nets (_clear_of_other_nets) — senão a tentativa falha.
    Não desfaz rotas existentes: só acrescenta.
    """
    if force_start_layer is not None:
        fx, fy = start[0], start[1]
        if not _clear_of_other_nets(placed, fx, fy, net_name, routed_tracks,
                                    item_radius=0.3, check_pads=True):
            return False  # via no pad feriria clearance de outra net
    obstacles, via_obstacles = build_obstacles(board, placed, net_name,
                                               routed_tracks,
                                               own_width_mm=width_mm,
                                               safety_mm=safety_mm)
    # Via nova precisa de hole-to-hole ≥ 0,25 mm de borda (furo Ø0,3 →
    # centros ≥ 0,55) de TODA via existente, INCLUSIVE da mesma net —
    # senão: hole_to_hole (0,5 mm entre centros) e holes_co_located (via
    # duplicada no mesmo ponto, p.ex. (103,108.5) na 2ª passada).
    for vx, vy, _vnet in _ALL_VIAS:
        via_obstacles |= {(gx, gy) for (gx, gy) in _grid_pts()
                          if math.hypot(gx - vx, gy - vy) <= 0.55 + 1e-9}
    # NORMALIZAÇÃO (bug pré-existente): build_obstacles mistura 3-tuplas
    # (gx, gy, camada) — de _inflate_segment/_inflate_point — com 2-tuplas
    # (gx, gy) em via_obstacles; o A* compara só 2-tuplas, então os
    # via-obstáculos de TRILHAS nunca bloqueavam (via a 0,5 mm de trilha
    # NET_RESET em B.Cu -> clearance 0,1). Achata para 2-tuplas. Aplicado
    # SÓ na 2ª passada para não alterar as rotas da 1ª.
    via_obstacles = {(p[0], p[1]) for p in via_obstacles}
    s = start if force_start_layer is None else (start[0], start[1],
                                                 force_start_layer)
    path = astar_route(grid, obstacles, s, goal,
                       via_obstacles=via_obstacles, via_cost=via_cost)
    if path is None:
        return False
    if force_start_layer is not None and path[0][2] != start[2]:
        path = [start] + path  # via no próprio pad (mesma net)
    sx, sy, _sl = start
    w_s = _stub_width(placed, net_name, routed_tracks, sx, sy, path[0], width_mm)
    gx, gy, _gl = goal
    w_g = _stub_width(placed, net_name, routed_tracks, gx, gy, path[-1], width_mm)
    if w_s is None or w_g is None:
        return False
    _path_to_tracks(board, net_name, path, width_mm, routed_tracks,
                    start_pad=start, goal_pad=goal,
                    stub_start=w_s, stub_goal=w_g)
    return True


def _bcu_via_anchor(placed, net_name, routed_tracks, obstacles, pad_node,
                    width_mm, grid, step=0.5, max_r=2.5) -> tuple:
    """Nó (x, y) para uma VIA de acesso em B.Cu ao pad (F.Cu) `pad_node`.

    Procura (anéis 0,5..2,5 mm) um nó da grade onde:
    - a via (cobre Ø0,6) respeita clearance F.Cu contra pads/trilhas/vias de
      outras nets (_clear_of_other_nets, item_radius 0,3);
    - o nó B.Cu (x, y, 1) está livre nos obstáculos;
    - o stub reto pad→via (largura width_mm) não fere clearance
      (_ext_collides).
    Retorna (x, y) ou None.
    """
    sx, sy, _sl = pad_node
    pts = {(round(x, 6), round(y, 6)) for (x, y) in grid}
    # ancora a busca no NÓ DA GRADE mais próximo do pad (o pad em si pode
    # estar fora da grade — ex.: pads de U1 em x=…,25/…,75)
    bx = round((sx - CENTER_X) / step) * step + CENTER_X
    by = round((sy - CENTER_Y) / step) * step + CENTER_Y
    best = None
    n = int(math.ceil(max_r / step))
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            gx = round(bx + i * step, 6)
            gy = round(by + j * step, 6)
            if (gx, gy) not in pts:
                continue
            if (gx, gy, 1) in obstacles:
                continue
            if not _clear_of_other_nets(placed, gx, gy, net_name,
                                        routed_tracks, item_radius=0.3):
                continue
            if _ext_collides(placed, net_name, routed_tracks, sx, sy,
                             (gx, gy, 0), width_mm, step):
                continue
            d = math.hypot(gx - sx, gy - sy)
            if best is None or d < best[0]:
                best = (d, gx, gy)
    return None if best is None else (best[1], best[2])


def _try_route_bcu(board, placed, grid, net_name, width_mm, routed_tracks,
                   start, goal) -> bool:
    """Terceira estratégia: via de acesso em B.Cu junto a cada pad + trecho
    em B.Cu (o F.Cu sob o U1 está saturado por VDD_BAT 0,5 mm + malha GND
    do die pad). True se trilhas/vias foram adicionadas."""
    obstacles, via_obstacles = build_obstacles(board, placed, net_name,
                                               routed_tracks,
                                               own_width_mm=width_mm,
                                               safety_mm=_SECOND_PASS_SAFETY_MM)
    for vx, vy, _vnet in _ALL_VIAS:
        via_obstacles |= {(gx, gy) for (gx, gy) in _grid_pts()
                          if math.hypot(gx - vx, gy - vy) <= 0.55 + 1e-9}
    via_obstacles = {(p[0], p[1]) for p in via_obstacles}
    a = _bcu_via_anchor(placed, net_name, routed_tracks, obstacles,
                        start, width_mm, grid)
    b = _bcu_via_anchor(placed, net_name, routed_tracks, obstacles,
                        goal, width_mm, grid)
    if a is None or b is None:
        return False
    path = astar_route(grid, obstacles, (a[0], a[1], 1), (b[0], b[1], 1),
                       via_obstacles=via_obstacles,
                       via_cost=_SECOND_PASS_VIA_COST)
    if path is None:
        return False
    sx, sy, _sl = start
    w_a = width_mm
    if (_ext_collides(placed, net_name, routed_tracks, sx, sy,
                      (a[0], a[1], 0), width_mm) and width_mm > 0.2
            and not _ext_collides(placed, net_name, routed_tracks, sx, sy,
                                  (a[0], a[1], 0), 0.2)):
        w_a = 0.2
    bb.add_track(board, net_name, sx, sy, a[0], a[1], layer="F.Cu",
                 width_mm=w_a)
    routed_tracks.append((sx, sy, a[0], a[1], 0, net_name, w_a))
    bb.add_via(board, net_name, a[0], a[1])
    _ALL_VIAS.append((a[0], a[1], net_name))
    gx, gy, _gl = goal
    w_b = width_mm
    if (_ext_collides(placed, net_name, routed_tracks, gx, gy,
                      (b[0], b[1], 0), width_mm) and width_mm > 0.2
            and not _ext_collides(placed, net_name, routed_tracks, gx, gy,
                                  (b[0], b[1], 0), 0.2)):
        w_b = 0.2
    bb.add_track(board, net_name, b[0], b[1], gx, gy, layer="F.Cu",
                 width_mm=w_b)
    routed_tracks.append((b[0], b[1], gx, gy, 0, net_name, w_b))
    bb.add_via(board, net_name, b[0], b[1])
    _ALL_VIAS.append((b[0], b[1], net_name))
    _path_to_tracks(board, net_name, path, width_mm, routed_tracks)
    return True


def route_pending_second_pass(board, placed, grid, routed_tracks,
                              pendencias) -> tuple:
    """SEGUNDA PASSADA de roteamento sobre os pares pendentes da 1ª passada.

    Para cada par (net, a, b):
    1. re-tenta a→b com via custo 100 e obstáculos de trilha inflados 0,05
       (corredores apertados);
    2. se ainda falhar, tenta o par INVERTIDO (b→a) por B.Cu primeiro
       (início forçado na camada 1 — via no pad de b, se o clearance permitir).

    NÃO desfaz rotas existentes — só adiciona trilhas/vias.
    Retorna (pendencias_restantes, n_rotadas).
    """
    remaining = []
    n_ok = 0
    for net_name, a, b in pendencias:
        r0, p0 = a.split(".", 1)
        r1, p1 = b.split(".", 1)
        if r0 not in placed or r1 not in placed:
            remaining.append((net_name, a, b))
            continue
        width = 0.5 if net_name == "VDD_BAT" else 0.2
        start = _pad_node(placed[r0], p0)
        goal = _pad_node(placed[r1], p1)
        ok = _try_route(board, placed, grid, net_name, width, routed_tracks,
                        start, goal, _SECOND_PASS_VIA_COST,
                        _SECOND_PASS_SAFETY_MM)
        if not ok:
            ok = _try_route(board, placed, grid, net_name, width,
                            routed_tracks, goal, start,
                            _SECOND_PASS_VIA_COST, _SECOND_PASS_SAFETY_MM,
                            force_start_layer=1)
        if not ok:
            ok = _try_route_bcu(board, placed, grid, net_name, width,
                                routed_tracks, start, goal)
        if ok:
            n_ok += 1
        else:
            remaining.append((net_name, a, b))
    return remaining, n_ok


# ---------------------------------------------------------------------------
# TERCEIRA PASSADA (manual, determinística): Dijkstra em treliça 0,25 mm
# ---------------------------------------------------------------------------
# DESVIO DOCUMENTADO da estratégia "L de 2 segmentos": L puro (HV e VH) em
# F.Cu falha em 9/9 pares (verificado por _seg_clear_of_other_nets — os pads
# da coluna leste do U1 têm gap de 0,25 mm entre si e qualquer saída
# horizontal/vertical cruza pads vizinhos ou trilhas VDD_BAT), e L em B.Cu
# falha em 8/9. Em vez disso: Dijkstra determinístico (heap + contador de
# desempate, vizinhança em ordem fixa, sets ordenados) sobre treliça de
# 0,25 mm ancorada no centro, com checagem geométrica EXATA por segmento
# (trilhas da mesma camada, vias through, retângulo exato dos pads,
# keepout da antena, borda r≤15,2). Pontos de cobre da própria net
# (terminais de trilhas + vias existentes) entram como nós neutros — o
# caminho pode partir de um stub parcial da 2ª passada. Largura 0,2 mm;
# via custo 8 (desestimula, permite o desvio por B.Cu via→trecho→via).
# Só desenha após validar vias novas (hole-to-hole ≥0,55 entre si e contra
# _ALL_VIAS); sem caminho válido -> par continua pendente (não inventa cobre).
_MAN_STEP_MM = 0.25
_MAN_W_MM = 0.2
_MAN_CLR_MM = 0.2
_MAN_R_EDGE_MM = 15.2
_MAN_VIA_COST = 8.0

# Ordem da tarefa (9 pares pendentes, sequência do enunciado). Nota empírica:
# com XC1 primeiro fecham XC1+DEC1 (a rota longa do XC1 ~28 mm sela o
# corredor oeste que o XC2 precisaria); com locais primeiro (DEC1, XC2, XC1)
# fecham 3 sinais mas a rota do XC2 esteriliza os stitches GND do oeste
# (C1.2/C2.2) e gerava clearance via×via — ver correções _man_via_ok (0,8).
# Mantida a ordem do enunciado: o saldo DRC/unconnected decide a MELHOR.
_MAN_PAIRS = [
    ("NET_XC1", "C1", "1", "U1", "23"),
    ("NET_XC2", "U1", "24", "X1", "2"),
    ("NET_DCC", "L2", "2", "U1", "31"),
    ("NET_DEC4", "L3", "2", "U1", "30"),
    ("NET_DEC1", "C5", "1", "U1", "1"),
    ("NET_DEC3", "C6", "1", "U1", "22"),
    ("NET_SWDCLK", "TP3", "1", "U1", "17"),
    ("NET_SWDIO", "TP2", "1", "U1", "18"),
    ("NET_RESET", "R1", "1", "U1", "16"),
]


def _man_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang) -> float:
    """Distância EXATA (mm) segmento↔retângulo (quadro local + 4 arestas)."""
    c, s = math.cos(ang), math.sin(ang)
    la = ((x1 - cx) * c + (y1 - cy) * s, -(x1 - cx) * s + (y1 - cy) * c)
    lb = ((x2 - cx) * c + (y2 - cy) * s, -(x2 - cx) * s + (y2 - cy) * c)
    hw, hh = w / 2.0, h / 2.0
    if abs(la[0]) <= hw and abs(la[1]) <= hh:
        return 0.0
    if abs(lb[0]) <= hw and abs(lb[1]) <= hh:
        return 0.0
    if abs((la[0] + lb[0]) / 2) <= hw and abs((la[1] + lb[1]) / 2) <= hh:
        for ex1, ey1, ex2, ey2 in ((-hw, -hh, hw, -hh), (hw, -hh, hw, hh),
                                   (hw, hh, -hw, hh), (-hw, hh, -hw, -hh)):
            if _segs_intersect(la[0], la[1], lb[0], lb[1], ex1, ey1, ex2, ey2):
                return 0.0
    best = float("inf")
    for ex1, ey1, ex2, ey2 in ((-hw, -hh, hw, -hh), (hw, -hh, hw, hh),
                               (hw, hh, -hw, hh), (-hw, hh, -hw, -hh)):
        best = min(best, _dist_seg_seg(la[0], la[1], lb[0], lb[1],
                                       ex1, ey1, ex2, ey2))
    return best


def _man_caches(placed):
    """Pads por camada: {0: [...], 1: [...]} de (cx,cy,w,h,ang,net)."""
    padr = {0: [], 1: []}
    for _ref, fp in placed.items():
        for pad in fp.Pads():
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            ln = _PAD_LAYER_NODE.get(pad.GetLayer(), 0)
            padr[ln].append((cx, cy, w, h, ang, pad.GetNetname()))
    return padr


def _man_edge_ok(padr, trk, vias, x1, y1, x2, y2, net, layer,
                 half=_MAN_W_MM / 2.0) -> bool:
    """Segmento de trilha 0,2 respeita clearance 0,2 (mesma camada p/ trilhas
    e pads; vias through sempre; keepout p/ não-RF)."""
    if in_keepout((x1, y1), net) or in_keepout((x2, y2), net):
        return False
    for tx1, ty1, tx2, ty2, _l, tnet, tw in trk[layer]:
        if tnet == net:
            continue
        if _dist_seg_seg(x1, y1, x2, y2, tx1, ty1, tx2, ty2) < half + _MAN_CLR_MM + tw / 2.0:
            return False
    for vx, vy, vnet in vias:
        if vnet == net:
            continue
        if _dist_point_seg(vx, vy, x1, y1, x2, y2) < half + _MAN_CLR_MM + 0.3:
            return False
    for cx, cy, w, h, ang, pnet in padr[layer]:
        if pnet == net:
            continue
        if _man_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang) < half + _MAN_CLR_MM:
            return False
    return True


def _man_via_ok(padr, trk, vias, vx, vy, net) -> bool:
    """Via through Ø0,6/furo Ø0,3 respeita clearance + hole-to-hole 0,55."""
    if in_keepout((vx, vy), net):
        return False
    for tx1, ty1, tx2, ty2, _l, tnet, tw in trk[0] + trk[1]:
        if tnet == net:
            continue
        if _dist_point_seg(vx, vy, tx1, ty1, tx2, ty2) < 0.3 + _MAN_CLR_MM + tw / 2.0:
            return False
    for ex, ey, evnet in vias:
        need = 0.55 if evnet == net else 0.8
        if math.hypot(vx - ex, vy - ey) <= need + 1e-9:
            return False
    for cx, cy, w, h, ang, pnet in padr[0] + padr[1]:
        if pnet == net:
            continue
        if _dist_point_rect(vx, vy, cx, cy, w, h, ang) < 0.3 + _MAN_CLR_MM:
            return False
    return True


def _man_neutral(net, routed_tracks, vias) -> list:
    """Âncoras de cobre da própria net: [(x, y, camada)] (via -> 2 camadas)."""
    out, seen = [], set()
    for x1, y1, x2, y2, layer, tnet, _tw in routed_tracks:
        if tnet != net:
            continue
        out.extend([(x1, y1, layer), (x2, y2, layer)])
    for vx, vy, vnet in vias:
        if vnet != net:
            continue
        out.extend([(vx, vy, 0), (vx, vy, 1)])
    res = []
    for x, y, layer in out:
        k = (round(x, 4), round(y, 4), layer)
        if k not in seen:
            seen.add(k)
            res.append((x, y, layer))
    return res


def _man_find(placed, padr, trk, vias, net, A, B, margin=3.0):
    """Dijkstra semeado lado-A -> lado-B. Retorna [(x,y,camada)] ou None."""
    st = _MAN_STEP_MM
    neut = _man_neutral(net, trk[0] + trk[1], vias)
    x0, y0 = min(A[0], B[0]) - margin, min(A[1], B[1]) - margin
    x1, y1 = max(A[0], B[0]) + margin, max(A[1], B[1]) + margin
    pts = []
    i0, i1 = math.ceil((x0 - CENTER_X) / st), math.floor((x1 - CENTER_X) / st)
    j0, j1 = math.ceil((y0 - CENTER_Y) / st), math.floor((y1 - CENTER_Y) / st)
    for i in range(i0, i1 + 1):
        for j in range(j0, j1 + 1):
            x = round(CENTER_X + i * st, 6)
            y = round(CENTER_Y + j * st, 6)
            if math.hypot(x - CENTER_X, y - CENTER_Y) <= _MAN_R_EDGE_MM:
                pts.append((x, y))
    pset = set(pts)
    eok = lambda ax, ay, bx, by, layer: _man_edge_ok(
        padr, trk, vias, ax, ay, bx, by, net, layer)
    a_seed = [p for p in pts
              if (p[0] - A[0]) ** 2 + (p[1] - A[1]) ** 2 <= 1.0
              and eok(A[0], A[1], p[0], p[1], 0)]
    b_seed = {p for p in pts
              if (p[0] - B[0]) ** 2 + (p[1] - B[1]) ** 2 <= 1.0
              and eok(p[0], p[1], B[0], B[1], 0)}
    if not a_seed or not b_seed:
        return None
    xnodes = set()
    for nx, ny, nl in neut:
        if not (x0 <= nx <= x1 and y0 <= ny <= y1):
            continue
        if math.hypot(nx - CENTER_X, ny - CENTER_Y) > _MAN_R_EDGE_MM:
            continue
        xnodes.add((round(nx, 6), round(ny, 6), nl))
    ecache, vokcache = {}, {}

    def eok_c(x, y, qx, qy, layer):
        key = (x, y, qx, qy, layer)
        v = ecache.get(key)
        if v is None:
            v = eok(x, y, qx, qy, layer)
            ecache[key] = v
        return v

    def vok_c(x, y):
        v = vokcache.get((x, y))
        if v is None:
            v = _man_via_ok(padr, trk, vias, x, y, net)
            vokcache[(x, y)] = v
        return v

    def neighbors(x, y, layer):
        out = []
        for dx, dy in ((st, 0), (-st, 0), (0, st), (0, -st)):
            qx, qy = round(x + dx, 6), round(y + dy, 6)
            if (qx, qy) in pset:
                out.append((qx, qy, layer))
        for qx, qy, ql in sorted(xnodes):
            if ql != layer or (qx, qy) == (x, y):
                continue
            if (qx - x) ** 2 + (qy - y) ** 2 <= 0.45 ** 2 + 1e-9:
                out.append((qx, qy, ql))
        if (x, y, layer) in xnodes:
            for px, py in pts:
                if (px - x) ** 2 + (py - y) ** 2 <= 0.45 ** 2 + 1e-9:
                    if (px, py) != (x, y):
                        out.append((px, py, layer))
        return out

    ctr = itertools.count()
    dist, prev, heap = {}, {}, []
    for p in a_seed:
        heapq.heappush(heap, ((p[0] - A[0]) ** 2 + (p[1] - A[1]) ** 2,
                              next(ctr), (p[0], p[1], 0)))
    for qx, qy, ql in sorted(xnodes):
        if ql == 0 and (qx - A[0]) ** 2 + (qy - A[1]) ** 2 <= 1.0 + 1e-9:
            if eok_c(A[0], A[1], qx, qy, 0):
                heapq.heappush(heap, (0.0, next(ctr), (qx, qy, ql)))
    goal = None
    while heap:
        c, _, (x, y, layer) = heapq.heappop(heap)
        if (x, y, layer) in dist:
            continue
        dist[(x, y, layer)] = c
        if (x, y) in b_seed and layer == 0:
            goal = (x, y, layer)
            break
        if ((x, y, layer) in xnodes
                and (x - B[0]) ** 2 + (y - B[1]) ** 2 <= 1.0 + 1e-9
                and layer == 0 and eok_c(x, y, B[0], B[1], 0)):
            prev[(B[0], B[1], 0)] = (x, y, layer)
            goal = (B[0], B[1], 0)
            break
        for qx, qy, ql in neighbors(x, y, layer):
            if (qx, qy, ql) in dist or not eok_c(x, y, qx, qy, ql):
                continue
            prev[(qx, qy, ql)] = (x, y, layer)
            heapq.heappush(heap, (c + (1.0 if ql == 0 else 1.2),
                                  next(ctr), (qx, qy, ql)))
        nl = 1 - layer
        if (x, y, nl) not in dist and vok_c(x, y):
            prev[(x, y, nl)] = (x, y, layer)
            heapq.heappush(heap, (c + _MAN_VIA_COST, next(ctr), (x, y, nl)))
    if goal is None:
        return None
    path = [goal]
    while path[-1] in prev:
        path.append(prev[path[-1]])
    path.reverse()
    seq = [(A[0], A[1], 0)] + [(p[0], p[1], p[2]) for p in path]
    if goal != (B[0], B[1], 0):
        seq.append((B[0], B[1], 0))
    return seq


def _man_runs(seq) -> list:
    """Seq de pontos -> runs retas [[(x,y,camada), ...]] (funde colineares)."""
    runs = [[seq[0]]]
    for p in seq[1:]:
        last = runs[-1][-1]
        if p[2] != last[2]:
            runs[-1].append(p)
            runs.append([p])
        elif len(runs[-1]) >= 2:
            a0, a1 = runs[-1][-2], last
            d1 = (a1[0] - a0[0], a1[1] - a0[1])
            d2 = (p[0] - a1[0], p[1] - a1[1])
            if (abs(d1[0] * d2[1] - d1[1] * d2[0]) < 1e-9
                    and (d1[0] * d2[0] + d1[1] * d2[1]) > 0):
                runs[-1].append(p)
            else:
                runs.append([a1, p])
        else:
            runs[-1].append(p)
    return [r for r in runs if len(r) >= 2]


def _man_commit(board, padr, trk, vias, net, seq, routed_tracks):
    """Valida (vias novas hole-to-hole) e desenha runs/vias. None se inválido."""
    new_vias = [(seq[i][0], seq[i][1]) for i in range(len(seq) - 1)
                if seq[i][2] != seq[i + 1][2]]
    for i, (vx, vy) in enumerate(new_vias):
        for ex, ey, evnet in vias:
            need = 0.55 if evnet == net else 0.8
            if math.hypot(vx - ex, vy - ey) <= need + 1e-9:
                return None
        for wx, wy in new_vias[i + 1:]:
            if math.hypot(vx - wx, vy - wy) <= 0.55 + 1e-9:
                return None
        if not _man_via_ok(padr, trk, vias, vx, vy, net):
            return None
    layer_name = {0: "F.Cu", 1: "B.Cu"}
    for vx, vy in new_vias:
        bb.add_via(board, net, vx, vy)
        _ALL_VIAS.append((vx, vy, net))
        vias.append((vx, vy, net))
    for r in _man_runs(seq):
        bb.add_track(board, net, r[0][0], r[0][1], r[-1][0], r[-1][1],
                     layer=layer_name[r[0][2]], width_mm=_MAN_W_MM)
        routed_tracks.append((r[0][0], r[0][1], r[-1][0], r[-1][1],
                              r[0][2], net, _MAN_W_MM))
    return (len(_man_runs(seq)), len(new_vias))


def route_manual(board, placed, routed_tracks) -> tuple:
    """Terceira passada: pares de _MAN_PAIRS via _man_find (margem 3, depois
    8); desenha com _man_commit. Retorna (fechados, restantes): fechados =
    [(net, a, b, n_runs, n_vias)], restantes = [(net, a, b)]."""
    padr = _man_caches(placed)
    vias = list(_ALL_VIAS)
    fechados, restantes = [], []
    for net, r0, p0, r1, p1 in _MAN_PAIRS:
        if r0 not in placed or r1 not in placed:
            restantes.append((net, f"{r0}.{p0}", f"{r1}.{p1}"))
            continue
        trk = {0: [t for t in routed_tracks if t[4] == 0],
               1: [t for t in routed_tracks if t[4] == 1]}
        A = bb.pad_position_mm(placed[r0], p0)
        B = bb.pad_position_mm(placed[r1], p1)
        seq = _man_find(placed, padr, trk, vias, net, A, B)
        if seq is None:
            seq = _man_find(placed, padr, trk, vias, net, A, B, margin=8.0)
        if seq is None:
            restantes.append((net, f"{r0}.{p0}", f"{r1}.{p1}"))
            continue
        res = _man_commit(board, padr, trk, vias, net, seq, routed_tracks)
        if res is None:
            restantes.append((net, f"{r0}.{p0}", f"{r1}.{p1}"))
            continue
        n_runs, n_vias = res
        fechados.append((net, f"{r0}.{p0}", f"{r1}.{p1}", n_runs, n_vias))
    return fechados, restantes


# ---------------------------------------------------------------------------
# Aterramento: malha sob o die pad + vias de costura + zona GND em B.Cu
# ---------------------------------------------------------------------------
# Refs com pads GND elegíveis para via de costura (item b). U1 só nos pinos
# 20/29 (o die pad U1.33 recebe a malha 3x3 do item a). R1 NÃO entra: vai em
# VDD_BAT/RESET — o filtro por netname já o exclui, mas fica explícito aqui.
_GND_STITCH_REFS = {"U1", "SHLD1", "BT1", "TP4", "ANT1"} | {f"C{i}" for i in range(1, 11)}
_GND_STITCH_U1_PINS = {"20", "29"}
_GND_CLEAR_MM = 0.3          # (doc) folga mínima via x trilhas/pads de outras nets
_GND_STITCH_TRACK_MM = 0.3   # largura da trilha GND pad→via de costura
_GND_STITCH_OFFSETS_MM = (0.8, 0.6, 0.9)  # distância via↔pad (item b)
_DIE_MESH_STEP_MM = 1.2      # passo da malha 3x3 sob o die pad (item a)


def _dist_point_seg(px, py, x1, y1, x2, y2) -> float:
    """Distância (mm) do ponto (px, py) ao segmento (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 <= 0.0:
        return math.hypot(px - x1, py - y1)
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def _pad_rect(fp, pad) -> tuple:
    """(cx, cy, w, h, ang_rad) do pad — retângulo em coords absolutas."""
    cx, cy = pad_abs_pos(fp, pad.GetNumber())
    return (cx, cy, bb._mm(pad.GetSizeX()), bb._mm(pad.GetSizeY()),
            math.radians(pad.GetOrientationDegrees()))


def _dist_point_rect(px, py, cx, cy, w, h, ang) -> float:
    """Distância (mm) do ponto ao retângulo (0 se dentro)."""
    c, s = math.cos(ang), math.sin(ang)
    dx, dy = px - cx, py - cy
    qx = dx * c + dy * s
    qy = -dx * s + dy * c
    ex = max(abs(qx) - w / 2.0, 0.0)
    ey = max(abs(qy) - h / 2.0, 0.0)
    return math.hypot(ex, ey)


def _dist_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang, sample=0.05) -> float:
    """Distância (mm) de um segmento ao retângulo (amostragem)."""
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
    """True se os segmentos (x1,y1)-(x2,y2) e (x3,y3)-(x4,y4) se cruzam."""
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) > (by - ay) * (cx - ax)
    return (ccw(x1, y1, x3, y3, x4, y4) != ccw(x2, y2, x3, y3, x4, y4) and
            ccw(x1, y1, x2, y2, x3, y3) != ccw(x1, y1, x2, y2, x4, y4))


def _dist_seg_seg(x1, y1, x2, y2, x3, y3, x4, y4) -> float:
    """Distância (mm) entre dois segmentos."""
    if _segs_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
        return 0.0
    return min(
        _dist_point_seg(x1, y1, x3, y3, x4, y4),
        _dist_point_seg(x2, y2, x3, y3, x4, y4),
        _dist_point_seg(x3, y3, x1, y1, x2, y2),
        _dist_point_seg(x4, y4, x1, y1, x2, y2),
    )


def _pad_half_dim(fp, pad) -> float:
    """Metade da maior dimensão do pad (mm)."""
    return max(bb._mm(pad.GetSizeX()), bb._mm(pad.GetSizeY())) / 2.0


def _clear_of_other_nets(placed, px, py, net_name, routed_tracks,
                         item_radius=0.3, clearance=0.2, check_pads=True) -> bool:
    """True se um item circular de raio `item_radius` em (px, py) respeita
    `clearance` contra trilhas (largura/2 por trilha), vias e pads (distância
    ao RETÂNGULO do pad) de outras nets."""
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
            for pad in fp.Pads():  # KiCad 10: GetPads() exige aPadNumber
                net = pad.GetNetname()
                if net == net_name:  # pads sem rede (NC) também bloqueiam
                    continue
                cx, cy, w, h, ang = _pad_rect(fp, pad)
                if _dist_point_rect(px, py, cx, cy, w, h, ang) < item_radius + clearance:
                    return False
    return True


def _seg_clear_of_other_nets(placed, x1, y1, x2, y2, net_name, routed_tracks,
                             item_half=0.15, clearance=0.2) -> bool:
    """True se um segmento de trilha (meia-largura `item_half`) respeita
    `clearance` contra trilhas, vias e pads (retângulo) de outras nets."""
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
            if net == net_name:  # pads sem rede (NC) também bloqueiam
                continue
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            if _dist_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang) < item_half + clearance:
                return False
    return True


def _seg_clear_layer(placed, x1, y1, x2, y2, net_name, routed_tracks,
                       layer_node, item_half=0.15, clearance=0.2) -> bool:
    """Variante de _seg_clear_of_other_nets só contra cobre da MESMA camada
    (trilhas layer_node + vias through + pads layer_node). A versão cega à
    camada rejeitava spur GND em F.Cu por causa de trilha B.Cu sob ele —
    sem violação real de DRC (camadas distintas)."""
    for tx1, ty1, tx2, ty2, tlayer, tnet, tw in routed_tracks:
        if tnet == net_name or tlayer != layer_node:
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
            if net == net_name:  # pads sem rede (NC) também bloqueiam
                continue
            if _PAD_LAYER_NODE.get(pad.GetLayer(), 0) != layer_node:
                continue
            cx, cy, w, h, ang = _pad_rect(fp, pad)
            if _dist_seg_rect(x1, y1, x2, y2, cx, cy, w, h, ang) < item_half + clearance:
                return False
    return True


def _gnd_pad_connected(placed, fp, pin, routed_tracks) -> bool:
    """True se o pad GND já toca cobre GND (trilha/via sobreposta).

    Evita pendência falsa: um stitch vizinho cujo spur/via cai sobre o pad
    (mesma net) já conecta o pad à zona — sem via própria. Toque EXATO:
    distância segmento↔retângulo do pad ≤ tw/2, ou ponto↔retângulo ≤ 0,3
    para via (nada de meia-diagonal — superestimava e pulava pads
    desconectados).
    """
    gnd = "GND"
    pad = fp.FindPadByNumber(str(pin))
    _px, _py, _w, _h, _ang = _pad_rect(fp, pad)
    for x1, y1, x2, y2, _layer, tnet, tw in routed_tracks:
        if tnet != gnd:
            continue
        if _man_seg_rect(x1, y1, x2, y2, _px, _py, _w, _h, _ang) <= tw / 2.0 + 1e-9:
            return True
    for vx, vy, vnet in _ALL_VIAS:
        if vnet != gnd:
            continue
        if _dist_point_rect(vx, vy, _px, _py, _w, _h, _ang) <= 0.3 + 1e-9:
            return True
    return False


def _gnd_spur_L(board, placed, routed_tracks, px, py) -> bool:
    """Spur GND em L (2 segmentos F.Cu 0,3 + via): saída horizontal e depois
    vertical (e vice-versa). Para pads encaixotados (U1.20/U1.29/C4.2) onde
    nenhum spur reto tem via+trilha livres. Varredura determinística por
    comprimento total crescente (passo 0,1, alcance 1,5 mm). True se desenhou.
    """
    gnd = "GND"
    cands = []
    d = 0.1
    while d <= 1.51:
        for s1 in (-1.0, 1.0):
            cands.append(("FH", round(px + s1 * d, 6)))
            cands.append(("FV", round(py + s1 * d, 6)))
        d = round(d + 0.1, 6)
    # ordena por comprimento mínimo possível (determinístico)
    cands.sort(key=lambda c: abs(c[1] - (px if c[0] == "FH" else py)))
    for fam, e in cands:
        d2 = 0.1
        while d2 <= 1.51:
            for s2 in (-1.0, 1.0):
                if fam == "FH":
                    xE, vy = e, round(py + s2 * d2, 6)
                    segs = ((px, py, xE, py), (xE, py, xE, vy))
                else:
                    vx, yE = round(px + s2 * d2, 6), e
                    segs = ((px, py, vx, py), (vx, py, vx, yE))
                    xE, vy = vx, yE
                if math.hypot(xE - CENTER_X, vy - CENTER_Y) > 15.0:
                    d2ok = True
                else:
                    d2ok = False
                    if any(math.hypot(xE - ex, vy - ey) <= 0.55 + 1e-9
                           for ex, ey, _vn in _ALL_VIAS):
                        d2ok = True
                    elif not _clear_of_other_nets(placed, xE, vy, gnd,
                                                  routed_tracks):
                        d2ok = True
                    elif not all(_seg_clear_layer(placed, a, b, c, e_,
                                                  gnd, routed_tracks, 0,
                                                  item_half=0.15)
                                 for a, b, c, e_ in segs):
                        d2ok = True
                if not d2ok:
                    for a, b, c, e_ in segs:
                        bb.add_track(board, gnd, a, b, c, e_, layer="F.Cu",
                                     width_mm=_GND_STITCH_TRACK_MM)
                        routed_tracks.append((a, b, c, e_, 0, gnd,
                                              _GND_STITCH_TRACK_MM))
                    bb.add_via(board, gnd, xE, vy)
                    _ALL_VIAS.append((xE, vy, gnd))
                    return True
            d2 = round(d2 + 0.1, 6)
    return False


def add_die_mesh(board, placed) -> int:
    """Malha 3x3 de vias GND sob o die pad U1.33 — DEVE rodar ANTES de
    route_all.

    Motivo (auditoria §3 item 11): com o roteamento primeiro, trilhas de
    outras nets (XC1/XC2/DEC2/SWDCLK) passam por cima/ sob o die pad e as 9
    posições da malha são todas rejeitadas pela checagem de colisão (via
    through fere trilha em B.Cu) — resultado: ZERO vias GND sob o die pad.
    Colocando a malha primeiro, as vias entram em _ALL_VIAS e o roteador
    desvia os sinais (o B.Cu sob o die pad fica reservado para o retorno
    GND). Retorna o nº de vias da malha.
    """
    gnd = "GND"
    n_vias = 0
    dx_pad, dy_pad = pad_abs_pos(placed["U1"], "33")
    for ox in (-_DIE_MESH_STEP_MM, 0.0, _DIE_MESH_STEP_MM):
        for oy in (-_DIE_MESH_STEP_MM, 0.0, _DIE_MESH_STEP_MM):
            vx, vy = dx_pad + ox, dy_pad + oy
            if not _clear_of_other_nets(placed, vx, vy, gnd, [],
                                        check_pads=False):
                continue  # colidiu com pad de outra net -> pula a via
            bb.add_via(board, gnd, vx, vy)
            _ALL_VIAS.append((vx, vy, gnd))
            n_vias += 1
    return n_vias


def add_shld_rings(board, placed, routed_tracks) -> tuple:
    """Anéis de cobre do footprint SHLD1_Ferrite_Shield_22mm — REMOVIDOS.

    A lib traz o círculo r=11 mm em F.Cu E B.Cu. O anel de F.Cu cruza o
    board inteiro (todas as rotas de saída do centro cruzam r=11) — origem
    de ~50 curtos/clearance/solder_mask_bridge na iteração 2. O anel de
    B.Cu, além de cruzar rotas em B.Cu, faz o fill_zones() do KiCad 10.0.6
    dar SEGFAULT (confirmado por biseção: anel presente -> crash no fill;
    sem anel -> fill ok). Ambos os anéis são removidos do board; a conexão
    de escudo fica no pad 1 do SHLD1 (GND, B.Cu), que funde com a zona.
    Retorna (n_removidos, 0).
    """
    fp = placed["SHLD1"]
    removed = 0
    # captura UMA vez: iterar GraphicalItems() depois de Remove segfaulta
    # (o iterador C++ toca o item já removido)
    items = [d for d in fp.GraphicalItems()]
    for d in items:
        if (d.GetClass() == "PCB_SHAPE"
                and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
                and d.GetLayer() in (pcbnew.F_Cu, pcbnew.B_Cu)):
            fp.Remove(d)
            removed += 1
    # proxies SWIG dos itens removidos ficam pendurados na lista `items` e
    # derrubam o ZONE_FILLER com SEGFAULT mais tarde (GC toca objeto C++
    # já liberado). Solta as referências e força coleta.
    del items
    gc.collect()
    return removed, 0


def add_ground(board, placed, routed_tracks, grid) -> tuple:
    """Aterramento: vias de costura nos pads GND + zona GND em B.Cu.

    (A malha 3x3 sob o die pad U1.33 virou add_die_mesh() e roda ANTES do
    roteamento — ver docstring lá.)

    a) Via de costura a 0,8 mm de cada pad GND em F.Cu (U1.20/U1.29, SHLD1,
       J1, TP4 e o pino GND de C1..C10), na direção radial para fora do
       centro do disco; 4 direções candidatas (radial + rotações de 90°),
       vence a primeira livre (via ≥ 0,5 mm de trilhas/pads de outras nets E
       trilha GND 0,3 mm pad→via sem colisão); nenhuma livre -> pendência.
       A trilha GND pad→via garante a conexão pad↔via↔zona (mata os
       unconnected de via/ilha GND em F.Cu). Pads já em B.Cu não recebem via
       (a zona em B.Cu os alcança diretamente).
    b) Zona GND circular r=16 mm centrada em (100,100) em B.Cu + fill.

    grid: aceito por compatibilidade de assinatura com route_all (as vias de
    costura usam offsets exatos de pad, não pontos da grade).

    Retorna (n_vias_gnd, pendencias):
    - n_vias_gnd: total de vias GND adicionadas (costura);
    - pendencias: [(ref.pin, motivo), ...] vias de costura não colocadas.
    """
    gnd = "GND"
    n_vias = 0
    pendencias = []

    # --- (a) vias de costura nos pads GND em F.Cu ---------------------------
    for ref in sorted(_GND_STITCH_REFS):
        fp = placed.get(ref)
        if fp is None:
            continue
        for pad in fp.Pads():  # KiCad 10: GetPads() exige aPadNumber
            if pad.GetNetname() != gnd:
                continue
            pin = pad.GetNumber()
            if ref == "U1" and pin not in _GND_STITCH_U1_PINS:
                continue  # die pad (33) já tem a malha; demais pinos fora da lista
            if pad.GetLayer() == pcbnew.B_Cu:
                continue  # já em B.Cu: a zona alcança o pad
            if _gnd_pad_connected(placed, fp, pin, routed_tracks):
                continue  # spur/via de stitch vizinho já toca o pad (mesma net)
            px, py = pad_abs_pos(fp, pin)
            base = math.atan2(py - CENTER_Y, px - CENTER_X)
            placed_stitch = False
            # 8 direções (radial + 45°) × 3 offsets (0,6–0,9 mm): vence a
            # primeira combinação livre (via ≥ 0,5 mm de trilhas/pads de
            # outras nets E trilha GND 0,3 mm pad→via sem colisão).
            for k in range(8):
                ang = base + k * math.pi / 4.0
                for off in _GND_STITCH_OFFSETS_MM:
                    vx = px + off * math.cos(ang)
                    vy = py + off * math.sin(ang)
                    # borda: via + trilha precisam de copper_edge_clearance
                    # 0,5 mm (raio útil 16 - 0,5 - via 0,3 ≈ 15,2; usa 15,0)
                    if math.hypot(vx - CENTER_X, vy - CENTER_Y) > 15.0:
                        continue
                    # furos co-locados: via nova a ≤0,55 mm de via existente
                    # (qualquer net, mesma regra hole-to-hole da 2ª passada) —
                    # sem isto BT1.2 e SHLD1.1 (pads concêntricos em (100,100))
                    # elegem o mesmo ponto (100.8,100) -> holes_co_located.
                    if any(math.hypot(vx - ex, vy - ey) <= 0.55 + 1e-9
                           for ex, ey, _vn in _ALL_VIAS):
                        continue
                    if not _clear_of_other_nets(placed, vx, vy, gnd,
                                                routed_tracks):
                        continue
                    # trilha GND 0,3 mm pad→via: conexão pad↔via↔zona
                    if not _seg_clear_of_other_nets(placed, px, py, vx, vy,
                                                    gnd, routed_tracks,
                                                    item_half=0.15):
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
                if placed_stitch:
                    break
            if not placed_stitch:
                # Fallback estendido (3ª passada): 16 direções × offsets
                # 0,6–1,5 mm, com o spur pad→via testado só contra cobre F.Cu
                # (_seg_clear_layer — trilhas B.Cu sob o spur não são curto).
                # Via continua com checagem cheia + hole-to-hole 0,55.
                for k in range(16):
                    ang = base + k * math.pi / 8.0
                    off = 0.6
                    while off <= 1.51:
                        vx = px + off * math.cos(ang)
                        vy = py + off * math.sin(ang)
                        if math.hypot(vx - CENTER_X, vy - CENTER_Y) <= 15.0:
                            if not any(math.hypot(vx - ex, vy - ey) <= 0.55 + 1e-9
                                       for ex, ey, _vn in _ALL_VIAS):
                                if _clear_of_other_nets(placed, vx, vy, gnd,
                                                        routed_tracks):
                                    if _seg_clear_layer(placed, px, py, vx, vy,
                                                        gnd, routed_tracks, 0,
                                                        item_half=0.15):
                                        bb.add_track(board, gnd, px, py, vx, vy,
                                                     layer="F.Cu", width_mm=_GND_STITCH_TRACK_MM)
                                        routed_tracks.append((px, py, vx, vy, 0, gnd,
                                                              _GND_STITCH_TRACK_MM))
                                        bb.add_via(board, gnd, vx, vy)
                                        _ALL_VIAS.append((vx, vy, gnd))
                                        n_vias += 1
                                        placed_stitch = True
                                        break
                        off = round(off + 0.1, 6)
                    if placed_stitch:
                        break
            if not placed_stitch:
                placed_stitch = _gnd_spur_L(board, placed, routed_tracks,
                                            px, py)
            if not placed_stitch:
                pendencias.append((f"{ref}.{pin}",
                                   "nenhuma das 8 direções x 3 offsets livre "
                                   "(via+trilha)"))

    # --- (b) zona GND em B.Cu ------------------------------------------------
    # r=15,5 (não 16,0): a zona encostada na borda gerava 11 violações de
    # copper_edge_clearance (mín. 0,5 mm) após o fix do raio do Edge.Cuts.
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
    """Board circular Ø32 mm em (100,100) + placement da tabela PLACEMENT.

    Retorna (board, {ref: FOOTPRINT}, nets_assigned). Lib_id de cada ref vem de
    parse_footprints(); a resolução do .pretty é feita por bb.place_footprint
    via FP_LIB_ROOTS (custom primeiro, depois /usr/share/kicad/footprints).
    Após o placement, parseia exports/wristband_discreto.net e atribui nets
    aos pads via bb.assign_pad_net.
    """
    fp_map = parse_footprints(SCH_FILE)

    board = bb.create_board(shape="circle", diameter_mm=32.0, layers=2, thickness_mm=0.8)
    # create_board centra na origem; move o círculo Edge.Cuts p/ (100,100).
    # Círculo KiCad = centro (start) + ponto na borda (end). SetCenter sozinho
    # deixa o `end` em (16,0) absoluto e o raio vira ~130,6 mm (bug da
    # auditoria). Replicar create_board: SetRadius via SetEnd na mesma escala
    # (bb._nm) — mesmo padrão de gen_board_modulo.py (linhas 426-431).
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE:
            d.SetCenter(pcbnew.VECTOR2I(bb._nm(CENTER_X), bb._nm(CENTER_Y)))
            d.SetEnd(pcbnew.VECTOR2I(bb._nm(CENTER_X + 16.0), bb._nm(CENTER_Y)))
            break

    placed = {}
    _PLACED_CACHE.clear()
    for ref in sorted(PLACEMENT):
        if ref not in fp_map:
            raise RuntimeError(f"ref {ref!r} da tabela de placement sem Footprint no esquemático")
        dx, dy = PLACEMENT[ref]
        layer = "B.Cu" if ref in FLIP_REFS else "F.Cu"
        placed[ref] = bb.place_footprint(
            board, fp_map[ref], CENTER_X + dx, CENTER_Y + dy, ref=ref,
            layer=layer, rot_deg=ROTATION.get(ref, 0.0)
        )
        _PLACED_CACHE[ref] = placed[ref]

    # --- Normalização de camada dos pads de footprints em B.Cu --------------
    # KiCad 10 (FootprintLoad): footprint nativo B.Cu carrega com fp em B_Cu
    # mas pads ainda em F_Cu (o Flip do place_footprint é pulado porque o lado
    # nativo já é o pedido — padrão corrigido do board_builder). Resultado: pad
    # de J1 ficava em F.Cu (auditoria §3 item 5). Força o LSET do pad para o
    # lado do footprint.
    for ref, fp in placed.items():
        if fp.GetLayer() != pcbnew.B_Cu:
            continue
        for pad in fp.Pads():
            if pad.GetLayer() == pcbnew.F_Cu:
                ls = pcbnew.LSET()
                for lay in (pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_Paste):
                    ls.AddLayer(lay)
                pad.SetLayerSet(ls)

    # --- Courtyard do U1 enxugado (margem 0,25 -> 0,15) ----------------------
    # O QFN-32-1EP padrão KiCad tem courtyard ±3,1 mm; com a aba do BT1 a
    # 0,21 mm dos pads superiores, os courtyards se sobrepõem (falso
    # positivo — a restrição real é pad a pad, já verificada). Encolhe o
    # octógono 0,15 mm em direção ao centro (margem 0,15 sobre os pads).
    if "U1" in placed:
        cx_u, cy_u = CENTER_X, CENTER_Y + PLACEMENT["U1"][1]
        for d in placed["U1"].GraphicalItems():
            if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.F_CrtYd:
                sxp, syp = d.GetStart().x / 1e6, d.GetStart().y / 1e6
                exp_, eyp = d.GetEnd().x / 1e6, d.GetEnd().y / 1e6
                def _shrink(v, c):
                    return v + (-0.15 if v >= c else 0.15)
                d.SetStart(pcbnew.VECTOR2I(bb._nm(_shrink(sxp := sxp, cx_u) if False else _shrink(sxp, cx_u)),
                                           bb._nm(_shrink(syp := syp, cy_u) if False else _shrink(syp, cy_u))))
                d.SetEnd(pcbnew.VECTOR2I(bb._nm(_shrink(exp_, cx_u)),
                                         bb._nm(_shrink(eyp := eyp, cy_u) if False else _shrink(eyp, cy_u))))

    # --- Courtyard do C10 enxugado (0603: margem 0,33 -> 0,15 em x) ---------
    if "C10" in placed:
        cx10, cy10 = (CENTER_X + PLACEMENT["C10"][0],
                      CENTER_Y + PLACEMENT["C10"][1])
        for d in placed["C10"].GraphicalItems():
            if d.GetClass() == "PCB_SHAPE" and d.GetLayer() == pcbnew.F_CrtYd:
                sxp, syp = d.GetStart().x / 1e6, d.GetStart().y / 1e6
                exp_, eyp = d.GetEnd().x / 1e6, d.GetEnd().y / 1e6
                d.SetStart(pcbnew.VECTOR2I(bb._nm(sxp + (-0.18 if sxp >= cx10 else 0.18)),
                                           bb._nm(syp)))
                d.SetEnd(pcbnew.VECTOR2I(bb._nm(exp_ + (-0.18 if exp_ >= cx10 else 0.18)),
                                         bb._nm(eyp)))

    # --- Atribuição de nets (parse da netlist exportada do esquemático) ----
    # parse_netlist já descarta 'unconnected-...'; refs fora do board
    # (ex.: TAG1, inlay adesivo) são pulados.
    nets = parse_netlist(NET_FILE)
    nets_assigned = 0
    for net_name in sorted(nets):
        for ref, pin in nets[net_name]:
            if ref not in placed:
                continue
            bb.assign_pad_net(placed[ref], pin, board, net_name)
            nets_assigned += 1

    # --- BT1 (Keystone 1060): polaridade conforme drawing 1060 rev C ---------
    # Pad 1 (aba +14,655) = VDD_BAT (positivo — vem da netlist, pino VDD do
    # símbolo). Pads 2 (central 11×7,01) e 3 (aba −14,655) = GND/negativo:
    # o símbolo só expõe o pino 2 (e a netlist o marca unconnected), e o pad 3
    # não existe no símbolo — amarrados aqui, no PCB, como manda o drawing
    # ("center pad and one end tab are the negative terminal").
    if "BT1" in placed:
        for pin in ("2", "3"):
            bb.assign_pad_net(placed["BT1"], pin, board, "GND")
            nets_assigned += 1

    # --- Assert: raio do Edge.Cuts = 16,000 mm (disco Ø32) -------------------
    for d in board.GetDrawings():
        if (d.GetLayer() == pcbnew.Edge_Cuts
                and d.GetShape() == pcbnew.SHAPE_T_CIRCLE):
            c, e = d.GetCenter(), d.GetEnd()
            r = math.hypot(bb._mm(e.x) - bb._mm(c.x),
                           bb._mm(e.y) - bb._mm(c.y))
            assert abs(r - 16.0) < 1e-6, f"Edge.Cuts raio {r} != 16.0"
            break
    else:
        raise RuntimeError("Edge.Cuts circular não encontrado")

    return board, placed, nets_assigned


if __name__ == "__main__":
    board, placed, nets_assigned = build_board()
    nets = parse_netlist(NET_FILE)
    grid = build_grid()
    mesh_vias = add_die_mesh(board, placed)
    pre_tracks = []  # obstáculos pré-roteamento (anéis do SHLD1)
    ring_removed, ring_seg = add_shld_rings(board, placed, pre_tracks)
    routed_tracks, pendencias = route_all(board, placed, nets, grid,
                                          routed_tracks=pre_tracks)
    pend_1a = list(pendencias)
    pendencias, n_2a = route_pending_second_pass(board, placed, grid,
                                                 routed_tracks, pendencias)
    man_ok, man_rest = route_manual(board, placed, routed_tracks)
    gnd_vias, gnd_pend = add_ground(board, placed, routed_tracks, grid)
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == "PCB_VIA")
    print(f"trilhas roteadas: {len(routed_tracks)}")
    print(f"vias: {n_vias}")
    print(f"pendências 1ª passada ({len(pend_1a)}): {pend_1a}")
    print(f"2ª passada: {n_2a} pares roteados, "
          f"{len(pendencias)} pendências restantes: {pendencias}")
    print(f"3ª passada (manual): {len(man_ok)} pares fechados: {man_ok}")
    print(f"3ª passada restantes ({len(man_rest)}): {man_rest}")
    print(f"vias GND adicionadas: {gnd_vias} (malha die pad: {mesh_vias})")
    print(f"SHLD1: anéis F.Cu removidos: {ring_removed}, segs obstáculo B.Cu: {ring_seg}")
    print(f"pendências de via GND ({len(gnd_pend)}): {gnd_pend}")
    out = bb.save_board(board, OUT_FILE)
    print(f"footprints colocados: {len(placed)}")
    print(f"nets atribuídas: {nets_assigned} pads")
    print(f"pontos da grade: {len(grid)}")
    # Exemplo: nós bloqueados para a net GND (sem trilhas roteadas ainda).
    obstacles_gnd, _via_obs_gnd = build_obstacles(board, placed, "GND", [])
    print(f"nós bloqueados para GND: {len(obstacles_gnd)}")
    # Teste A*: caminho livre de (100,100,0) até (108,108,0) — 16+16 passos
    # de 0,5 mm => 32 passos => 33 nós no caminho.
    path_test = astar_route(grid, set(), (100.0, 100.0, 0), (108.0, 108.0, 0))
    print(f"teste A* (100,100,0)->(108,108,0): comprimento do caminho = "
          f"{len(path_test) if path_test else None}")
    print(f"board salvo em: {out}")
