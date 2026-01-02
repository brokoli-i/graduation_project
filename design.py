# ============================================
# design.py # Tasarım ana modülü
# ============================================
from ast import Tuple
from constant import SLAB_CASES
from models import DesignOut, InputData, ThicknessCheck
from core import calc_K_and_As_from_M, choose_distribution_rebar, choose_main_rebar_half_half_same_phi, choose_single_layer_rebar
from utils import edge_continuity_note_for_case, interp_piecewise, parse_concrete, rho_min_oneway

def compute(data: InputData) -> Tuple[DesignOut, DesignOut, ThicknessCheck]:
    L_short = min(data.lx, data.ly)
    L_long = max(data.lx, data.ly)

    # m = (uzun+kolon)/(kısa+kolon)
    m = (L_long + data.col) / (L_short + data.col)
    slab_type = "one_way" if m > 2.0 else "two_way"

    # Kalınlık kontrolü (ayrı)
    if slab_type == "one_way":
        thk = thickness_check_oneway(L_short=L_short, col=data.col, h_mm=data.h_mm)
    else:
        thk = thickness_check_twoway(L_short=L_short, L_long=L_long, col=data.col, h_mm=data.h_mm)

    # d metre
    d_m = max((data.h_mm - data.cover_mm) / 1000.0, 1e-6)
    d_mm = d_m * 1000.0
    b_mm = 1000.0
    fck = parse_concrete(data.concrete)

    s_max_ana = min(1.5 * data.h_mm, 200.0)  # TS500: 1.5h ve 200mm'den küçük olanı
    s_max_dagitma = 250.0                    # TS500: Dağıtma ve uzun doğrultu için max 250mm (veya 300mm)

    # X uzun mu?
    x_is_long = data.lx >= data.ly

    # ========================================================
    # TEK DOĞRULTU
    # ========================================================
    if slab_type == "one_way":
        # Tek doğrultu: basit mesnet varsayımı, sadece uzun doğrultuda moment
        M_long = data.w * (L_long**2) / 8.0

        Mx_pos = M_long if x_is_long else 0.0
        My_pos = 0.0 if x_is_long else M_long

        # Negatif moment alınmıyor (basit mesnet)
        Mx_neg = 0.0
        My_neg = 0.0

        # Ana donatı minimumu: Asmin = rho*b*d
        rho_min = rho_min_oneway(data.steel)
        Asmin_main = rho_min * b_mm * d_mm  # mm²/m

        # Momentten gelen As
        _, _, Asx_M = calc_K_and_As_from_M(Mx_pos, d_m, fck, data.steel)
        _, _, Asy_M = calc_K_and_As_from_M(My_pos, d_m, fck, data.steel)

        # Minimum testi
        note_x = ""
        note_y = ""
        Asx_req = 0.0
        Asy_req = 0.0

        if Mx_pos > 0:
            if Asx_M < Asmin_main:
                note_x = f"Asx(M)={Asx_M:.0f} < Asmin={Asmin_main:.0f} → Asmin alındı"
                Asx_req = Asmin_main
            else:
                note_x = f"Asx(M)={Asx_M:.0f} ≥ Asmin={Asmin_main:.0f}"
                Asx_req = Asx_M

        if My_pos > 0:
            if Asy_M < Asmin_main:
                note_y = f"Asy(M)={Asy_M:.0f} < Asmin={Asmin_main:.0f} → Asmin alındı"
                Asy_req = Asmin_main
            else:
                note_y = f"Asy(M)={Asy_M:.0f} ≥ Asmin={Asmin_main:.0f}"
                Asy_req = Asy_M

        # Aralık limitleri (konservatif)
        s_max_bottom = int(min(1.5 * data.h_mm, 200))
        s_max_top = int(min(2.0 * data.h_mm, 200))  # üst donatı yok ama yine de koyuyoruz

        edges_note = "Tek doğrultu: basit mesnet kabulü (negatif moment/üst donatı yok)."

        out_x = build_design(
            direction="X", slab_type=slab_type,
            slab_case=data.slab_case, slab_case_name=SLAB_CASES.get(data.slab_case, SLAB_CASES[7])["name"],
            m=m, L_short=L_short, L_long=L_long,
            d_m=d_m, fck=fck, steel=data.steel,
            a_pos=0.0, M_pos=Mx_pos, As_pos_req=Asx_req,
            a_neg=0.0, M_neg=Mx_neg, As_neg_req=0.0,
            s_max_bottom_mm=s_max_bottom, s_max_top_mm=s_max_top,
            note_min=note_x, edges_note=edges_note
        )
        out_y = build_design(
            direction="Y", slab_type=slab_type,
            slab_case=data.slab_case, slab_case_name=SLAB_CASES.get(data.slab_case, SLAB_CASES[7])["name"],
            m=m, L_short=L_short, L_long=L_long,
            d_m=d_m, fck=fck, steel=data.steel,
            a_pos=0.0, M_pos=My_pos, As_pos_req=Asy_req,
            a_neg=0.0, M_neg=My_neg, As_neg_req=0.0,
            s_max_bottom_mm=s_max_bottom, s_max_top_mm=s_max_top,
            note_min=note_y, edges_note=edges_note
        )

        # Dağıtma donatısı hesabı:
        As_ana = main.As_pos_req_mm2_per_m
        As_dagitma_min1 = As_ana * 0.20             # Ana donatının %20'si
        As_dagitma_min2 = 0.0012 * b_mm * data.h_mm # Brüt kesit alanının 0.0012'si

        dist.dist_As_req_mm2_per_m = max(As_dagitma_min1, As_dagitma_min2)
        # s_max_dagitma (250-300mm) kullanılarak donatı seçimi yapılır.

        
        # Dağıtma donatısı: As_main/5 ve s<=300mm
        main = out_x if out_x.M_pos_kNm_per_m > 0 else out_y
        dist = out_y if main.direction == "X" else out_x

        dist.dist_As_req_mm2_per_m = main.As_pos_req_mm2_per_m / 5.0
        dist.dist_bars = choose_distribution_rebar(dist.dist_As_req_mm2_per_m)
        dist.note_min = f"Dağıtma: As/5={dist.dist_As_req_mm2_per_m:.0f} mm²/m, s<=300mm"

        return out_x, out_y, thk

    # ========================================================
    # ÇİFT DOĞRULTU
    # ========================================================
    case = SLAB_CASES.get(data.slab_case, SLAB_CASES[7])
    case_name = case["name"]

    # Katsayılar
    aS_pos = interp_piecewise(case["short_pos"], m)
    aS_neg = interp_piecewise(case["short_neg"], m) if case["short_neg"] else 0.0

    aL_pos = float(case["long_pos"])
    aL_neg = float(case["long_neg"])

    base = data.w * (L_short**2)

    # Kısa/uzun doğrultu momentleri (pozitif/negatif)
    M_short_pos = aS_pos * base
    M_short_neg = aS_neg * base
    M_long_pos = aL_pos * base
    M_long_neg = aL_neg * base

    # X/Y yönlerine dağıt (x uzun mu?)
    if x_is_long:
        Mx_pos, My_pos = M_long_pos, M_short_pos
        Mx_neg, My_neg = M_long_neg, M_short_neg
        ax_pos, ay_pos = aL_pos, aS_pos
        ax_neg, ay_neg = aL_neg, aS_neg
    else:
        Mx_pos, My_pos = M_short_pos, M_long_pos
        Mx_neg, My_neg = M_short_neg, M_long_neg
        ax_pos, ay_pos = aS_pos, aL_pos
        ax_neg, ay_neg = aS_neg, aL_neg

    # Momentten gelen As (pozitif)
    _, _, Asx_pos_M = calc_K_and_As_from_M(Mx_pos, d_m, fck, data.steel)
    _, _, Asy_pos_M = calc_K_and_As_from_M(My_pos, d_m, fck, data.steel)

    # 1. Kontrol: Her bir yön kendi içinde tek doğrultulu min (0.002) şartını sağlamalı
    rho_min_tek = rho_min_oneway(data.steel) # 0.002
    Asx_pos_req = max(Asx_pos_M, rho_min_tek * b_mm * d_mm)
    Asy_pos_req = max(Asy_pos_M, rho_min_tek * b_mm * d_mm)

    # 2. Kontrol: Toplam donatı oranı kontrolü (rho_x + rho_y >= 0.0035)
    As_sum = Asx_pos_req + Asy_pos_req
    Asmin_total = 0.0035 * b_mm * d_mm

    if As_sum < Asmin_total:
        scale = Asmin_total / As_sum
        Asx_pos_req *= scale
        Asy_pos_req *= scale
        note_total = f"Toplam As < 0.0035*b*d olduğu için ölçeklendi (x{scale:.2f})"

    # Minimum toplam (alt donatı için): min(Asx+Asy)=0.0035*b*d
    Asmin_total = 0.0035 * b_mm * d_mm
    As_sum = Asx_pos_M + Asy_pos_M

    if As_sum < Asmin_total:
        if As_sum > 1e-12:
            scale = Asmin_total / As_sum
            Asx_pos_req = Asx_pos_M * scale
            Asy_pos_req = Asy_pos_M * scale
            note_total = f"Asx+Asy={As_sum:.0f} < Asmin_total={Asmin_total:.0f} → ölçeklendi (×{scale:.3f})"
        else:
            Asx_pos_req = Asmin_total / 2.0
            Asy_pos_req = Asmin_total / 2.0
            note_total = f"As moment≈0 → Asx=Asy=Asmin_total/2={Asx_pos_req:.0f}"
    else:
        Asx_pos_req = Asx_pos_M
        Asy_pos_req = Asy_pos_M
        note_total = f"Asx+Asy={As_sum:.0f} ≥ Asmin_total={Asmin_total:.0f}"

    # Negatif momentten gelen As (üst donatı) + minimum (konservatif)
    _, _, Asx_neg_M = calc_K_and_As_from_M(Mx_neg, d_m, fck, data.steel)
    _, _, Asy_neg_M = calc_K_and_As_from_M(My_neg, d_m, fck, data.steel)

    # Üst donatı için minimumu konservatif alalım: As_top_min = 0.002*b*d
    As_top_min = 0.002 * b_mm * d_mm

    Asx_neg_req = max(Asx_neg_M, As_top_min) if Mx_neg > 1e-12 else 0.0
    Asy_neg_req = max(Asy_neg_M, As_top_min) if My_neg > 1e-12 else 0.0

    # Aralık limitleri (konservatif)
    s_max_bottom = int(min(2.0 * data.h_mm, 200))
    s_max_top = int(min(2.0 * data.h_mm, 200))

    edges_note = edge_continuity_note_for_case(data.slab_case, data.lx, data.ly)

    out_x = build_design(
        direction="X", slab_type=slab_type,
        slab_case=data.slab_case, slab_case_name=case_name,
        m=m, L_short=L_short, L_long=L_long,
        d_m=d_m, fck=fck, steel=data.steel,
        a_pos=ax_pos, M_pos=Mx_pos, As_pos_req=Asx_pos_req,
        a_neg=ax_neg, M_neg=Mx_neg, As_neg_req=Asx_neg_req,
        s_max_bottom_mm=s_max_bottom, s_max_top_mm=s_max_top,
        note_min=note_total, edges_note=edges_note
    )
    out_y = build_design(
        direction="Y", slab_type=slab_type,
        slab_case=data.slab_case, slab_case_name=case_name,
        m=m, L_short=L_short, L_long=L_long,
        d_m=d_m, fck=fck, steel=data.steel,
        a_pos=ay_pos, M_pos=My_pos, As_pos_req=Asy_pos_req,
        a_neg=ay_neg, M_neg=My_neg, As_neg_req=Asy_neg_req,
        s_max_bottom_mm=s_max_bottom, s_max_top_mm=s_max_top,
        note_min=note_total, edges_note=edges_note
    )
    return out_x, out_y, thk

