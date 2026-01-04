# ============================================================
# models.py # Veri modelleri
# ============================================================

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class BarChoice:
    phi: int
    s_cm: float
    As_prov_mm2_per_m: float
    As_prov_cm2_per_m: float
    ratio: float

@dataclass
class MainRebarLayout:
    straight: BarChoice
    pilye: BarChoice
    As_total_prov_mm2_per_m: float
    As_total_req_mm2_per_m: float
    ratio: float

@dataclass
class ThicknessCheck:
    h_min_mm: float
    ok: bool
    note: str

@dataclass
class InputData:
    """Enhanced input data with beam widths and separate loads per TS500/TBDY-2018"""
    # Geometry
    lx: float  # X span length (m)
    ly: float  # Y span length (m)
    
    # Beam widths (mm) - for net span calculation
    beam_w_left_x: float = 250.0   # Left beam width in X direction
    beam_w_right_x: float = 250.0  # Right beam width in X direction
    beam_w_left_y: float = 250.0   # Left beam width in Y direction
    beam_w_right_y: float = 250.0  # Right beam width in Y direction
    
    # Slab properties
    h_mm: float = 120.0       # Slab thickness (mm)
    cover_mm: float = 20.0    # Concrete cover (mm)
    
    # Materials
    concrete: str = "C30"     # Concrete grade (min C25)
    steel: str = "S420"       # Steel grade
    
    # Loads (kN/m²) - separate dead and live per README
    g_additional: float = 1.5  # Additional dead load (coating, plaster, etc.)
    q_live: float = 5.0        # Live load based on occupancy
    
    # Slab case (support conditions)
    slab_case: int = 7  # 1..7 from ABAK tables
    
    # Optional identifier for database storage
    slab_id: Optional[str] = None


@dataclass
class DesignOut:
    direction: str
    slab_type: str
    slab_case: int
    slab_case_name: str
    m: float
    L_short: float
    L_long: float
    
    # Net spans (after beam deductions)
    Lsn_x: float = 0.0
    Lsn_y: float = 0.0

    # Pozitif moment (alt donatı) için
    a_pos_used: float = 0.0
    M_pos_kNm_per_m: float = 0.0
    Kcalc_pos_x1e5: float = 0.0
    ks_pos: float = 0.0
    As_pos_req_mm2_per_m: float = 0.0
    main_bottom_layout: Optional[MainRebarLayout] = None

    # Negatif moment (üst donatı) için
    a_neg_used: float = 0.0
    M_neg_kNm_per_m: float = 0.0
    Kcalc_neg_x1e5: float = 0.0
    ks_neg: float = 0.0
    As_neg_req_mm2_per_m: float = 0.0
    top_layout: Optional[BarChoice] = None

    # Ortak
    d_m: float = 0.0
    note_min: str = ""
    note_spacing: str = ""
    edges_continuity_note: str = ""

    # Tek doğrultuda moment olmayan doğrultu için dağıtma
    dist_As_req_mm2_per_m: float = 0.0
    dist_bars: Optional[BarChoice] = None


@dataclass
class LoadAnalysis:
    """Load analysis results per TS500"""
    g_self_weight: float  # Self-weight: h × 25 kN/m³
    g_additional: float   # Additional dead load (coating, plaster)
    g_total: float        # Total dead load
    q_live: float         # Live load
    pd_factored: float    # Factored load: 1.4g + 1.6q


@dataclass
class SlabDesignResult:
    """Database storage model for slab design results"""
    slab_id: str
    
    # Input summary
    lx_m: float
    ly_m: float
    h_mm: float
    concrete: str
    steel: str
    
    # Load summary
    g_total_kN_m2: float
    q_live_kN_m2: float
    pd_factored_kN_m2: float
    
    # Slab classification
    slab_type: str  # "one_way" or "two_way"
    slab_case: int
    m_ratio: float
    
    # Net spans
    Lsn_x_m: float
    Lsn_y_m: float
    
    # Reinforcement results (string format: "Ø10/130")
    x_bottom_main: str
    x_bottom_pilye: str
    x_top: str
    y_bottom_main: str
    y_bottom_pilye: str
    y_top: str
    
    # Distribution bars (one-way only)
    distribution_bars: str = ""
    
    # Thickness check
    h_min_required_mm: float = 0.0
    thickness_ok: bool = True
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""
