# ============================================================
# diagrams.py # Donatı Çizimleri (Reinforcement Sketches)
# ============================================================
"""
Text-based and optional matplotlib diagram generation for slab reinforcement.
Generates:
1. Cross-section diagrams showing reinforcement layout
2. Plan view with bar arrangements
3. Bent bar (pilye) details with dimensions
"""

from typing import Optional
from models import DesignOut, BarChoice, MainRebarLayout


def format_bar_str(c: Optional[BarChoice]) -> str:
    """Format bar choice as readable string"""
    if c is None or c.phi <= 0:
        return "-"
    return f"Ø{c.phi}/{c.s_cm:.0f}cm"


def generate_section_text(
    design: DesignOut,
    h_mm: float,
    cover_mm: float,
    width_cm: float = 100.0
) -> str:
    """
    Generate ASCII text representation of slab cross-section
    showing top and bottom reinforcement
    """
    lines = []
    lines.append(f"╔{'═' * 50}╗")
    lines.append(f"║ DÖŞEME KESİT - {design.direction} DOĞRULTUSU".ljust(50) + "║")
    lines.append(f"╠{'═' * 50}╣")
    
    # Top reinforcement
    top_bar = format_bar_str(design.top_layout)
    lines.append(f"║ Üst Donatı: {top_bar}".ljust(50) + "║")
    lines.append(f"║ {'─' * 48} ║")
    lines.append(f"║   ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  (üst)".ljust(50) + "║")
    lines.append(f"║ ╔{'═' * 46}╗ ║")
    
    # Slab body
    h_scaled = int((h_mm / 20))  # Scale for display
    for i in range(min(h_scaled, 5)):
        if i == h_scaled // 2:
            lines.append(f"║ ║  h = {h_mm:.0f} mm ({h_mm/10:.1f} cm)".ljust(48) + "║ ║")
        else:
            lines.append(f"║ ║".ljust(48) + "║ ║")
    
    lines.append(f"║ ╚{'═' * 46}╝ ║")
    
    # Bottom reinforcement (straight + pilye)
    if design.main_bottom_layout and design.main_bottom_layout.straight.phi > 0:
        straight = format_bar_str(design.main_bottom_layout.straight)
        pilye = format_bar_str(design.main_bottom_layout.pilye)
        lines.append(f"║   ●  ○  ●  ○  ●  ○  ●  ○  ●  ○  (alt)".ljust(50) + "║")
        lines.append(f"║   ● = düz {straight}, ○ = pilye {pilye}".ljust(50) + "║")
    else:
        lines.append(f"║   (Bu doğrultuda ana donatı yok)".ljust(50) + "║")
    
    lines.append(f"║ {'─' * 48} ║")
    lines.append(f"║ Alt Donatı: {format_bar_str(design.main_bottom_layout.straight if design.main_bottom_layout else None)}".ljust(50) + "║")
    lines.append(f"║ Paspayı: {cover_mm:.0f} mm".ljust(50) + "║")
    lines.append(f"╚{'═' * 50}╝")
    
    return "\n".join(lines)


