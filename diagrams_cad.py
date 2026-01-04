# ============================================================
# diagrams_cad.py # DXF/CAD Diagram Generation (AutoCAD compatible)
# ============================================================
"""
Creates professional DXF drawings for slab reinforcement.
Style based on Turkish structural engineering conventions.

Uses ezdxf library: pip install ezdxf
"""

import ezdxf
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from typing import Optional
from models import DesignOut, BarChoice


def format_bar_label(c: Optional[BarChoice]) -> str:
    """Format bar as string (e.g., phi8/170)"""
    if c is None or c.phi <= 0:
        return "-"
    spacing_mm = c.s_cm * 10
    return f"phi{c.phi}/{spacing_mm:.0f}"


def create_slab_dxf(
    design_x: DesignOut,
    design_y: DesignOut,
    lx: float,
    ly: float,
    h_mm: float,
    cover_mm: float,
    output_file: str = "slab_reinforcement.dxf"
) -> str:
    """Create a professional reinforcement drawing."""
    
    doc = ezdxf.new("R2010")
    doc.units = units.MM
    
    # Setup layers
    doc.layers.add("OUTLINE", color=7)      # White
    doc.layers.add("BEAM", color=8)         # Gray
    doc.layers.add("REBAR_BOT_X", color=1)  # Red
    doc.layers.add("REBAR_BOT_Y", color=3)  # Green
    doc.layers.add("REBAR_TOP", color=5)    # Blue
    doc.layers.add("DIM", color=2)          # Yellow
    doc.layers.add("LABEL", color=4)        # Cyan
    
    msp = doc.modelspace()
    
    # Dimensions in mm
    lx_mm = lx * 1000
    ly_mm = ly * 1000
    beam_w = 300
    
    # Get bar labels
    x_label = "-"
    if design_x.main_bottom_layout and design_x.main_bottom_layout.straight.phi > 0:
        x_label = format_bar_label(design_x.main_bottom_layout.straight)
    elif design_x.dist_bars and design_x.dist_bars.phi > 0:
        x_label = format_bar_label(design_x.dist_bars)
    
    y_label = "-"
    if design_y.main_bottom_layout and design_y.main_bottom_layout.straight.phi > 0:
        y_label = format_bar_label(design_y.main_bottom_layout.straight)
    elif design_y.dist_bars and design_y.dist_bars.phi > 0:
        y_label = format_bar_label(design_y.dist_bars)
    
    # ===== SLAB OUTLINE =====
    outline = [(0, 0), (lx_mm, 0), (lx_mm, ly_mm), (0, ly_mm), (0, 0)]
    msp.add_lwpolyline(outline, dxfattribs={"layer": "OUTLINE", "lineweight": 70})
    
    # Beam lines
    msp.add_line((0, beam_w), (lx_mm, beam_w), dxfattribs={"layer": "BEAM", "lineweight": 18})
    msp.add_line((0, ly_mm - beam_w), (lx_mm, ly_mm - beam_w), dxfattribs={"layer": "BEAM", "lineweight": 18})
    msp.add_line((beam_w, 0), (beam_w, ly_mm), dxfattribs={"layer": "BEAM", "lineweight": 18})
    msp.add_line((lx_mm - beam_w, 0), (lx_mm - beam_w, ly_mm), dxfattribs={"layer": "BEAM", "lineweight": 18})
    
    # ===== X DIRECTION REBARS (horizontal) =====
    hook = 100
    # Draw 5 rebars distributed evenly
    for i in range(5):
        bar_y = beam_w + 200 + i * (ly_mm - 2*beam_w - 400) / 4
        
        # Main horizontal line
        msp.add_line((beam_w, bar_y), (lx_mm - beam_w, bar_y), 
                     dxfattribs={"layer": "REBAR_BOT_X", "lineweight": 35})
        # Left hook (bent down into beam)
        msp.add_line((beam_w, bar_y), (beam_w - hook/2, bar_y - hook), 
                     dxfattribs={"layer": "REBAR_BOT_X", "lineweight": 35})
        # Right hook (bent down into beam)
        msp.add_line((lx_mm - beam_w, bar_y), (lx_mm - beam_w + hook/2, bar_y - hook), 
                     dxfattribs={"layer": "REBAR_BOT_X", "lineweight": 35})
    
    # X label - placed outside the slab on the left
    msp.add_text(
        x_label,
        dxfattribs={"layer": "LABEL", "height": 80}
    ).set_placement((-200, ly_mm/2), align=TextEntityAlignment.RIGHT)
    msp.add_text(
        "(alt)",
        dxfattribs={"layer": "LABEL", "height": 50}
    ).set_placement((-200, ly_mm/2 - 100), align=TextEntityAlignment.RIGHT)
    
    # ===== Y DIRECTION REBARS (vertical) =====
    for i in range(5):
        bar_x = beam_w + 200 + i * (lx_mm - 2*beam_w - 400) / 4
        
        # Main vertical line
        msp.add_line((bar_x, beam_w), (bar_x, ly_mm - beam_w), 
                     dxfattribs={"layer": "REBAR_BOT_Y", "lineweight": 35})
        # Bottom hook (bent left into beam)
        msp.add_line((bar_x, beam_w), (bar_x - hook, beam_w - hook/2), 
                     dxfattribs={"layer": "REBAR_BOT_Y", "lineweight": 35})
        # Top hook (bent left into beam)
        msp.add_line((bar_x, ly_mm - beam_w), (bar_x - hook, ly_mm - beam_w + hook/2), 
                     dxfattribs={"layer": "REBAR_BOT_Y", "lineweight": 35})
    
    # Y label - placed outside the slab on the bottom
    msp.add_text(
        y_label,
        dxfattribs={"layer": "LABEL", "height": 80}
    ).set_placement((lx_mm/2, -200), align=TextEntityAlignment.CENTER)
    msp.add_text(
        "(alt)",
        dxfattribs={"layer": "LABEL", "height": 50}
    ).set_placement((lx_mm/2, -300), align=TextEntityAlignment.CENTER)
    
    # ===== DIMENSIONS =====
    # Lx dimension at bottom
    dim_y = -500
    msp.add_line((0, dim_y), (lx_mm, dim_y), dxfattribs={"layer": "DIM"})
    msp.add_line((0, dim_y - 50), (0, dim_y + 50), dxfattribs={"layer": "DIM"})
    msp.add_line((lx_mm, dim_y - 50), (lx_mm, dim_y + 50), dxfattribs={"layer": "DIM"})
    msp.add_text(
        f"Lx = {lx:.2f} m",
        dxfattribs={"layer": "DIM", "height": 60}
    ).set_placement((lx_mm/2, dim_y - 100), align=TextEntityAlignment.CENTER)
    
    # Ly dimension at right
    dim_x = lx_mm + 500
    msp.add_line((dim_x, 0), (dim_x, ly_mm), dxfattribs={"layer": "DIM"})
    msp.add_line((dim_x - 50, 0), (dim_x + 50, 0), dxfattribs={"layer": "DIM"})
    msp.add_line((dim_x - 50, ly_mm), (dim_x + 50, ly_mm), dxfattribs={"layer": "DIM"})
    msp.add_text(
        f"Ly = {ly:.2f} m",
        dxfattribs={"layer": "DIM", "height": 60, "rotation": 90}
    ).set_placement((dim_x + 100, ly_mm/2), align=TextEntityAlignment.CENTER)
    
    # ===== TITLE =====
    msp.add_text(
        "DOSEME DONATI KROKISI",
        dxfattribs={"layer": "OUTLINE", "height": 100}
    ).set_placement((0, ly_mm + 300), align=TextEntityAlignment.LEFT)
    
    info = f"{design_x.slab_type.upper()} | h={h_mm:.0f}mm | X: {x_label} | Y: {y_label}"
    msp.add_text(
        info,
        dxfattribs={"layer": "LABEL", "height": 60}
    ).set_placement((0, ly_mm + 150), align=TextEntityAlignment.LEFT)
    
    doc.saveas(output_file)
    return output_file


def generate_slab_drawing(
    design_x: DesignOut,
    design_y: DesignOut,
    lx: float,
    ly: float,
    h_mm: float,
    cover_mm: float,
    output_file: str = "slab_reinforcement.dxf"
) -> str:
    """Main function to generate slab reinforcement DXF drawing."""
    return create_slab_dxf(
        design_x=design_x,
        design_y=design_y,
        lx=lx,
        ly=ly,
        h_mm=h_mm,
        cover_mm=cover_mm,
        output_file=output_file
    )
