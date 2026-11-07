"""Resultados e zonas auto-calculadas a partir dos tests.

As zonas calculadas aquí son PROVISIONAIS: o adestrador revísaas e confírmaas (ou cámbiaas).
Os factores saen das táboas que Isma xa usa co clube; se el cambia de criterio, cámbiase aquí.
Os ritmos e tempos van sempre en segundos; os vatios e pulsacións, en números enteiros.
"""

# ── Carreira (test de 3000 m) ──
# Sacados da táboa de Isma do test do 30/09/2026: 3000 m en 11:49 → ritmo medio 3′56″/km (236,33 s)
#   1000 3′55″ · 500 1′48″ · 400 1′28″ · 200 43″ (tempos de cada repetición)
#   umbral anaeróbico 4′21″/km · umbral aeróbico 4′54″/km · ritmo suave 5′36″/km
_P = 709 / 3
RUN_FACTORS = {
    "r1000": 235 / _P,
    "r500": 108 / _P,
    "r400": 88 / _P,
    "r200": 43 / _P,
    "uan": 261 / _P,
    "uae": 294 / _P,
    "easy": 336 / _P,
}
RUN_KEYS = [*RUN_FACTORS, "vo2max"]

# ── Natación (test de 200 m) ──
# O ritmo por 100 m do test tómase como Z5 (VO2max). O resto, a mesma distancia en segundos
# ca na táboa de Isma (Z1 1′44″ … Z5 1′31″, Z6 1′29″-1′27″, sprint 50 m 38″, 25 m 17″).
SWIM_OFFSETS = {"z1": 13, "z2": 8, "z3": 5, "z4": 3, "z5": 0}
SWIM_KEYS = ["z1", "z2", "z3", "z4", "z5", "z6", "s50", "s25"]

# ── Bici ──
# 20′ a tope con potenciómetro: FTP = 95 % dos vatios medios; zonas de Coggan en % do FTP
BIKE_POWER_ZONES = {"z1": (None, 0.55), "z2": (0.56, 0.75), "z3": (0.76, 0.90), "z4": (0.91, 1.05),
                    "z5": (1.06, 1.20), "z6": (1.21, None)}
# 20′ a tope con pulsómetro: pulso de limiar ≈ 95 % do pulso medio; zonas de Friel en % do limiar
BIKE_HR_ZONES = {"z1": (None, 0.81), "z2": (0.81, 0.89), "z3": (0.90, 0.93), "z4": (0.94, 0.99),
                 "z5": (1.00, 1.06)}
BIKE_POWER_KEYS = ["ftp", *BIKE_POWER_ZONES]
BIKE_HR_KEYS = ["lthr", *BIKE_HR_ZONES]

ZONE_KEYS = {"run_3000": RUN_KEYS, "swim_200": SWIM_KEYS, "bike_ftp20": BIKE_POWER_KEYS, "bike_hr20": BIKE_HR_KEYS}


def _band(base: float, lo: float | None, hi: float | None) -> list[int | None]:
    return [round(base * lo) if lo else None, round(base * hi) if hi else None]


def run_result(data: dict) -> dict:
    splits = data["splits"]
    total = splits[-1]["total_s"]
    hrs = [s["hr"] for s in splits if s.get("hr")]
    return {"result_seconds": total, "result_value": None,
            "avg_hr": round(sum(hrs) / len(hrs)) if hrs else None}


def run_zones(total_s: int) -> dict:
    pace = total_s / 3
    zones: dict = {k: round(pace * f) for k, f in RUN_FACTORS.items()}
    zones["vo2max"] = None  # Isma pono a man
    return zones


def swim_zones(total_s: int) -> dict:
    p = total_s / 2
    zones: dict = {k: round(p + off) for k, off in SWIM_OFFSETS.items()}
    zones["z6"] = [round(p - 4), round(p - 2)]
    zones["s50"] = round(p * 38 / 91)
    zones["s25"] = round(p * 17 / 91)
    return zones


def bike_power_zones(avg_watts: int) -> dict:
    ftp = round(avg_watts * 0.95)
    return {"ftp": ftp, **{k: _band(ftp, lo, hi) for k, (lo, hi) in BIKE_POWER_ZONES.items()}}


def bike_hr_zones(avg_hr: int) -> dict:
    lthr = round(avg_hr * 0.95)
    return {"lthr": lthr, **{k: _band(lthr, lo, hi) for k, (lo, hi) in BIKE_HR_ZONES.items()}}


def compute(kind: str, data: dict) -> tuple[dict, dict | None]:
    """Devolve (resultados para as columnas, zonas provisionais ou None)."""
    if kind == "run_3000":
        res = run_result(data)
        return res, run_zones(res["result_seconds"])
    if kind == "swim_200":
        return {"result_seconds": data["total_s"], "result_value": None, "avg_hr": data.get("hr")}, \
            swim_zones(data["total_s"])
    if kind == "bike_ftp20":
        return {"result_seconds": 1200, "result_value": data["avg_watts"], "avg_hr": data.get("avg_hr")}, \
            bike_power_zones(data["avg_watts"])
    if kind == "bike_hr20":
        return {"result_seconds": 1200, "result_value": data["avg_hr"], "avg_hr": data["avg_hr"]}, \
            bike_hr_zones(data["avg_hr"])
    # bike_climb: só o tempo, sen zonas
    return {"result_seconds": data["total_s"], "result_value": None, "avg_hr": data.get("avg_hr")}, None