def generate_plan_view_text(
    design_x: DesignOut,
    design_y: DesignOut,
    lx: float,
    ly: float
) -> str:
    """
    Generate ASCII plan view showing X and Y direction reinforcement
    """
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║                    DÖŞEME PLAN GÖRÜNÜMÜ                       ║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    lines.append(f"║ Boyutlar: Lx = {lx:.2f} m, Ly = {ly:.2f} m".ljust(63) + "║")
    lines.append(f"║ Tip: {design_x.slab_type}, m = {design_x.m:.2f}".ljust(63) + "║")
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    
    # X direction info
    if design_x.main_bottom_layout and design_x.main_bottom_layout.straight.phi > 0:
        x_str = format_bar_str(design_x.main_bottom_layout.straight)
        lines.append(f"║ X Doğrultusu (→): Alt {x_str}".ljust(63) + "║")
    else:
        lines.append(f"║ X Doğrultusu: Dağıtma/Yok".ljust(63) + "║")
    
    x_top = format_bar_str(design_x.top_layout)
    lines.append(f"║              Üst {x_top}".ljust(63) + "║")
    
    # Y direction info
    if design_y.main_bottom_layout and design_y.main_bottom_layout.straight.phi > 0:
        y_str = format_bar_str(design_y.main_bottom_layout.straight)
        lines.append(f"║ Y Doğrultusu (↑): Alt {y_str}".ljust(63) + "║")
    else:
        lines.append(f"║ Y Doğrultusu: Dağıtma/Yok".ljust(63) + "║")
    
    y_top = format_bar_str(design_y.top_layout)
    lines.append(f"║              Üst {y_top}".ljust(63) + "║")
    
    lines.append("╠══════════════════════════════════════════════════════════════╣")
    
    # Visual grid
    lines.append("║                                                               ║")
    lines.append("║     ┌─────────────────────────────────────────────────┐      ║")
    lines.append("║     │  ══════════════════════════════════ → X        │      ║")
    lines.append("║     │  ║   ║   ║   ║   ║   ║   ║   ║   ║             │      ║")
    lines.append("║     │  ║   ║   ║   ║   ║   ║   ║   ║   ║   ↑        │      ║")
    lines.append("║     │  ║   ║   ║   ║   ║   ║   ║   ║   ║   Y        │      ║")
    lines.append("║     │  ║   ║   ║   ║   ║   ║   ║   ║   ║             │      ║")
    lines.append("║     │  ══════════════════════════════════             │      ║")
    lines.append("║     └─────────────────────────────────────────────────┘      ║")
    lines.append("║                                                               ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    
    return "\n".join(lines)


def generate_pilye_detail(
    phi: int,
    span_m: float,
    h_mm: float,
    cover_mm: float
) -> str:
    """
    Generate bent bar (pilye) detail with dimensions
    Standard pilye: bent up at L/5 from supports, top level at midspan
    """
    L_cm = span_m * 100
    bend_point = L_cm / 5  # Bend at L/5
    straight_length = L_cm - 2 * bend_point
    bend_angle = 45  # degrees
    
    # Vertical rise
    rise = h_mm - 2 * cover_mm
    
    lines = []
    lines.append("╔═══════════════════════════════════════════════════════╗")
    lines.append(f"║  PİLYE DETAYI - Ø{phi}".ljust(55) + "║")
    lines.append("╠═══════════════════════════════════════════════════════╣")
    lines.append(f"║  Açıklık L = {span_m:.2f} m = {L_cm:.0f} cm".ljust(55) + "║")
    lines.append(f"║  Döşeme h = {h_mm:.0f} mm".ljust(55) + "║")
    lines.append("╠═══════════════════════════════════════════════════════╣")
    lines.append("║                                                       ║")
    lines.append("║         ┌─────────────────────────┐                   ║")
    lines.append("║        /                           \\                  ║")
    lines.append("║       /                             \\                 ║")
    lines.append("║ ─────┘                               └─────           ║")
    lines.append("║                                                       ║")
    lines.append(f"║  ├──L/5──┤←── 3L/5 düz ──→├──L/5──┤".ljust(55) + "║")
    lines.append(f"║  = {bend_point:.0f} cm    = {straight_length:.0f} cm      = {bend_point:.0f} cm".ljust(55) + "║")
    lines.append("║                                                       ║")
    lines.append(f"║  Kıvrım açısı: {bend_angle}°".ljust(55) + "║")
    lines.append(f"║  Yükseklik farkı: h - 2×paspayı = {rise:.0f} mm".ljust(55) + "║")
    lines.append("║                                                       ║")
    lines.append("╚═══════════════════════════════════════════════════════╝")
    
    return "\n".join(lines)


def generate_all_diagrams(
    design_x: DesignOut,
    design_y: DesignOut,
    h_mm: float,
    cover_mm: float,
    lx: float,
    ly: float
) -> str:
    """Generate all diagrams as a combined text output"""
    sections = []
    
    # Plan view
    sections.append(generate_plan_view_text(design_x, design_y, lx, ly))
    sections.append("")
    
    # X section
    sections.append(generate_section_text(design_x, h_mm, cover_mm))
    sections.append("")
    
    # Y section
    sections.append(generate_section_text(design_y, h_mm, cover_mm))
    sections.append("")
    
    # Pilye detail (if used)
    if design_x.main_bottom_layout and design_x.main_bottom_layout.pilye.phi > 0:
        span = max(lx, ly) if design_x.slab_type == "one_way" else lx
        sections.append(generate_pilye_detail(
            design_x.main_bottom_layout.pilye.phi,
            span, h_mm, cover_mm
        ))
    elif design_y.main_bottom_layout and design_y.main_bottom_layout.pilye.phi > 0:
        span = max(lx, ly) if design_y.slab_type == "one_way" else ly
        sections.append(generate_pilye_detail(
            design_y.main_bottom_layout.pilye.phi,
            span, h_mm, cover_mm
        ))
    
    return "\n".join(sections)


def save_diagrams_to_file(
    design_x: DesignOut,
    design_y: DesignOut,
    h_mm: float,
    cover_mm: float,
    lx: float,
    ly: float,
    output_path: str = "slab_diagrams.txt"
) -> str:
    """Save all diagrams to a text file"""
    diagrams = generate_all_diagrams(design_x, design_y, h_mm, cover_mm, lx, ly)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"DÖŞEME DONATILAMA ÇIZIMLERI\n")
        f.write(f"{'='*60}\n")
        f.write(f"Oluşturulma: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write(f"{'='*60}\n\n")
        f.write(diagrams)
    
    return output_path
