# =================================================
# main.py # Giriş ve Raporlama
# =================================================
from constant import SLAB_CASES
from design import compute
from models import BarChoice, DesignOut, InputData, ThicknessCheck


def print_choice(prefix: str, c: BarChoice):
    if c.phi <= 0:
        print(f"{prefix}: seçilemedi / gerek yok")
        return
    print(f"{prefix}: Ø{c.phi} / {c.s_cm:.1f} cm  (As={c.As_prov_cm2_per_m:.2f} cm²/m, oran={c.ratio:.3f})")


def print_design(o: DesignOut):
    print(f"\n--- {o.direction} doğrultusu ---")
    print(f"Tip: {o.slab_type} | Senaryo {o.slab_case}: {o.slab_case_name} | m={o.m:.3f}")
    if o.edges_continuity_note:
        print(o.edges_continuity_note)

    print(f"d = {o.d_m:.4f} m (= {o.d_m*1000:.1f} mm)")
    if o.note_min:
        print(f"Min kontrol: {o.note_min}")
    if o.note_spacing:
        print(f"Aralık kısıtı: {o.note_spacing}")

    # Alt (pozitif)
    if o.M_pos_kNm_per_m > 1e-12:
        print("\nAlt donatı (pozitif moment, açıklık ortası):")
        print(f"  a_pos = {o.a_pos_used:.3f}")
        print(f"  M_pos = {o.M_pos_kNm_per_m:.3f} kNm/m")
        print(f"  K_calc (x10^5) = {o.Kcalc_pos_x1e5:.1f} | ks = {o.ks_pos:.3f}")
        print(f"  As_req = {o.As_pos_req_mm2_per_m:.0f} mm²/m ({o.As_pos_req_mm2_per_m/100:.2f} cm²/m)")

        ml = o.main_bottom_layout
        if ml.straight.phi == 0:
            print("  Ana alt donatı seçilemedi (yük çok büyük veya grid dışında).")
        else:
            print("  Ana alt donatı (%50 düz + %50 pilye) [AYNI ÇAP]:")
            print_choice("    Düz", ml.straight)
            print_choice("    Pilye", ml.pilye)
            print(f"    Toplam As_prov = {ml.As_total_prov_mm2_per_m:.0f} mm²/m ({ml.As_total_prov_mm2_per_m/100:.2f} cm²/m) | oran={ml.ratio:.3f}")
    else:
        if o.dist_bars and o.dist_bars.phi > 0:
            print("\nBu doğrultuda pozitif moment yok → dağıtma donatısı:")
            print(f"  As_dist_req = {o.dist_As_req_mm2_per_m:.0f} mm²/m ({o.dist_As_req_mm2_per_m/100:.2f} cm²/m)")
            print_choice("  Dağıtma", o.dist_bars)
        else:
            print("\nBu doğrultuda pozitif moment yok.")

    # Üst (negatif)
    if o.M_neg_kNm_per_m > 1e-12 and o.As_neg_req_mm2_per_m > 1e-12:
        print("\nÜst donatı (negatif moment, sürekli kenar bölgesi):")
        print(f"  a_neg = {o.a_neg_used:.3f}")
        print(f"  M_neg = {o.M_neg_kNm_per_m:.3f} kNm/m")
        print(f"  K_calc (x10^5) = {o.Kcalc_neg_x1e5:.1f} | ks = {o.ks_neg:.3f}")
        print(f"  As_req = {o.As_neg_req_mm2_per_m:.0f} mm²/m ({o.As_neg_req_mm2_per_m/100:.2f} cm²/m)")
        print_choice("  Seçilen üst donatı", o.top_layout)
    else:
        print("\nÜst donatı: negatif moment yok / abakta yok (bu senaryo/kenar süreksizliği için).")


def print_thickness(thk: ThicknessCheck, h_mm: float):
    print("\n--- Kalınlık kontrolü ---")
    print(thk.note)
    if thk.ok:
        print(f"OK: h={h_mm:.1f}mm ≥ h_min={thk.h_min_mm:.1f}mm")
    else:
        print(f"UYARI: h={h_mm:.1f}mm < h_min={thk.h_min_mm:.1f}mm (tasarım devam ediyor ama kalınlık artırılmalı)")

def get_input(msg, cast, default):
    v = input(f"{msg} [{default}]: ").strip()
    return default if v == "" else cast(v)


def main():
    print("\n=== Döşeme (TS500 abak 1..7 + alt/üst donatı + minimum donatı + minimum kalınlık) ===")

    lx = get_input("X kenar uzunluğu (m)", float, 5.0)
    ly = get_input("Y kenar uzunluğu (m)", float, 6.0)
    col = get_input("Kolon kalınlığı (m)", float, 0.50)

    h_mm = get_input("Döşeme kalınlığı (mm)", float, 120.0)
    cover_mm = get_input("Paspayı (mm)", float, 20.0)

    conc = get_input("Beton sınıfı (C25..C50 veya ara: C32)", str, "C30").upper()
    steel = get_input("Çelik sınıfı (S420 / S220 / B500C vb.)", str, "S420").upper()

    w = get_input("Toplam yayılı yük w (kN/m2)", float, 10.0)

    print("\nSenaryolar:")
    for k in range(1, 8):
        print(f"  {k}) {SLAB_CASES[k]['name']}")
    slab_case = get_input("Döşeme mesnet senaryosu (1..7)", int, 7)

    data = InputData(
        lx=lx, ly=ly, col=col, h_mm=h_mm, cover_mm=cover_mm,
        concrete=conc, steel=steel, w=w, slab_case=slab_case
    )

    out_x, out_y, thk = compute(data) # type: ignore

    print("\n" + "=" * 100)
    print(f"Kısa={min(lx, ly):.3f} m, Uzun={max(lx, ly):.3f} m, Kolon={col:.3f} m")
    print(f"m=(uzun+kolon)/(kısa+kolon) = {out_x.m:.3f}  =>  {out_x.slab_type}")
    print(f"Senaryo {slab_case}: {SLAB_CASES.get(slab_case, SLAB_CASES[7])['name']}")
    print("=" * 100)

    print_thickness(thk, h_mm)
    print_design(out_x)
    print_design(out_y)


if __name__ == "__main__":
    main()