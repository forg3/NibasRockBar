#!/usr/bin/env python3
"""board_builder.py — programmatic KiCad 10 board construction via pcbnew.

Reusable helpers for layout workers (plan frentes A/B/C, step 1.1).

Proven on KiCad 10.0.6-1.fc44 (python3 `import pcbnew`). pcbnew prints
harmless PROPERTY_ENUM asserts to stderr at import time — ignore them.

Units: all public functions take/return millimetres (float); conversion to
KiCad internal nanometres happens here. Layers accept the friendly names
"F.Cu", "B.Cu", "In1.Cu".. or raw pcbnew layer ids.

Requires: python3 stdlib + pcbnew. No kiutils/skidl (absent on this host).
"""

from __future__ import annotations

import argparse
import math
import os
import sys
import traceback
from pathlib import Path

import pcbnew

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TRACK_WIDTH_MM = 0.25
DEFAULT_VIA_DRILL_MM = 0.3
DEFAULT_VIA_DIAMETER_MM = 0.6
DEFAULT_EDGE_WIDTH_MM = 0.1
DEFAULT_ZONE_PRIORITY = 0

COPPER_LAYERS = {
    "F.Cu": pcbnew.F_Cu,
    "B.Cu": pcbnew.B_Cu,
    "In1.Cu": pcbnew.In1_Cu if hasattr(pcbnew, "In1_Cu") else None,
    "In2.Cu": pcbnew.In2_Cu if hasattr(pcbnew, "In2_Cu") else None,
}

# Footprint library search roots (first hit wins; override via env).
FP_LIB_ROOTS = [
    os.environ.get("KICAD_FOOTPRINTS_DIR", ""),
    "/usr/share/kicad/footprints",
    "/usr/local/share/kicad/footprints",
]


class BoardBuilderError(RuntimeError):
    """Raised on any construction failure with a precise message."""


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _nm(mm: float) -> int:
    """Millimetres -> KiCad internal nanometres (int)."""
    return int(pcbnew.FromMM(float(mm)))


def _mm(nm: int) -> float:
    """KiCad internal nanometres -> millimetres (float)."""
    return float(pcbnew.ToMM(int(nm)))


def _vec(x_mm: float, y_mm: float) -> "pcbnew.VECTOR2I":
    return pcbnew.VECTOR2I(_nm(x_mm), _nm(y_mm))


def _layer_id(layer) -> int:
    """Accept 'F.Cu'/'B.Cu'/... names or an already-numeric layer id."""
    if isinstance(layer, int):
        return layer
    key = str(layer)
    if key in COPPER_LAYERS and COPPER_LAYERS[key] is not None:
        return COPPER_LAYERS[key]
    raise BoardBuilderError(f"unsupported layer {layer!r}; known: {list(COPPER_LAYERS)}")


# ---------------------------------------------------------------------------
# Nets
# ---------------------------------------------------------------------------

def get_or_create_net(board: "pcbnew.BOARD", net_name: str) -> "pcbnew.NETINFO_ITEM":
    """Return the NETINFO_ITEM for net_name, creating + registering it if new."""
    if not net_name:
        raise BoardBuilderError("net name must be non-empty")
    net = board.FindNet(net_name)
    if net is None:
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
    return net


# ---------------------------------------------------------------------------
# Board creation
# ---------------------------------------------------------------------------

