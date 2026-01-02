# ============================================================
# models.py # Veri modelleri
# ============================================================

from dataclasses import dataclass
from typing import Optional


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
    lx: float
    ly: float
    col: float
    h_mm: float
    cover_mm: float
    concrete: str
    steel: str
    w: float  # kN/m2 toplam yayılı yük
    slab_case: int = 7  # 1..7


@dataclass
class DesignOut:
    direction: str
    slab_type: str
    slab_case: int
    slab_case_name: str
    m: float
    L_short: float
    L_long: float

    # Pozitif moment (alt donatı) için
    a_pos_used: float
    M_pos_kNm_per_m: float
    Kcalc_pos_x1e5: float
    ks_pos: float
    As_pos_req_mm2_per_m: float
    main_bottom_layout: MainRebarLayout

    # Negatif moment (üst donatı) için
    a_neg_used: float
    M_neg_kNm_per_m: float
    Kcalc_neg_x1e5: float
    ks_neg: float
    As_neg_req_mm2_per_m: float
    top_layout: BarChoice

    # Ortak
    d_m: float
    note_min: str = ""
    note_spacing: str = ""
    edges_continuity_note: str = ""

    # Tek doğrultuda moment olmayan doğrultu için dağıtma
    dist_As_req_mm2_per_m: float = 0.0
    dist_bars: Optional[BarChoice] = None