def thickness_check_oneway(L_short: float, col: float, h_mm: float) -> ThicknessCheck:
    ln = max(L_short, 0.10)
    h_min = max((ln * 1000) / 25.0, 80)
    ok = h_mm >= h_min
    note = f"Tek doğrultu (konservatif): h_min=ln/25, ln={ln:.3f}m → h_min={h_min:.1f}mm"
    return ThicknessCheck(h_min, ok, note)


def thickness_check_twoway(L_short: float, L_long: float, col: float, h_mm: float) -> ThicknessCheck:
    ln_short = max(L_short, 0.10)
    m = max(L_long / L_short, 1.0)
    alpha_s = 0.0
    denom = 15.0 + (20.0 / m) * (1.0 - alpha_s / 4.0)
    h_min = max((ln_short * 1000) / denom, 80)
    ok = h_mm >= h_min
    note = f"Çift doğrultu (konservatif): h_min=ln_short/(15+20/m), ln_short={ln_short:.3f}m, m={m:.3f} → h_min={h_min:.1f}mm"
    return ThicknessCheck(h_min, ok, note)

def build_design(
    direction: str,
    slab_type: str,
    slab_case: int,
    slab_case_name: str,
    m: float,
    L_short: float,
    L_long: float,
    d_m: float,
    fck: float,
    steel: str,
    a_pos: float,
    M_pos: float,
    As_pos_req: float,
    a_neg: float,
    M_neg: float,
    As_neg_req: float,
    s_max_bottom_mm: int,
    s_max_top_mm: int,
    note_min: str,
    edges_note: str
) -> DesignOut:
    # Pozitif
    Kp, ksp, _ = calc_K_and_As_from_M(M_pos, d_m, fck, steel)
    bottom_layout = choose_main_rebar_half_half_same_phi(
        As_req_mm2_per_m=As_pos_req,
        s_max_main_mm=s_max_bottom_mm,
        s_min_main_mm=70,
        phi_min_main=8,
    )

    # Negatif
    Kn, ksn, _ = calc_K_and_As_from_M(M_neg, d_m, fck, steel)
    top_layout = choose_single_layer_rebar(
        As_req_mm2_per_m=As_neg_req,
        s_max_mm=s_max_top_mm,
        s_min_mm=70,
        phi_min=8
    )

    note_spacing = f"Alt s_max={s_max_bottom_mm}mm | Üst s_max={s_max_top_mm}mm"

    return DesignOut(
        direction=direction,
        slab_type=slab_type,
        slab_case=slab_case,
        slab_case_name=slab_case_name,
        m=m,
        L_short=L_short,
        L_long=L_long,
        a_pos_used=a_pos,
        M_pos_kNm_per_m=M_pos,
        Kcalc_pos_x1e5=Kp,
        ks_pos=ksp,
        As_pos_req_mm2_per_m=As_pos_req,
        main_bottom_layout=bottom_layout,
        a_neg_used=a_neg,
        M_neg_kNm_per_m=M_neg,
        Kcalc_neg_x1e5=Kn,
        ks_neg=ksn,
        As_neg_req_mm2_per_m=As_neg_req,
        top_layout=top_layout,
        d_m=d_m,
        note_min=note_min,
        note_spacing=note_spacing,
        edges_continuity_note=edges_note
    )