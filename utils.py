# ============================================================
# utils.py # Yardımcı fonksiyonlar
# ============================================================

import math
from typing import Dict, List, Optional, Tuple
from constant import CONC_NODES, K_TABLE_ROWS, M_NODES, PHI_GRID, S_GRID
from models import BarChoice

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def best_spacing_for_phi(
    As_req_mm2_per_m: float,
    phi: int,
    s_max_mm: int,
    s_min_mm: int = 70
) -> Optional[BarChoice]:
    if As_req_mm2_per_m <= 1e-12:
        return BarChoice(phi, 0.0, 0.0, 0.0, 0.0)
    if phi not in PHI_GRID:
        return None

    As_req_cm2 = As_req_mm2_per_m / 100.0
    s_max_cm = s_max_mm / 10.0
    s_min_cm = s_min_mm / 10.0

    pj = PHI_GRID.index(phi)
    best: Optional[BarChoice] = None

    for si, s in enumerate(S_GRID):
        if s < s_min_cm or s > s_max_cm:
            continue
        As_cm2 = AS_GRID[si][pj]
        if As_cm2 + 1e-12 < As_req_cm2:
            continue
        ratio = As_cm2 / As_req_cm2
        cand = BarChoice(phi, s, As_cm2 * 100.0, As_cm2, ratio)
        if best is None or cand.ratio < best.ratio:
            best = cand
    return best

def interp_piecewise(points: Dict[float, float], x: float) -> float:
    xs = sorted(points.keys())
    if x <= xs[0]:
        return points[xs[0]]
    if x >= xs[-1]:
        return points[xs[-1]]
    hi = next(i for i in range(1, len(xs)) if xs[i] >= x)
    lo = hi - 1
    x1, x2 = xs[lo], xs[hi]
    t = (x - x1) / (x2 - x1)
    return lerp(points[x1], points[x2], t)


def parse_concrete(name: str) -> float:
    name = name.strip().upper()
    if not name.startswith("C"):
        raise ValueError("Beton sınıfı C30 gibi olmalı.")
    return float(name[1:])


def steel_group(name: str) -> str:
    s = name.strip().upper()
    return "B500" if "500" in s else "S420"


def rho_min_oneway(steel: str) -> float:
    s = steel.strip().upper()
    if "220" in s:
        return 0.003
    return 0.002  # S420 ve S500/B500 için


def K_row_concrete_value(row: Tuple, fck: float) -> float:
    K_map = {
        25.0: row[1], 30.0: row[2], 35.0: row[3],
        40.0: row[4], 45.0: row[5], 50.0: row[6],
    }
    if fck <= 25.0:
        return K_map[25.0]
    if fck >= 50.0:
        return K_map[50.0]
    hi = next(i for i in range(1, len(CONC_NODES)) if CONC_NODES[i] >= fck)
    lo = hi - 1
    f1, f2 = CONC_NODES[lo], CONC_NODES[hi]
    t = (fck - f1) / (f2 - f1)
    return lerp(K_map[f1], K_map[f2], t)


def ks_from_Kcalc(Kcalc_x1e5: float, fck: float, steel: str) -> float:
    grp = steel_group(steel)
    Kvals = [K_row_concrete_value(r, fck) for r in K_TABLE_ROWS]  # azalan

    if Kcalc_x1e5 >= Kvals[0]:
        r = K_TABLE_ROWS[0]
        return r[7] if grp == "S420" else r[8]
    if Kcalc_x1e5 <= Kvals[-1]:
        r = K_TABLE_ROWS[-1]
        return r[7] if grp == "S420" else r[8]

    i2 = next(i for i in range(1, len(Kvals)) if Kvals[i] <= Kcalc_x1e5)
    i1 = i2 - 1
    K1, K2 = Kvals[i1], Kvals[i2]
    r1, r2 = K_TABLE_ROWS[i1], K_TABLE_ROWS[i2]

    ks1 = r1[7] if grp == "S420" else r1[8]
    ks2 = r2[7] if grp == "S420" else r2[8]

    t = (Kcalc_x1e5 - K1) / (K2 - K1)
    return lerp(ks1, ks2, t)

def as_cm2_per_m(phi_mm: float, s_cm: float) -> float:
    s_mm = s_cm * 10.0
    a_bar = math.pi * (phi_mm**2) / 4.0  # mm²
    as_mm2_per_m = a_bar * 1000.0 / s_mm
    return as_mm2_per_m / 100.0  # cm²/m

def _pts(vals: List[float]) -> Dict[float, float]:
    return {M_NODES[i]: vals[i] for i in range(len(M_NODES))}

def edge_continuity_note_for_case(
    case_id: int, lx: float, ly: float
) -> str:
    """
    Varsayım (geometriye bağlı):
      - Eğer lx < ly ise: kısa kenarlar y=0 & y=ly (uzunluk=lx), uzun kenarlar x=0 & x=lx (uzunluk=ly)
      - Eğer ly <= lx ise: kısa kenarlar x=0 & x=lx (uzunluk=ly), uzun kenarlar y=0 & y=ly (uzunluk=lx)

    Senaryo 2 ve 3 için "hangi kenar(lar)" bilgisini abak vermiyor.
    Bu yüzden burada sadece tipik/varsayılan bir atama yapıyoruz:
      2: bir kenar süreksiz -> uzun kenarlardan birini (top) süreksiz
      3: iki komşu süreksiz -> bir uzun + bir kısa (top + right)
      6: üç kenar süreksiz -> sadece left sürekli (örnek)
    """
    short_is_x = lx <= ly  # kısa açıklık (L_short) x yönünde mi?

    if short_is_x:
        short_edges = ["y=0", "y=ly"]   # uzunluğu lx (kısa kenar)
        long_edges = ["x=0", "x=lx"]    # uzunluğu ly (uzun kenar)
    else:
        short_edges = ["x=0", "x=lx"]
        long_edges = ["y=0", "y=ly"]

    if case_id == 1:
        cont = short_edges + long_edges
        disc: List[str] = []
    elif case_id == 7:
        cont = []
        disc = short_edges + long_edges
    elif case_id == 4:  # iki kısa kenar süreksiz
        disc = short_edges
        cont = long_edges
    elif case_id == 5:  # iki uzun kenar süreksiz
        disc = long_edges
        cont = short_edges
    elif case_id == 2:  # bir kenar süreksiz (varsayım: bir uzun kenar süreksiz)
        disc = [long_edges[1]]
        cont = [e for e in (short_edges + long_edges) if e not in disc]
    elif case_id == 3:  # iki komşu süreksiz (varsayım: bir uzun + bir kısa)
        disc = [long_edges[1], short_edges[1]]
        cont = [e for e in (short_edges + long_edges) if e not in disc]
    elif case_id == 6:  # üç kenar süreksiz (varsayım: sadece long_edges[0] sürekli)
        cont = [long_edges[0]]
        disc = [e for e in (short_edges + long_edges) if e not in cont]
    else:
        cont = []
        disc = []

    cont_s = ", ".join(cont) if cont else "yok"
    disc_s = ", ".join(disc) if disc else "yok"
    return f"Sürekli kenarlar: {cont_s} | Süreksiz kenarlar: {disc_s} (not: 2/3/6 için varsayım)"

AS_GRID = [[as_cm2_per_m(phi, s) for phi in PHI_GRID] for s in S_GRID]