def create_board(
    width_mm: float = None,
    height_mm: float = None,
    *,
    shape: str = "rect",
    diameter_mm: float = None,
    layers: int = 2,
    thickness_mm: float = 0.8,
) -> "pcbnew.BOARD":
    """Create an empty board with an Edge.Cuts outline centred on the origin.

    - shape="rect": width_mm x height_mm rectangle (origin = centre).
    - shape="circle": diameter_mm disk (origin = centre) — wristband form factor.
    - layers: copper layer count (2 for all NibasRockBar boards; 4 enables
      the default KiCad stackup F.Cu, In1.Cu, In2.Cu, B.Cu).
    - thickness_mm: board thickness (design setting, used by STEP export;
      0.8 mm for both 2L and 4L wristband boards).
    """
    if shape not in ("rect", "circle"):
        raise BoardBuilderError(f"shape must be 'rect' or 'circle', got {shape!r}")
    if shape == "rect" and (width_mm is None or height_mm is None):
        raise BoardBuilderError("rect board needs width_mm and height_mm")
    if shape == "circle" and diameter_mm is None:
        raise BoardBuilderError("circle board needs diameter_mm")
    if int(layers) not in (2, 4):
        raise BoardBuilderError(f"layers must be 2 or 4, got {layers!r}")

    board = pcbnew.CreateEmptyBoard()
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(int(layers))
    ds.SetBoardThickness(_nm(thickness_mm))

    if int(layers) == 4:
        # Default KiCad 4L stackup order: F.Cu, In1.Cu, In2.Cu, B.Cu.
        # SetCopperLayerCount(4) enables exactly these four; verify so a
        # future default change cannot silently break us.
        for _name in ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu"):
            if not board.IsLayerEnabled(_layer_id(_name)):
                raise BoardBuilderError(f"4L stackup: layer {_name} not enabled after setup")

    if shape == "rect":
        hw, hh = float(width_mm) / 2.0, float(height_mm) / 2.0
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        for i in range(4):
            x1, y1 = corners[i]
            x2, y2 = corners[(i + 1) % 4]
            seg = pcbnew.PCB_SHAPE(board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetStart(_vec(x1, y1))
            seg.SetEnd(_vec(x2, y2))
            seg.SetWidth(_nm(DEFAULT_EDGE_WIDTH_MM))
            seg.SetLayer(pcbnew.Edge_Cuts)
            board.Add(seg)
    else:
        circ = pcbnew.PCB_SHAPE(board)
        circ.SetShape(pcbnew.SHAPE_T_CIRCLE)
        circ.SetCenter(_vec(0, 0))
        circ.SetRadius(int(_nm(diameter_mm) / 2))
        circ.SetWidth(_nm(DEFAULT_EDGE_WIDTH_MM))
        circ.SetLayer(pcbnew.Edge_Cuts)
        board.Add(circ)

    return board


# ---------------------------------------------------------------------------
# Footprints
# ---------------------------------------------------------------------------

def _resolve_fp_paths(lib_id: str) -> tuple[str, str]:
    """'Lib:Name' -> (<dir with Lib.pretty>, Name) using FP_LIB_ROOTS."""
    if ":" not in lib_id:
        raise BoardBuilderError(
            f"lib_id {lib_id!r} must be 'Lib:FootprintName' (e.g. 'Resistor_SMD:R_0603_1608Metric')"
        )
    lib, name = lib_id.split(":", 1)
    for root in FP_LIB_ROOTS:
        if not root:
            continue
        pretty = Path(root) / f"{lib}.pretty"
        if pretty.is_dir():
            return str(pretty), name
    searched = [r for r in FP_LIB_ROOTS if r]
    raise BoardBuilderError(
        f"footprint library {lib!r} not found; searched roots: {searched} "
        f"(set KICAD_FOOTPRINTS_DIR to override)"
    )


def place_footprint(
    board: "pcbnew.BOARD",
    lib_id: str,
    x_mm: float,
    y_mm: float,
    *,
    rot_deg: float = 0.0,
    ref: str = None,
    value: str = None,
    layer: str = "F.Cu",
) -> "pcbnew.FOOTPRINT":
    """Load a footprint from a KiCad library, add it to the board, position it.

    The footprint is embedded into the .kicad_pcb on save (kicad-cli never
    loads fp-lib-table, so embedding is the only CLI-safe mechanism).
    Returns the FOOTPRINT for further pad/net wiring.
    """
    lib_path, fp_name = _resolve_fp_paths(lib_id)
    fp = pcbnew.FootprintLoad(lib_path, fp_name)
    if fp is None:
        raise BoardBuilderError(f"footprint {fp_name!r} not found in {lib_path!r}")
    board.Add(fp)
    fp.SetPosition(_vec(x_mm, y_mm))
    fp.SetOrientationDegrees(float(rot_deg))
    side = _layer_id(layer)
    if side not in (pcbnew.F_Cu, pcbnew.B_Cu):
        raise BoardBuilderError("footprint layer must be 'F.Cu' or 'B.Cu'")
    # Flip só se o lado nativo do footprint diferir do pedido — footprints
    # nativos B.Cu (ex.: J1_Battery_Negative_Contact) já estão do lado certo;
    # flipar de novo os devolveria a F.Cu (bug de duplo-flip).
    if side != fp.GetLayer():
        fp.Flip(_vec(x_mm, y_mm), False)
    if ref is not None:
        fp.SetReference(ref)
    if value is not None:
        fp.SetValue(value)
    return fp


def assign_pad_net(fp: "pcbnew.FOOTPRINT", pad_number: str, board: "pcbnew.BOARD", net_name: str) -> None:
    """Bind a numbered pad of a footprint to a named net."""
    pad = fp.FindPadByNumber(str(pad_number))
    if pad is None:
        raise BoardBuilderError(f"pad {pad_number!r} not found on {fp.GetReference()}")
    pad.SetNetCode(get_or_create_net(board, net_name).GetNetCode())


def pad_position_mm(fp: "pcbnew.FOOTPRINT", pad_number: str) -> tuple[float, float]:
    """Absolute pad centre in mm — use it as track endpoint."""
    pad = fp.FindPadByNumber(str(pad_number))
    if pad is None:
        raise BoardBuilderError(f"pad {pad_number!r} not found on {fp.GetReference()}")
    pos = pad.GetPosition()
    return _mm(pos.x), _mm(pos.y)


# ---------------------------------------------------------------------------
# Copper: tracks and vias
# ---------------------------------------------------------------------------

def add_track(
    board: "pcbnew.BOARD",
    net_name: str,
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    *,
    layer="F.Cu",
    width_mm: float = DEFAULT_TRACK_WIDTH_MM,
) -> "pcbnew.PCB_TRACK":
    """Add one straight copper segment on `layer` with the given net."""
    track = pcbnew.PCB_TRACK(board)
    track.SetStart(_vec(x1_mm, y1_mm))
    track.SetEnd(_vec(x2_mm, y2_mm))
    track.SetWidth(_nm(width_mm))
    track.SetLayer(_layer_id(layer))
    track.SetNetCode(get_or_create_net(board, net_name).GetNetCode())
    board.Add(track)
    return track


def add_route(
    board: "pcbnew.BOARD",
    net_name: str,
    points_mm,
    *,
    layer="F.Cu",
    width_mm: float = DEFAULT_TRACK_WIDTH_MM,
):
    """Route a polyline (list of (x, y) mm tuples) as consecutive tracks."""
    if len(points_mm) < 2:
        raise BoardBuilderError("add_route needs at least 2 points")
    tracks = []
    for (x1, y1), (x2, y2) in zip(points_mm, points_mm[1:]):
        tracks.append(
            add_track(board, net_name, x1, y1, x2, y2, layer=layer, width_mm=width_mm)
        )
    return tracks


def add_via(
    board: "pcbnew.BOARD",
    net_name: str,
    x_mm: float,
    y_mm: float,
    *,
    drill_mm: float = DEFAULT_VIA_DRILL_MM,
    diameter_mm: float = DEFAULT_VIA_DIAMETER_MM,
    layer_top="F.Cu",
    layer_bottom="B.Cu",
) -> "pcbnew.PCB_VIA":
    """Add a via at (x, y) spanning an arbitrary copper layer pair.

    Defaults to a through via (F.Cu <-> B.Cu) — the pre-4L behaviour.
    Blind/buried pairs pick the matching type automatically:
    - F.Cu <-> B.Cu -> VIATYPE_THROUGH (e.g. F.Cu->B.Cu)
    - one side outer (F.Cu/B.Cu), other inner -> VIATYPE_BLIND
      (e.g. F.Cu->In1.Cu, F.Cu->In2.Cu)
    - both sides inner -> VIATYPE_BURIED (e.g. In1.Cu->In2.Cu)
    """
    top_id = _layer_id(layer_top)
    bot_id = _layer_id(layer_bottom)
    if top_id == bot_id:
        raise BoardBuilderError(
            f"via layer pair must span two different layers, got {layer_top!r} -> {layer_bottom!r}"
        )
    outer = {pcbnew.F_Cu, pcbnew.B_Cu}
    if {top_id, bot_id} == outer:
        via_type = pcbnew.VIATYPE_THROUGH
    elif top_id in outer or bot_id in outer:
        via_type = pcbnew.VIATYPE_BLIND
    else:
        via_type = pcbnew.VIATYPE_BURIED
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(_vec(x_mm, y_mm))
    via.SetViaType(via_type)
    via.SetDrill(_nm(drill_mm))
    via.SetWidth(_nm(diameter_mm))
    via.SetLayerPair(top_id, bot_id)
    via.SetNetCode(get_or_create_net(board, net_name).GetNetCode())
    board.Add(via)
    return via


# ---------------------------------------------------------------------------
# Zones
# ---------------------------------------------------------------------------

def add_zone(
    board: "pcbnew.BOARD",
    net_name: str,
    points_mm,
    *,
    layer="B.Cu",
    priority: int = DEFAULT_ZONE_PRIORITY,
) -> "pcbnew.ZONE":
    """Add an unfilled copper zone polygon (list of (x, y) mm vertices).

    Call fill_zones(board) afterwards to run ZONE_FILLER.
    """
    if len(points_mm) < 3:
        raise BoardBuilderError("zone outline needs at least 3 vertices")
    zone = pcbnew.ZONE(board)
    zone.SetLayer(_layer_id(layer))
    zone.SetNetCode(get_or_create_net(board, net_name).GetNetCode())
    zone.SetAssignedPriority(int(priority))
    outline = zone.Outline()
    outline.NewOutline()
    for x, y in points_mm:
        outline.Append(_nm(x), _nm(y))
    board.Add(zone)
    return zone


def add_rect_zone(
    board: "pcbnew.BOARD",
    net_name: str,
    x1_mm: float,
    y1_mm: float,
    x2_mm: float,
    y2_mm: float,
    *,
    layer="B.Cu",
    priority: int = DEFAULT_ZONE_PRIORITY,
) -> "pcbnew.ZONE":
    """Rectangular zone convenience wrapper around add_zone."""
    return add_zone(
        board,
        net_name,
        [(x1_mm, y1_mm), (x2_mm, y1_mm), (x2_mm, y2_mm), (x1_mm, y2_mm)],
        layer=layer,
        priority=priority,
    )


def add_plane(
    board: "pcbnew.BOARD",
    net_name: str,
    layer,
    *,
    center_mm: tuple[float, float] = (100.0, 100.0),
    radius_mm: float = 16.0,
    segments: int = 64,
    priority: int = DEFAULT_ZONE_PRIORITY,
) -> "pcbnew.ZONE":
    """Add a solid copper plane on an inner layer (In1.Cu or In2.Cu).

    The plane is a circle of radius_mm centred on center_mm, approximated
    as a `segments`-gon zone outline (defaults: r=16 at (100, 100)).
    Continuous pour — no keepouts are added. Call fill_zones(board)
    afterwards to run ZONE_FILLER.
    """
    key = layer if isinstance(layer, int) else str(layer)
    if key not in ("In1.Cu", "In2.Cu") and key not in (
        COPPER_LAYERS["In1.Cu"],
        COPPER_LAYERS["In2.Cu"],
    ):
        raise BoardBuilderError(
            f"plane layer must be 'In1.Cu' or 'In2.Cu', got {layer!r}"
        )
    if board.GetCopperLayerCount() < 4:
        raise BoardBuilderError(
            "add_plane needs a 4-layer board (create_board(..., layers=4))"
        )
    cx, cy = float(center_mm[0]), float(center_mm[1])
    points = [
        (
            cx + float(radius_mm) * math.cos(2.0 * math.pi * i / int(segments)),
            cy + float(radius_mm) * math.sin(2.0 * math.pi * i / int(segments)),
        )
        for i in range(int(segments))
    ]
    return add_zone(
        board,
        net_name,
        points,
        layer=layer,
        priority=priority,
    )


def fill_zones(board: "pcbnew.BOARD") -> int:
    """Run ZONE_FILLER over all zones; returns number of zones filled."""
    zones = board.Zones()
    if len(zones) == 0:
        return 0
    filler = pcbnew.ZONE_FILLER(board)
    ok = filler.Fill(zones)
    if not ok:
        raise BoardBuilderError("ZONE_FILLER.Fill returned failure")
    return len(zones)


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_board(board: "pcbnew.BOARD", path) -> Path:
    """Save the board; returns the absolute path written."""
    out = Path(path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    ok = pcbnew.SaveBoard(str(out), board)
    if not ok:
        raise BoardBuilderError(f"SaveBoard returned failure for {out}")
    return out


# ---------------------------------------------------------------------------
# Validation (used by layout workers in phase 2)
# ---------------------------------------------------------------------------

def validate_pads_inside_edges(board: "pcbnew.BOARD") -> list[str]:
    """Return a list of problems: pads outside the Edge.Cuts outline.

    Supports both outlines produced by create_board:
    - rect (4 gr_line segments): pads must fit in the bounding box;
    - circle (gr_circle): pads must fit inside the radius.
    Empty list = clean.
    """
    problems = []
    segments = [
        d for d in board.GetDrawings()
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_SEGMENT
    ]
    circles = [
        d for d in board.GetDrawings()
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetShape() == pcbnew.SHAPE_T_CIRCLE
    ]
    if circles:
        c = circles[0]
        center, radius = c.GetCenter(), c.GetRadius()
        cx, cy, r = _mm(center.x), _mm(center.y), _mm(radius)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                pos = pad.GetPosition()
                x, y = _mm(pos.x), _mm(pos.y)
                pad_r = _mm(pad.GetSizeX()) / 2.0
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if dist + pad_r > r:
                    problems.append(
                        f"pad {fp.GetReference()}.{pad.GetNumber()} at ({x:.3f}, {y:.3f}) mm "
                        f"escapes circle r={r:.3f} mm (dist={dist:.3f}+pad {pad_r:.3f})"
                    )
        return problems

    if not segments:
        return ["no Edge.Cuts segments/circles found — cannot validate"]
    xs, ys = [], []
    for seg in segments:
        s, e = seg.GetStart(), seg.GetEnd()
        xs += [_mm(s.x), _mm(e.x)]
        ys += [_mm(s.y), _mm(e.y)]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)

    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            pos = pad.GetPosition()
            x, y = _mm(pos.x), _mm(pos.y)
            r = _mm(pad.GetSizeX()) / 2.0
            if not (lo_x + r <= x <= hi_x - r and lo_y + r <= y <= hi_y - r):
                problems.append(
                    f"pad {ref}.{pad.GetNumber()} at ({x:.3f}, {y:.3f}) mm outside/on "
                    f"Edge.Cuts rect [{lo_x:.3f}..{hi_x:.3f}, {lo_y:.3f}..{hi_y:.3f}]"
                )
    return problems


def board_summary(board: "pcbnew.BOARD") -> str:
    """One-line human summary (footprints/tracks/vias/zones counts)."""
    return (
        f"footprints={len(board.GetFootprints())} tracks={len(board.GetTracks())} "
        f"zones={len(board.Zones())} "
        f"nets={len([n for n in board.GetNetsByNetcode().values() if n.GetNetCode() > 0])}"
    )


# ---------------------------------------------------------------------------
# Self-test (plan 1.1 acceptance flow)
# ---------------------------------------------------------------------------

def selftest(output_path=None) -> int:
    """Full proof flow: board -> footprints -> nets -> track -> via -> zone+fill
    -> save. Writes a test board and prints PASS/FAIL lines. Exit 0 = pass."""
    print(f"pcbnew build version: {pcbnew.GetBuildVersion()}")

    if output_path is None:
        output_path = Path(__file__).resolve().parent.parent / "_spike" / "board_builder_selftest.kicad_pcb"
    output_path = Path(output_path)

    # 1. Board: 20 x 15 mm rect, 2 layers, 0.8 mm thick
    board = create_board(20.0, 15.0, layers=2, thickness_mm=0.8)
    print(f"PASS create_board rect 20x15mm 2L: {board_summary(board)}")

    # 2. Nets
    get_or_create_net(board, "GND")
    get_or_create_net(board, "SIG")

    # 3. Footprints on real library pads (board origin = centre of the rect)
    r1 = place_footprint(board, "Resistor_SMD:R_0603_1608Metric", -6.0, 0.0, ref="R1", value="10k")
    r2 = place_footprint(board, "Resistor_SMD:R_0603_1608Metric", 6.0, 0.0, ref="R2", value="10k")
    assign_pad_net(r1, "1", board, "SIG")
    assign_pad_net(r1, "2", board, "GND")
    assign_pad_net(r2, "1", board, "SIG")
    assign_pad_net(r2, "2", board, "GND")
    print(f"PASS place_footprint x2 (R_0603_1608Metric): {board_summary(board)}")

    # 4. Track SIG between the two pads, routed ABOVE (y=+4) so it never
    #    crosses the GND pads; endpoints from real pad centres.
    a1 = pad_position_mm(r1, "1")
    a2 = pad_position_mm(r2, "1")
    add_route(board, "SIG", [a1, (a1[0], 4.0), (a2[0], 4.0), a2], layer="F.Cu")

    # 5. GND: one via + spur per part, routed BELOW (y=-5.5); the B.Cu zone
    #    stitches both vias together. No crossings with the SIG corridor.
    b1 = pad_position_mm(r1, "2")
    b2 = pad_position_mm(r2, "2")
    via1 = (b1[0], -5.5)
    via2 = (b2[0], -5.5)
    add_via(board, "GND", via1[0], via1[1])
    add_via(board, "GND", via2[0], via2[1])
    add_route(board, "GND", [b1, via1], layer="F.Cu")
    add_route(board, "GND", [b2, via2], layer="F.Cu")
    print(f"PASS track + route + via: {board_summary(board)}")

    # 6. GND zone on B.Cu + fill
    zone = add_rect_zone(board, "GND", -9.0, -6.5, 9.0, 6.5, layer="B.Cu")
    n_filled = fill_zones(board)
    filled_ok = zone.IsFilled()
    verts = zone.GetFilledPolysList(pcbnew.B_Cu).TotalVertices()
    print(f"PASS zone GND B.Cu added; ZONE_FILLER filled {n_filled} zone(s); "
          f"IsFilled={filled_ok}; filled vertices={verts}")
    if not filled_ok or verts == 0:
        raise BoardBuilderError("zone was not filled (IsFilled=False or empty polygons)")

    # 7. Placement validation
    problems = validate_pads_inside_edges(board)
    if problems:
        for p in problems:
            print(f"FAIL {p}")
        raise BoardBuilderError("placement validation failed")
    print("PASS validate_pads_inside_edges: all pads inside Edge.Cuts")

    # 8. Save
    written = save_board(board, output_path)
    size = written.stat().st_size
    print(f"PASS save_board: {written} ({size} bytes)")
    print(f"SELFTEST OK -> {written}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="KiCad 10 board construction helpers (pcbnew)")
    parser.add_argument("--selftest", action="store_true",
                        help="build a full test board (fp+track+via+filled zone) and save it")
    parser.add_argument("--output", default=None,
                        help="selftest output .kicad_pcb path (default: hardware/kicad/_spike/board_builder_selftest.kicad_pcb)")
    args = parser.parse_args(argv)

    if not args.selftest:
        parser.print_help()
        return 2
    try:
        return selftest(args.output)
    except Exception:
        traceback.print_exc()
        print("SELFTEST FAILED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
