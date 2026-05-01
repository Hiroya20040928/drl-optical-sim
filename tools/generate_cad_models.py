from __future__ import annotations

from pathlib import Path

import cadquery as cq


ROOT = Path(__file__).resolve().parents[1]
CAD_GENERATED = ROOT / "cad" / "generated"
CAD_ASSEMBLY = ROOT / "cad" / "assembly"


def export_step(shape, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(path))


def xhp70b_approx():
    """Approximate XHP70.2 package envelope from public 7.00 x 7.00 x 4.35 mm data."""
    base = cq.Workplane("XY").box(7.0, 7.0, 0.65).translate((0, 0, 0.325))
    ceramic = cq.Workplane("XY").box(6.6, 6.6, 0.35).translate((0, 0, 0.825))
    phosphor = cq.Workplane("XY").box(5.15, 5.15, 0.16).translate((0, 0, 1.08))

    die = cq.Workplane("XY").box(2.15, 2.15, 0.08)
    dies = cq.Workplane("XY")
    for x in (-1.22, 1.22):
        for y in (-1.22, 1.22):
            dies = dies.union(die.translate((x, y, 1.22)))

    dome_sphere = cq.Workplane("XY").sphere(3.35).translate((0, 0, 1.0))
    lower_cut = cq.Workplane("XY").box(8.0, 8.0, 8.0).translate((0, 0, -4.0))
    dome = dome_sphere.cut(lower_cut)
    height_cut = cq.Workplane("XY").box(8.0, 8.0, 8.0).translate((0, 0, 8.35))
    dome = dome.cut(height_cut)

    cathode_mark = cq.Workplane("XY").box(1.4, 0.18, 0.08).translate((-2.5, 3.25, 1.0))
    return base.union(ceramic).union(phosphor).union(dies).union(dome).union(cathode_mark)


def ledil_c16369_approx():
    """Approximate LEDiL C16369_HB-SQ-W envelope from public mechanical drawing.

    This is not the optical-production CAD. It preserves the public envelope
    dimensions used for lamp packaging: 25 x 25 mm front aperture, 11.06 mm
    height, 25.4 mm adhesive tape, and drawing-visible side bosses/notches.
    """
    flange = cq.Workplane("XY").box(25.0, 25.0, 1.1).translate((0, 0, 0.55))
    flange = flange.edges("|Z").fillet(0.65)

    body = (
        cq.Workplane("XY")
        .workplane(offset=1.1)
        .rect(21.52, 21.52)
        .workplane(offset=9.96)
        .rect(10.76, 10.76)
        .loft(combine=True)
    )
    top_flat = cq.Workplane("XY").box(10.76, 10.76, 0.18).translate((0, 0, 11.15))

    center_window = cq.Workplane("XY").cylinder(0.35, 3.2).translate((0, 0, 1.35))
    locating_boss = cq.Workplane("YZ").circle(1.0).extrude(1.2).translate((12.55, 0, 4.2))
    locating_boss_2 = cq.Workplane("YZ").circle(1.0).extrude(1.2).translate((-13.75, 0, 4.2))

    tape = cq.Workplane("XY").box(25.4, 25.4, 0.15).translate((0, 0, -0.075))
    tape = tape.edges("|Z").fillet(0.7)
    tape_hole = cq.Workplane("XY").box(16.5, 16.5, 0.35).translate((0, 0, -0.075))
    tape = tape.cut(tape_hole)

    notch_cut_top = cq.Workplane("XY").cylinder(2.0, 1.6).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, 12.5, 0.55))
    notch_cut_bottom = cq.Workplane("XY").cylinder(2.0, 1.6).rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -12.5, 0.55))

    lens = flange.union(body).union(top_flat).union(center_window).union(locating_boss).union(locating_boss_2).union(tape)
    return lens.cut(notch_cut_top).cut(notch_cut_bottom)


def drl_2x3_assembly():
    board = cq.Workplane("XY").box(95.0, 67.0, 2.0).translate((0, 0, -1.0))
    led = xhp70b_approx()
    lens = ledil_c16369_approx()

    assembly = board
    for x in (-28.0, 0.0, 28.0):
        for y in (-14.0, 14.0):
            assembly = assembly.union(led.translate((x, y, 0.0)))
            assembly = assembly.union(lens.translate((x, y, 0.0)))
    return assembly


def main() -> None:
    export_step(xhp70b_approx(), CAD_GENERATED / "CREE_XHP70B_00_0000_0D0BN440E_approx.step")
    export_step(ledil_c16369_approx(), CAD_GENERATED / "LEDiL_C16369_HB-SQ-W_approx.step")
    export_step(drl_2x3_assembly(), CAD_ASSEMBLY / "DRL_CREE_XHP70B_LEDiL_C16369_2x3_approx.step")


if __name__ == "__main__":
    main()
