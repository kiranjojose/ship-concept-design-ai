"""Physical constants and unit conversions. All engine internals are SI (m, kg, s, N, W).

Values that appear in the reference report are used where the report states them
(rho_sw = 1.025 t/m3, shell factor 1.006). Others are standard ITTC values.
"""
G = 9.81                    # m/s2, as used in the report (p.16 Froude number)
RHO_SW = 1025.0             # kg/m3, REPORT p.19 / p.33 (1.025 t/m3)
NU_SW_15C = 1.18831e-6      # m2/s, ITTC 7.5-02-01-03 (2011), sea water 15 degC, 35 g/kg
SHELL_FACTOR = 1.006        # REPORT p.33: displacement = moulded volume * rho * 1.006
KNOT = 1852.0 / 3600.0      # m/s per knot


def kn_to_ms(v_kn):
    return v_kn * KNOT


def ms_to_kn(v_ms):
    return v_ms / KNOT
