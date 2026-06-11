


"""Subsystem mass and power estimation utilities """

""" Note : Heavy reliance on AI generated code. Not completely verified - needs work """

import math
from typing import Any, Iterable, Mapping, Optional


__all__ = [
    "FT_PER_M",
    "FT2_PER_M2",
    "FT3_PER_M3",
    "LB_PER_KG",
    "KG_PER_LB",
    "NMI_PER_M",
    "SUBSYSTEM_PHASE_FACTORS",
    "AVIONICS_INSTRUMENTS_PHASE_FACTORS",
    "CONTROL_SURFACE_DEFLECTION_RATES_DEG_S",
    "CONTROL_SURFACE_USAGE_FACTORS",
    "SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG",
    "m_to_ft",
    "m2_to_ft2",
    "m3_to_ft3",
    "kg_to_lb",
    "lb_to_kg",
    "m_to_nmi",
    "fuselage_planform_area_ft2",
    "scaled_total_engines",
    "scaled_wing_engines",
    "scaled_fuselage_engines",
    "scaled_nacelle_diameter_ft",
    "power_from_power_to_weight_ratio_kg",
    "mechanical_linkage_weight_kg",
    "actuator_max_power_w",
    "control_surface_phase_power_w",
    "actuator_mass_from_power_kg",
    "galley_entertainment_furnishing_nominal_power_kw",
    "lights_nominal_power_kw",
    "avionics_instruments_taxi_power_kw",
    "avionics_instruments_nominal_power_kw",
    "ice_protection_nominal_power_kw",
    "electrothermal_deicing_nominal_power_kw",
    "air_conditioning_nominal_power_kw",
    "fuel_system_nominal_power_kw",
    "subsystem_phase_power_kw",
    "avionics_instruments_phase_power_kw",
    "fuel_system_weight_kg",
    "hydraulic_system_weight_kg",
    "electrical_system_weight_kg",
    "avionics_system_weight_kg",
    "auxiliary_power_unit_weight_kg",
    "instruments_system_weight_kg",
    "air_conditioning_system_weight_kg",
    "ice_protection_system_weight_kg",
    "furnishings_weight_kg",
    "galley_entertainment_furnishing_weight_mohan_kg",
    "derive_system_context_from_inputs",
    "estimate_subsystem_power_from_inputs",
    "estimate_subsystem_power_by_phase_from_inputs",
    "estimate_subsystem_weights_from_inputs",
]


# Unit conversions
FT_PER_M = 3.280839895013123
FT2_PER_M2 = FT_PER_M**2
FT3_PER_M3 = FT_PER_M**3
LB_PER_KG = 2.20462262185
KG_PER_LB = 1.0 / LB_PER_KG
NMI_PER_M = 1.0 / 1852.0


def m_to_ft(length_m: float) -> float:
    """Convert length from metres to feet."""
    return float(length_m) * FT_PER_M


def m2_to_ft2(area_m2: float) -> float:
    """Convert area from square metres to square feet."""
    return float(area_m2) * FT2_PER_M2


def m3_to_ft3(volume_m3: float) -> float:
    """Convert volume from cubic metres to cubic feet."""
    return float(volume_m3) * FT3_PER_M3


def kg_to_lb(mass_kg: float) -> float:
    """Convert mass from kilograms to pounds."""
    return float(mass_kg) * LB_PER_KG


def lb_to_kg(mass_lb: float) -> float:
    """Convert mass from pounds to kilograms."""
    return float(mass_lb) * KG_PER_LB


def m_to_nmi(distance_m: float) -> float:
    """Convert distance from metres to nautical miles."""
    return float(distance_m) * NMI_PER_M


# Phase factors and power-to-weight ratios used by the subsystem estimators.
SUBSYSTEM_PHASE_FACTORS = {
    "galley_entertainment_furnishing": {
        "ground": 0.46,
        "taxi": 1.03,
        "takeoff": 1.0,
        "climb": 1.0,
        "cruise": 1.09,
        "descent": 0.72,
        "approach": 0.72,
        "landing": 0.72,
    },
    "lights": {
        "ground": 0.945,
        "taxi": 0.75,
        "takeoff": 1.0,
        "climb": 1.0,
        "cruise": 0.943,
        "descent": 1.19,
        "approach": 1.19,
        "landing": 1.07,
    },
    "ice_protection": {
        "ground": 0.33,
        "taxi": 0.33,
        "takeoff": 0.33,
        "climb": 0.33,
        "cruise": 0.33,
        "descent": 0.5,
        "approach": 0.5,
        "landing": 0.33,
    },
    "air_conditioning": {
        "ground": 1.0,
        "taxi": 1.0,
        "takeoff": 1.06,
        "climb": 1.0,
        "cruise": 1.0,
        "descent": 1.06,
        "approach": 1.06,
        "landing": 0.92,
    },
    "fuel_system": {
        "ground": 0.0,
        "taxi": 0.0,
        "takeoff": 1.0,
        "climb": 1.0,
        "cruise": 0.15,
        "descent": 1.0,
        "approach": 0.33,
        "landing": 1.0,
    },
}


AVIONICS_INSTRUMENTS_PHASE_FACTORS = {
    "ground": 0.25,
    "taxi": 1.0,
    "takeoff": 1.0,
    "climb": 1.0,
    "cruise": 1.0,
    "descent": 1.0,
    "approach": 1.0,
    "landing": 1.0,
}


CONTROL_SURFACE_DEFLECTION_RATES_DEG_S = {
    "roll": 60.0,
    "autobrake": 30.0,
    "high_lift": 10.0,
    "yaw": 40.0,
    "pitch": 60.0,
    "pitch_trim": 0.5,
}


CONTROL_SURFACE_USAGE_FACTORS = {
    "roll": {
        "ground": 0.33,
        "taxi": 0.33,
        "takeoff": 0.0,
        "climb": 1.0,
        "cruise": 1.0,
        "descent": 1.0,
        "approach": 0.33,
        "landing": 0.33,
    },
    "autobrake": {
        "ground": 0.33,
        "taxi": 0.33,
        "takeoff": 0.0,
        "climb": 1.0,
        "cruise": 1.0,
        "descent": 1.0,
        "approach": 0.0,
        "landing": 0.33,
    },
    "high_lift": {
        "ground": 0.0,
        "taxi": 1.0,
        "takeoff": 0.0,
        "climb": 0.0,
        "cruise": 0.0,
        "descent": 1.0,
        "approach": 0.0,
        "landing": 0.0,
    },
    "yaw": {
        "ground": 0.33,
        "taxi": 0.33,
        "takeoff": 0.33,
        "climb": 0.33,
        "cruise": 0.33,
        "descent": 0.5,
        "approach": 0.5,
        "landing": 0.33,
    },
    "pitch": {
        "ground": 0.0,
        "taxi": 0.0,
        "takeoff": 1.0,
        "climb": 1.0,
        "cruise": 0.15,
        "descent": 1.0,
        "approach": 0.33,
        "landing": 1.0,
    },
    "pitch_trim": {
        "ground": 0.0,
        "taxi": 0.0,
        "takeoff": 1.0,
        "climb": 1.0,
        "cruise": 0.15,
        "descent": 1.0,
        "approach": 0.33,
        "landing": 1.0,
    },
}


SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG = {
    "HMA": 0.4,
    "EHSA": 0.2,
    "EHA": 0.2,
    "EMA": 0.4,
    "EDP": 4.6,
    "HMG": 0.46,
    "actuator_power_electronics": 2.0,
    "EMP": 0.4,
    "hydraulic_power_drive": 0.043,
    "electric_motor_power_drive": 0.045,
    "THSA": 0.045,
    "AC_generator": 1.3,
    "DC_generator": 0.5,
    "EBHA": 0.13,
}


# Small internal helpers
def _phase_key(phase: str) -> str:
    normalized = str(phase).strip().lower()
    aliases = {
        "warmup": "ground",
        "warm-up": "ground",
        "land": "landing",
        "take-off": "takeoff",
        "descend": "descent",
    }
    return aliases.get(normalized, normalized)


def _require_positive(name: str, value: float) -> float:
    value = float(value)
    if value <= 0.0:
        raise ValueError(f"{name} must be > 0")
    return value


def _scaled_count(count: float) -> float:
    count = float(count)
    if count <= 4.0:
        return count
    return 4.0 + 2.0 * math.atan((count - 4.0) / 3.0)


def _coalesce(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _as_mapping(obj: Any) -> Mapping[str, Any]:
    if isinstance(obj, Mapping):
        return obj
    return {}


def _phase_entry(mission: Iterable[Mapping[str, Any]], phase_name: str) -> Mapping[str, Any]:
    target = _phase_key(phase_name)
    for entry in mission:
        if _phase_key(entry.get("phase", "")) == target:
            return entry
    return {}


def fuselage_planform_area_ft2(
    fuselage_length_m: float,
    fuselage_width_m: float,
    *,
    n_fuselages: int = 1,
) -> float:
    """Return fuselage planform area in square feet."""
    return float(n_fuselages) * m_to_ft(fuselage_length_m) * m_to_ft(fuselage_width_m)


def scaled_total_engines(n_engines: float) -> float:
    """Return the FLOPS-style scaled total engine count."""
    return _scaled_count(n_engines)


def scaled_wing_engines(n_wing_engines: float) -> float:
    """Return the FLOPS-style scaled wing-mounted engine count."""
    return _scaled_count(n_wing_engines)


def scaled_fuselage_engines(n_fuselage_engines: float) -> float:
    """Return the FLOPS-style scaled fuselage-mounted engine count."""
    return _scaled_count(n_fuselage_engines)


def scaled_nacelle_diameter_ft(engine_diameter_m: float, n_engines: float) -> float:
    """Return the scaled nacelle diameter in feet."""
    diameter_ft = m_to_ft(engine_diameter_m)
    n_engines = float(n_engines)
    if n_engines <= 4.0:
        return diameter_ft
    return diameter_ft * math.sqrt(n_engines / 2.0)


def power_from_power_to_weight_ratio_kg(
    power_kw: float,
    power_to_weight_kw_per_kg: float,
) -> float:
    """Convert a power requirement into installed mass using a power-to-weight ratio."""
    power_kw = float(power_kw)
    power_to_weight_kw_per_kg = _require_positive(
        "power_to_weight_kw_per_kg", power_to_weight_kw_per_kg
    )
    if power_kw < 0.0:
        raise ValueError("power_kw must be >= 0")
    return power_kw / power_to_weight_kw_per_kg


# Flight-control helpers
_MECHANICAL_LINKAGE_COEFFICIENTS = {
    # Coefficients from Mohan (2023), Table 3-3, with S_cs in m^2 and mass in kg.
    "roll": (14445.0, -247.0),
    "yaw": (13814.0, -12708.0),
    "pitch": (9112.9, -12098.0),
}


def mechanical_linkage_weight_kg(
    control_function: str,
    control_surface_area_m2: float,
    *,
    signaling_only: bool = False,
    signaling_weight_reduction_fraction: float = 0.12,
) -> float:
    """Estimate mechanical linkage mass for one control surface."""
    key = str(control_function).strip().lower()
    if key not in _MECHANICAL_LINKAGE_COEFFICIENTS:
        raise ValueError("control_function must be one of: roll, yaw, pitch")

    control_surface_area_m2 = _require_positive(
        "control_surface_area_m2", control_surface_area_m2
    )
    scale, offset = _MECHANICAL_LINKAGE_COEFFICIENTS[key]
    inner = scale * control_surface_area_m2 + offset
    if inner <= 0.0:
        raise ValueError(
            "control_surface_area_m2 is outside the positive range of the linkage fit"
        )

    weight_kg = 0.0256 * (inner**0.67)
    if signaling_only:
        if not (0.0 <= signaling_weight_reduction_fraction < 1.0):
            raise ValueError("signaling_weight_reduction_fraction must be in [0, 1)")
        weight_kg *= 1.0 - signaling_weight_reduction_fraction
    return weight_kg


def actuator_max_power_w(
    hinge_moment_nm: float,
    deflection_rate_deg_s: float,
    *,
    actuator_correction_factor: float = 1.0,
) -> float:
    """Return peak actuator power from hinge moment and deflection rate."""
    hinge_moment_nm = _require_positive("hinge_moment_nm", hinge_moment_nm)
    deflection_rate_deg_s = _require_positive(
        "deflection_rate_deg_s", deflection_rate_deg_s
    )
    actuator_correction_factor = _require_positive(
        "actuator_correction_factor", actuator_correction_factor
    )
    deflection_rate_rad_s = math.radians(deflection_rate_deg_s)
    return hinge_moment_nm * deflection_rate_rad_s * actuator_correction_factor


def control_surface_phase_power_w(
    hinge_moment_nm: float,
    control_surface_role: str,
    phase: str,
    *,
    actuator_correction_factor: float = 1.0,
) -> float:
    """Estimate control-surface actuator power for a given mission phase."""
    role = str(control_surface_role).strip().lower()
    if role not in CONTROL_SURFACE_DEFLECTION_RATES_DEG_S:
        raise ValueError(
            "control_surface_role must be one of: "
            + ", ".join(sorted(CONTROL_SURFACE_DEFLECTION_RATES_DEG_S))
        )

    phase_key = _phase_key(phase)
    if phase_key not in CONTROL_SURFACE_USAGE_FACTORS[role]:
        raise ValueError(
            f"Unsupported phase '{phase}'. "
            "Use one of: ground, taxi, takeoff, climb, cruise, descent, approach, landing"
        )

    max_power_w = actuator_max_power_w(
        hinge_moment_nm,
        CONTROL_SURFACE_DEFLECTION_RATES_DEG_S[role],
        actuator_correction_factor=actuator_correction_factor,
    )
    return max_power_w * CONTROL_SURFACE_USAGE_FACTORS[role][phase_key]


def actuator_mass_from_power_kg(
    power_w: float,
    actuator_type: str,
    *,
    include_power_electronics: bool = False,
    misc_mass_fraction: float = 0.0,
) -> float:
    """Estimate installed actuator mass from rated power."""
    if power_w < 0.0:
        raise ValueError("power_w must be >= 0")
    key = str(actuator_type).strip()
    if key not in SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG:
        raise ValueError(
            "Unknown actuator_type. Use one of: "
            + ", ".join(sorted(SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG))
        )
    if misc_mass_fraction < 0.0:
        raise ValueError("misc_mass_fraction must be >= 0")

    power_kw = float(power_w) / 1000.0
    mass_kg = power_from_power_to_weight_ratio_kg(
        power_kw, SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG[key]
    )

    if include_power_electronics:
        mass_kg += power_from_power_to_weight_ratio_kg(
            power_kw, SUBSYSTEM_POWER_TO_WEIGHT_KW_PER_KG["actuator_power_electronics"]
        )

    return mass_kg * (1.0 + misc_mass_fraction)


# Subsystem power-demand equations
def galley_entertainment_furnishing_nominal_power_kw(
    fuselage_length_m: float,
    fuselage_width_m: float,
    n_engines: int,
) -> float:
    """Estimate nominal galley, entertainment, and furnishing electrical power."""
    fuselage_length_m = _require_positive("fuselage_length_m", fuselage_length_m)
    fuselage_width_m = _require_positive("fuselage_width_m", fuselage_width_m)
    n_engines = _require_positive("n_engines", n_engines)
    return 10.284 * math.exp(0.0139 * (fuselage_length_m * fuselage_width_m / n_engines))


def lights_nominal_power_kw(fuselage_length_m: float) -> float:
    """Estimate nominal lighting power from fuselage length."""
    fuselage_length_m = _require_positive("fuselage_length_m", fuselage_length_m)
    return 0.31 * fuselage_length_m


def avionics_instruments_taxi_power_kw(fuselage_length_m: float) -> float:
    """Estimate avionics and instruments power during taxi."""
    fuselage_length_m = _require_positive("fuselage_length_m", fuselage_length_m)
    return 0.612 * math.exp(0.048 * fuselage_length_m)


def avionics_instruments_nominal_power_kw(fuselage_length_m: float) -> float:
    """Estimate nominal in-flight avionics and instruments power."""
    fuselage_length_m = _require_positive("fuselage_length_m", fuselage_length_m)
    return 0.02 * (fuselage_length_m**1.55)


def ice_protection_nominal_power_kw(wing_area_m2: float) -> float:
    """Estimate nominal ice-protection electrical power."""
    wing_area_m2 = _require_positive("wing_area_m2", wing_area_m2)
    return 0.035 * wing_area_m2 + 2.02


def electrothermal_deicing_nominal_power_kw(
    anti_icing_nominal_power_kw: float,
    *,
    fraction_of_anti_ice: float = 0.05,
) -> float:
    """Estimate electrothermal de-icing power as a fraction of anti-ice power."""
    anti_icing_nominal_power_kw = _require_positive(
        "anti_icing_nominal_power_kw", anti_icing_nominal_power_kw
    )
    if fraction_of_anti_ice < 0.0:
        raise ValueError("fraction_of_anti_ice must be >= 0")
    return anti_icing_nominal_power_kw * fraction_of_anti_ice


def air_conditioning_nominal_power_kw(cabin_volume_m3: float) -> float:
    """Estimate nominal air-conditioning electrical power."""
    cabin_volume_m3 = _require_positive("cabin_volume_m3", cabin_volume_m3)
    return 0.077 * cabin_volume_m3 - 0.40


def fuel_system_nominal_power_kw(fuselage_length_m: float) -> float:
    """Estimate nominal fuel-system electrical power from fuselage length."""
    fuselage_length_m = _require_positive("fuselage_length_m", fuselage_length_m)
    return 2.88 * math.exp(0.0399 * fuselage_length_m)


def subsystem_phase_power_kw(
    subsystem_name: str,
    nominal_power_kw: float,
    phase: str,
) -> float:
    """Apply a mission-phase factor to a subsystem nominal power level."""
    subsystem_key = str(subsystem_name).strip().lower()
    phase_key = _phase_key(phase)
    if subsystem_key not in SUBSYSTEM_PHASE_FACTORS:
        raise ValueError(
            "Unsupported subsystem_name. Use one of: "
            + ", ".join(sorted(SUBSYSTEM_PHASE_FACTORS))
        )
    if phase_key not in SUBSYSTEM_PHASE_FACTORS[subsystem_key]:
        raise ValueError(
            f"Unsupported phase '{phase}'. "
            "Use one of: ground, taxi, takeoff, climb, cruise, descent, approach, landing"
        )
    nominal_power_kw = _require_positive("nominal_power_kw", nominal_power_kw)
    return nominal_power_kw * SUBSYSTEM_PHASE_FACTORS[subsystem_key][phase_key]


def avionics_instruments_phase_power_kw(
    fuselage_length_m: float,
    phase: str,
) -> float:
    """Estimate avionics and instruments power in a specific mission phase."""
    phase_key = _phase_key(phase)
    if phase_key not in AVIONICS_INSTRUMENTS_PHASE_FACTORS:
        raise ValueError(
            f"Unsupported phase '{phase}'. "
            "Use one of: ground, taxi, takeoff, climb, cruise, descent, approach, landing"
        )

    if phase_key in ("ground", "taxi"):
        base_kw = avionics_instruments_taxi_power_kw(fuselage_length_m)
    else:
        base_kw = avionics_instruments_nominal_power_kw(fuselage_length_m)

    return base_kw * AVIONICS_INSTRUMENTS_PHASE_FACTORS[phase_key]


# FLOPS-based subsystem weight equations
def fuel_system_weight_kg(
    max_fuel_capacity_kg: float,
    n_engines: int,
    *,
    v_max_mach: Optional[float] = None,
    n_tanks: Optional[int] = None,
    aircraft_class: str = "transport",
) -> float:
    """Estimate installed fuel-system mass."""
    max_fuel_capacity_lb = kg_to_lb(_require_positive("max_fuel_capacity_kg", max_fuel_capacity_kg))
    fneng = scaled_total_engines(_require_positive("n_engines", n_engines))
    aircraft_class = str(aircraft_class).strip().lower()

    if aircraft_class == "transport":
        v_max_mach = _require_positive("v_max_mach", v_max_mach)
        weight_lb = 1.07 * (max_fuel_capacity_lb**0.58) * (fneng**0.43) * (v_max_mach**0.34)
    elif aircraft_class == "general_aviation":
        weight_lb = 1.07 * (max_fuel_capacity_lb**0.58) * (fneng**0.43)
    elif aircraft_class == "fighter_attack":
        if n_tanks is None:
            raise ValueError("n_tanks is required for fighter_attack fuel-system weight")
        weight_lb = 36.0 * (max_fuel_capacity_lb**0.2) * (float(n_tanks) ** 0.5) * (fneng**0.4)
    else:
        raise ValueError(
            "aircraft_class must be one of: transport, general_aviation, fighter_attack"
        )

    return lb_to_kg(weight_lb)


def hydraulic_system_weight_kg(
    fuselage_length_m: float,
    fuselage_width_m: float,
    wing_area_m2: float,
    v_max_mach: float,
    *,
    n_wing_engines: int = 0,
    n_fuselage_engines: int = 0,
    n_fuselages: int = 1,
    hydraulic_pressure_psi: float = 3000.0,
    variable_sweep_factor: float = 0.0,
) -> float:
    """Estimate hydraulic system mass using the FLOPS transport-aircraft relation."""
    fparea_ft2 = fuselage_planform_area_ft2(
        fuselage_length_m, fuselage_width_m, n_fuselages=n_fuselages
    )
    sw_ft2 = m2_to_ft2(_require_positive("wing_area_m2", wing_area_m2))
    fnew = scaled_wing_engines(max(0, n_wing_engines))
    fnef = scaled_fuselage_engines(max(0, n_fuselage_engines))
    hydraulic_pressure_psi = _require_positive(
        "hydraulic_pressure_psi", hydraulic_pressure_psi
    )
    v_max_mach = _require_positive("v_max_mach", v_max_mach)
    if variable_sweep_factor < 0.0:
        raise ValueError("variable_sweep_factor must be >= 0")

    weight_lb = (
        0.57
        * (fparea_ft2 + 0.27 * sw_ft2)
        * (1.0 + 0.03 * fnew + 0.05 * fnef)
        * ((3000.0 / hydraulic_pressure_psi) ** 0.35)
        * (1.0 + 0.04 * variable_sweep_factor)
        * (v_max_mach**0.33)
    )
    return lb_to_kg(weight_lb)


def electrical_system_weight_kg(
    fuselage_length_m: float,
    fuselage_width_m: float,
    n_engines: int,
    n_passengers: int,
    n_flight_crew: int,
    *,
    n_fuselages: int = 1,
) -> float:
    """Estimate installed electrical system mass."""
    xl_ft = m_to_ft(_require_positive("fuselage_length_m", fuselage_length_m))
    wf_ft = m_to_ft(_require_positive("fuselage_width_m", fuselage_width_m))
    fneng = scaled_total_engines(_require_positive("n_engines", n_engines))
    if n_passengers < 0 or n_flight_crew < 0 or n_fuselages < 1:
        raise ValueError("passenger, crew, and fuselage counts must be non-negative")

    weight_lb = (
        92.0
        * (xl_ft**0.4)
        * (wf_ft**0.14)
        * (float(n_fuselages) ** 0.27)
        * (fneng**0.69)
        * (1.0 + 0.044 * float(n_flight_crew) + 0.0015 * float(n_passengers))
    )
    return lb_to_kg(weight_lb)


def avionics_system_weight_kg(
    design_range_m: float,
    n_flight_crew: int,
    fuselage_length_m: float,
    fuselage_width_m: float,
    *,
    n_fuselages: int = 1,
) -> float:
    """Estimate avionics system mass."""
    design_range_nmi = m_to_nmi(_require_positive("design_range_m", design_range_m))
    if n_flight_crew < 0 or n_fuselages < 1:
        raise ValueError("n_flight_crew must be >= 0 and n_fuselages >= 1")
    fparea_ft2 = fuselage_planform_area_ft2(
        fuselage_length_m, fuselage_width_m, n_fuselages=n_fuselages
    )

    weight_lb = (
        15.8
        * (design_range_nmi**0.1)
        * (float(n_flight_crew) ** 0.7)
        * (fparea_ft2**0.43)
    )
    return lb_to_kg(weight_lb)


def auxiliary_power_unit_weight_kg(
    fuselage_length_m: float,
    fuselage_width_m: float,
    n_passengers: int,
    *,
    n_fuselages: int = 1,
) -> float:
    """Estimate auxiliary power unit mass."""
    if n_passengers < 0 or n_fuselages < 1:
        raise ValueError("n_passengers must be >= 0 and n_fuselages >= 1")
    fparea_ft2 = fuselage_planform_area_ft2(
        fuselage_length_m, fuselage_width_m, n_fuselages=n_fuselages
    )
    weight_lb = 54.0 * (fparea_ft2**0.3) + 5.4 * (float(n_passengers) ** 0.9)
    return lb_to_kg(weight_lb)


def instruments_system_weight_kg(
    fuselage_length_m: float,
    fuselage_width_m: float,
    v_max_mach: float,
    n_flight_crew: int,
    *,
    n_wing_engines: int = 0,
    n_fuselage_engines: int = 0,
    n_fuselages: int = 1,
) -> float:
    """Estimate instruments system mass."""
    if n_flight_crew < 0 or n_fuselages < 1:
        raise ValueError("n_flight_crew must be >= 0 and n_fuselages >= 1")
    v_max_mach = _require_positive("v_max_mach", v_max_mach)
    fparea_ft2 = fuselage_planform_area_ft2(
        fuselage_length_m, fuselage_width_m, n_fuselages=n_fuselages
    )
    fnew = scaled_wing_engines(max(0, n_wing_engines))
    fnef = scaled_fuselage_engines(max(0, n_fuselage_engines))

    weight_lb = (
        0.48
        * (fparea_ft2**0.57)
        * (v_max_mach**0.5)
        * (10.0 + 2.5 * float(n_flight_crew) + fnew + 1.5 * fnef)
    )
    return lb_to_kg(weight_lb)


def air_conditioning_system_weight_kg(
    fuselage_length_m: float,
    fuselage_width_m: float,
    fuselage_depth_m: float,
    n_passengers: int,
    v_max_mach: float,
    avionics_weight_kg: float,
    *,
    n_fuselages: int = 1,
) -> float:
    """Estimate air-conditioning system mass."""
    if n_passengers < 0 or n_fuselages < 1:
        raise ValueError("n_passengers must be >= 0 and n_fuselages >= 1")
    v_max_mach = _require_positive("v_max_mach", v_max_mach)
    avionics_weight_lb = kg_to_lb(_require_positive("avionics_weight_kg", avionics_weight_kg))
    fparea_ft2 = fuselage_planform_area_ft2(
        fuselage_length_m, fuselage_width_m, n_fuselages=n_fuselages
    )
    df_ft = m_to_ft(_require_positive("fuselage_depth_m", fuselage_depth_m))

    weight_lb = (
        (3.2 * ((fparea_ft2 * df_ft) ** 0.6) + 9.0 * (float(n_passengers) ** 0.83))
        * v_max_mach
        + 0.075 * avionics_weight_lb
    )
    return lb_to_kg(weight_lb)


def ice_protection_system_weight_kg(
    wing_span_m: float,
    wing_sweep_quarter_chord_deg: float,
    n_engines: int,
    engine_diameter_m: float,
    fuselage_width_m: float,
) -> float:
    """Estimate ice-protection system mass."""
    wing_span_ft = m_to_ft(_require_positive("wing_span_m", wing_span_m))
    fuselage_width_ft = m_to_ft(_require_positive("fuselage_width_m", fuselage_width_m))
    fneng = scaled_total_engines(_require_positive("n_engines", n_engines))
    fnac = scaled_nacelle_diameter_ft(
        _require_positive("engine_diameter_m", engine_diameter_m),
        n_engines,
    )

    sweep_rad = math.radians(float(wing_sweep_quarter_chord_deg))
    cos_sweep = math.cos(sweep_rad)
    if cos_sweep <= 0.0:
        raise ValueError("wing_sweep_quarter_chord_deg results in a non-positive cosine")

    weight_lb = wing_span_ft / cos_sweep + 3.8 * fnac * fneng + 1.5 * fuselage_width_ft
    return lb_to_kg(weight_lb)


def furnishings_weight_kg(
    n_flight_crew: int,
    passenger_compartment_length_m: float,
    fuselage_width_m: float,
    fuselage_depth_m: float,
    *,
    n_first_class_passengers: int = 0,
    n_business_class_passengers: int = 0,
    n_tourist_class_passengers: int = 0,
    n_fuselages: int = 1,
) -> float:
    """Estimate furnishings mass with the FLOPS transport-aircraft relation."""
    if min(
        n_flight_crew,
        n_first_class_passengers,
        n_business_class_passengers,
        n_tourist_class_passengers,
    ) < 0:
        raise ValueError("crew and passenger counts must be >= 0")
    if n_fuselages < 1:
        raise ValueError("n_fuselages must be >= 1")

    xlp_ft = m_to_ft(_require_positive("passenger_compartment_length_m", passenger_compartment_length_m))
    wf_ft = m_to_ft(_require_positive("fuselage_width_m", fuselage_width_m))
    df_ft = m_to_ft(_require_positive("fuselage_depth_m", fuselage_depth_m))

    weight_lb = (
        127.0 * float(n_flight_crew)
        + 112.0 * float(n_first_class_passengers)
        + 78.0 * float(n_business_class_passengers)
        + 44.0 * float(n_tourist_class_passengers)
        + 2.6 * xlp_ft * (wf_ft + df_ft) * float(n_fuselages)
    )
    return lb_to_kg(weight_lb)


def galley_entertainment_furnishing_weight_mohan_kg(
    n_crew: int,
    n_passengers: int,
    cabin_volume_m3: float,
    *,
    k_gef: Optional[float] = None,
) -> float:
    """Estimate furnishing-related mass with the Mohan correlation."""
    if n_crew < 0 or n_passengers < 0:
        raise ValueError("n_crew and n_passengers must be >= 0")
    cabin_volume_ft3 = m3_to_ft3(_require_positive("cabin_volume_m3", cabin_volume_m3))

    if k_gef is None:
        if n_passengers >= 60:
            k_gef = 9.1
        elif n_passengers >= 10:
            k_gef = 15.2
        else:
            k_gef = 25.3

    return float(k_gef) * ((float(n_crew + n_passengers) ** 1.65) / (cabin_volume_ft3**0.18))


# High-level wrappers for the worked-example dictionary
def derive_system_context_from_inputs(
    inputs: Mapping[str, Any],
    *,
    overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Extract subsystem inputs from the worked-example sizing dictionary."""
    overrides = _as_mapping(overrides)
    systems = _as_mapping(inputs.get("systems"))
    wing = _as_mapping(inputs.get("wing"))
    fuselage = _as_mapping(inputs.get("fuselage"))
    engine = _as_mapping(inputs.get("engine"))
    tail = _as_mapping(inputs.get("tail"))
    mission = inputs.get("mission", [])
    if not isinstance(mission, list):
        mission = []

    assumptions: list[str] = []
    cruise_phase = _phase_entry(mission, "cruise")

    n_passengers = _coalesce(
        overrides.get("n_passengers"),
        systems.get("n_passengers"),
        inputs.get("n_passengers"),
        inputs.get("pax"),
        cruise_phase.get("pax"),
    )
    if n_passengers is not None and n_passengers == cruise_phase.get("pax"):
        assumptions.append("Used mission cruise-phase passenger count for systems sizing.")

    n_flight_crew = _coalesce(
        overrides.get("n_flight_crew"),
        systems.get("n_flight_crew"),
        inputs.get("n_flight_crew"),
        inputs.get("n_crew"),
    )
    if n_flight_crew is None:
        n_flight_crew = 2
        assumptions.append("Defaulted n_flight_crew to 2 because no crew count was present.")

    n_fuselages = _coalesce(
        overrides.get("n_fuselages"),
        systems.get("n_fuselages"),
        inputs.get("n_fuselages"),
        fuselage.get("n_fuselages"),
        1,
    )
    if n_fuselages == 1 and _coalesce(
        overrides.get("n_fuselages"),
        systems.get("n_fuselages"),
        inputs.get("n_fuselages"),
        fuselage.get("n_fuselages"),
    ) is None:
        assumptions.append("Defaulted n_fuselages to 1.")

    design_range_m = _coalesce(
        overrides.get("design_range_m"),
        systems.get("design_range_m"),
        inputs.get("design_range_m"),
        cruise_phase.get("range"),
    )
    if design_range_m is not None and design_range_m == cruise_phase.get("range"):
        assumptions.append("Used cruise-phase range as design_range_m.")

    v_max_mach = _coalesce(
        overrides.get("v_max_mach"),
        systems.get("v_max_mach"),
        inputs.get("v_max_mach"),
        cruise_phase.get("cruise_speed"),
        inputs.get("cruise_speed"),
    )
    if v_max_mach is not None and v_max_mach == cruise_phase.get("cruise_speed"):
        assumptions.append("Used cruise-phase Mach number as v_max_mach.")

    wing_area_m2 = _coalesce(
        overrides.get("wing_area_m2"),
        systems.get("wing_area_m2"),
        wing.get("S_m2"),
        wing.get("S_wing"),
    )
    wing_span_m = _coalesce(
        overrides.get("wing_span_m"),
        systems.get("wing_span_m"),
        wing.get("b_m"),
    )
    wing_sweep_quarter_chord_deg = _coalesce(
        overrides.get("wing_sweep_quarter_chord_deg"),
        systems.get("wing_sweep_quarter_chord_deg"),
        wing.get("sweep_quarter_chord_deg"),
        wing.get("sweep_half_chord_deg"),
    )
    if wing_sweep_quarter_chord_deg is not None and wing.get("sweep_quarter_chord_deg") is None:
        if wing.get("sweep_half_chord_deg") is not None:
            assumptions.append(
                "Approximated wing_sweep_quarter_chord_deg with wing['sweep_half_chord_deg']."
            )

    n_engines = _coalesce(
        overrides.get("n_engines"),
        systems.get("n_engines"),
        inputs.get("n_engines"),
        engine.get("N_engines"),
    )
    n_wing_engines = _coalesce(
        overrides.get("n_wing_engines"),
        systems.get("n_wing_engines"),
        inputs.get("n_wing_engines"),
        wing.get("engines_wing_mounted"),
    )
    n_fuselage_engines = _coalesce(
        overrides.get("n_fuselage_engines"),
        systems.get("n_fuselage_engines"),
        inputs.get("n_fuselage_engines"),
    )
    if n_fuselage_engines is None and n_engines is not None and n_wing_engines is not None:
        n_fuselage_engines = max(0, int(n_engines) - int(n_wing_engines))
        assumptions.append("Derived n_fuselage_engines from total and wing-mounted engine counts.")
    elif n_fuselage_engines is None and n_engines is not None and "fuselage_mounted_engines" in fuselage:
        n_fuselage_engines = int(n_engines) if fuselage.get("fuselage_mounted_engines") else 0
        assumptions.append(
            "Derived n_fuselage_engines from fuselage['fuselage_mounted_engines']."
        )

    engine_diameter_m = _coalesce(
        overrides.get("engine_diameter_m"),
        systems.get("engine_diameter_m"),
        inputs.get("engine_diameter_m"),
        engine.get("diameter_m"),
    )

    fuselage_length_m = _coalesce(
        overrides.get("fuselage_length_m"),
        systems.get("fuselage_length_m"),
        fuselage.get("length_m"),
        fuselage.get("l_f_m"),
        inputs.get("fuselage_length_m"),
    )
    if fuselage_length_m is None:
        required_tail_keys = (
            wing.get("W_G_kg"),
            wing.get("S_m2"),
            wing.get("b_m"),
            wing.get("c_root"),
            wing.get("c_tip"),
            tail.get("c_ht"),
            tail.get("c_vt"),
            tail.get("a_fus"),
            tail.get("c_fus"),
            tail.get("ht_arm_fraction"),
            tail.get("vt_arm_fraction"),
        )
        if all(value is not None for value in required_tail_keys):
            from class_2_airframe_structure import tail_areas_from_volume_coefficients

            tail_out = tail_areas_from_volume_coefficients(
                MTOM_kg=wing["W_G_kg"],
                S_w_m2=wing["S_m2"],
                b_w_m=wing["b_m"],
                c_bar_w_m=0.5 * (wing["c_root"] + wing["c_tip"]),
                c_ht=tail["c_ht"],
                c_vt=tail["c_vt"],
                a_fus=tail["a_fus"],
                c_fus=tail["c_fus"],
                ht_arm_fraction=tail["ht_arm_fraction"],
                vt_arm_fraction=tail["vt_arm_fraction"],
            )
            fuselage_length_m = tail_out["l_f_m"]
            assumptions.append(
                "Derived fuselage_length_m from class_2_airframe_structure.tail_areas_from_volume_coefficients."
            )

    fuselage_width_m = _coalesce(
        overrides.get("fuselage_width_m"),
        systems.get("fuselage_width_m"),
        fuselage.get("width_m"),
        fuselage.get("b_f_m"),
        inputs.get("fuselage_width_m"),
    )
    fuselage_depth_m = _coalesce(
        overrides.get("fuselage_depth_m"),
        systems.get("fuselage_depth_m"),
        fuselage.get("depth_m"),
        fuselage.get("h_f_m"),
        inputs.get("fuselage_depth_m"),
    )
    cabin_volume_m3 = _coalesce(
        overrides.get("cabin_volume_m3"),
        systems.get("cabin_volume_m3"),
        inputs.get("cabin_volume_m3"),
    )
    passenger_compartment_length_m = _coalesce(
        overrides.get("passenger_compartment_length_m"),
        systems.get("passenger_compartment_length_m"),
        inputs.get("passenger_compartment_length_m"),
    )

    hydraulic_pressure_psi = _coalesce(
        overrides.get("hydraulic_pressure_psi"),
        systems.get("hydraulic_pressure_psi"),
        inputs.get("hydraulic_pressure_psi"),
        3000.0,
    )
    if hydraulic_pressure_psi == 3000.0 and _coalesce(
        overrides.get("hydraulic_pressure_psi"),
        systems.get("hydraulic_pressure_psi"),
        inputs.get("hydraulic_pressure_psi"),
    ) is None:
        assumptions.append("Defaulted hydraulic_pressure_psi to 3000.")

    variable_sweep_factor = _coalesce(
        overrides.get("variable_sweep_factor"),
        systems.get("variable_sweep_factor"),
        inputs.get("variable_sweep_factor"),
        0.0,
    )
    if variable_sweep_factor == 0.0 and _coalesce(
        overrides.get("variable_sweep_factor"),
        systems.get("variable_sweep_factor"),
        inputs.get("variable_sweep_factor"),
    ) is None:
        assumptions.append("Defaulted variable_sweep_factor to 0.0.")

    n_first_class_passengers = _coalesce(
        overrides.get("n_first_class_passengers"),
        systems.get("n_first_class_passengers"),
        inputs.get("n_first_class_passengers"),
    )
    n_business_class_passengers = _coalesce(
        overrides.get("n_business_class_passengers"),
        systems.get("n_business_class_passengers"),
        inputs.get("n_business_class_passengers"),
    )
    n_tourist_class_passengers = _coalesce(
        overrides.get("n_tourist_class_passengers"),
        systems.get("n_tourist_class_passengers"),
        inputs.get("n_tourist_class_passengers"),
    )
    if (
        n_passengers is not None
        and n_first_class_passengers is None
        and n_business_class_passengers is None
        and n_tourist_class_passengers is None
    ):
        n_first_class_passengers = 0
        n_business_class_passengers = 0
        n_tourist_class_passengers = int(n_passengers)
        assumptions.append(
            "Allocated all passengers to tourist class for the FLOPS furnishings estimate."
        )

    max_fuel_capacity_kg = _coalesce(
        overrides.get("max_fuel_capacity_kg"),
        systems.get("max_fuel_capacity_kg"),
        inputs.get("max_fuel_capacity_kg"),
        engine.get("max_fuel_capacity_kg"),
        inputs.get("fuel_mass_kg"),
    )
    if max_fuel_capacity_kg is None and engine.get("E_fuel") is not None and inputs.get("e_f") is not None:
        max_fuel_capacity_kg = float(engine["E_fuel"]) / float(inputs["e_f"])
        assumptions.append("Derived max_fuel_capacity_kg from engine['E_fuel'] / inputs['e_f'].")

    return {
        "n_passengers": n_passengers,
        "n_flight_crew": n_flight_crew,
        "n_fuselages": n_fuselages,
        "design_range_m": design_range_m,
        "v_max_mach": v_max_mach,
        "wing_area_m2": wing_area_m2,
        "wing_span_m": wing_span_m,
        "wing_sweep_quarter_chord_deg": wing_sweep_quarter_chord_deg,
        "n_engines": n_engines,
        "n_wing_engines": n_wing_engines,
        "n_fuselage_engines": n_fuselage_engines,
        "engine_diameter_m": engine_diameter_m,
        "fuselage_length_m": fuselage_length_m,
        "fuselage_width_m": fuselage_width_m,
        "fuselage_depth_m": fuselage_depth_m,
        "cabin_volume_m3": cabin_volume_m3,
        "passenger_compartment_length_m": passenger_compartment_length_m,
        "hydraulic_pressure_psi": hydraulic_pressure_psi,
        "variable_sweep_factor": variable_sweep_factor,
        "n_first_class_passengers": n_first_class_passengers,
        "n_business_class_passengers": n_business_class_passengers,
        "n_tourist_class_passengers": n_tourist_class_passengers,
        "max_fuel_capacity_kg": max_fuel_capacity_kg,
        "assumptions": assumptions,
    }


def estimate_subsystem_power_from_inputs(
    inputs: Mapping[str, Any],
    *,
    phase: str = "cruise",
    overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Estimate subsystem power demand for one mission phase."""
    context = derive_system_context_from_inputs(inputs, overrides=overrides)
    overrides = _as_mapping(overrides)
    systems = _as_mapping(inputs.get("systems"))
    assumptions = list(context.get("assumptions", []))
    missing_inputs: list[str] = []
    nominal_power_kw: dict[str, float] = {}
    phase_power_kw: dict[str, float] = {}
    phase_key = _phase_key(phase)

    if phase_key not in AVIONICS_INSTRUMENTS_PHASE_FACTORS:
        raise ValueError(
            f"Unsupported phase '{phase}'. "
            "Use one of: ground, taxi, takeoff, climb, cruise, descent, approach, landing"
        )

    bleedless_factor = _coalesce(
        overrides.get("air_conditioning_bleedless_factor"),
        systems.get("air_conditioning_bleedless_factor"),
        inputs.get("air_conditioning_bleedless_factor"),
        1.0,
    )
    if float(bleedless_factor) < 1.0:
        raise ValueError("air_conditioning_bleedless_factor must be >= 1.0")
    if float(bleedless_factor) != 1.0:
        assumptions.append(
            f"Applied air_conditioning_bleedless_factor={float(bleedless_factor):.3g}."
        )

    if context["fuselage_length_m"] is not None:
        nominal_power_kw["lights"] = lights_nominal_power_kw(context["fuselage_length_m"])
        nominal_power_kw["avionics_and_instruments"] = avionics_instruments_nominal_power_kw(
            context["fuselage_length_m"]
        )
        nominal_power_kw["fuel_system"] = fuel_system_nominal_power_kw(
            context["fuselage_length_m"]
        )
        phase_power_kw["lights"] = subsystem_phase_power_kw(
            "lights", nominal_power_kw["lights"], phase_key
        )
        phase_power_kw["avionics_and_instruments"] = avionics_instruments_phase_power_kw(
            context["fuselage_length_m"], phase_key
        )
        phase_power_kw["fuel_system"] = subsystem_phase_power_kw(
            "fuel_system", nominal_power_kw["fuel_system"], phase_key
        )
    else:
        missing_inputs.extend(
            [
                "fuselage_length_m required for lights power",
                "fuselage_length_m required for avionics/instruments power",
                "fuselage_length_m required for fuel-system power",
            ]
        )

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["n_engines"] is not None
    ):
        nominal_power_kw["galley_entertainment_furnishing"] = (
            galley_entertainment_furnishing_nominal_power_kw(
                context["fuselage_length_m"],
                context["fuselage_width_m"],
                int(context["n_engines"]),
            )
        )
        phase_power_kw["galley_entertainment_furnishing"] = subsystem_phase_power_kw(
            "galley_entertainment_furnishing",
            nominal_power_kw["galley_entertainment_furnishing"],
            phase_key,
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, and n_engines required for galley/entertainment/furnishing power"
        )

    if context["wing_area_m2"] is not None:
        nominal_power_kw["ice_protection"] = ice_protection_nominal_power_kw(
            context["wing_area_m2"]
        )
        nominal_power_kw["electrothermal_deicing"] = electrothermal_deicing_nominal_power_kw(
            nominal_power_kw["ice_protection"]
        )
        phase_power_kw["ice_protection"] = subsystem_phase_power_kw(
            "ice_protection", nominal_power_kw["ice_protection"], phase_key
        )
        phase_power_kw["electrothermal_deicing"] = electrothermal_deicing_nominal_power_kw(
            phase_power_kw["ice_protection"]
        )
    else:
        missing_inputs.append("wing_area_m2 required for ice-protection power")

    if context["cabin_volume_m3"] is not None:
        nominal_power_kw["air_conditioning"] = (
            air_conditioning_nominal_power_kw(context["cabin_volume_m3"])
            * float(bleedless_factor)
        )
        phase_power_kw["air_conditioning"] = subsystem_phase_power_kw(
            "air_conditioning", nominal_power_kw["air_conditioning"], phase_key
        )
    else:
        missing_inputs.append("cabin_volume_m3 required for air-conditioning power")

    return {
        "phase": phase_key,
        "nominal_power_kw": nominal_power_kw,
        "phase_power_kw": phase_power_kw,
        "total_nominal_power_kw": sum(nominal_power_kw.values()),
        "total_phase_power_kw": sum(phase_power_kw.values()),
        "assumptions": assumptions,
        "missing_inputs": missing_inputs,
    }


def estimate_subsystem_power_by_phase_from_inputs(
    inputs: Mapping[str, Any],
    *,
    phases: Optional[Iterable[str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Estimate subsystem power demand across a set of mission phases."""
    if phases is None:
        phases = (
            "ground",
            "taxi",
            "takeoff",
            "climb",
            "cruise",
            "descent",
            "approach",
            "landing",
        )

    results_by_phase: dict[str, dict[str, float]] = {}
    phase_totals_kw: dict[str, float] = {}
    nominal_power_kw: Optional[dict[str, float]] = None
    assumptions: list[str] = []
    missing_inputs: list[str] = []

    for phase in phases:
        result = estimate_subsystem_power_from_inputs(
            inputs,
            phase=phase,
            overrides=overrides,
        )
        phase_key = result["phase"]
        if nominal_power_kw is None:
            nominal_power_kw = dict(result["nominal_power_kw"])
        results_by_phase[phase_key] = dict(result["phase_power_kw"])
        phase_totals_kw[phase_key] = float(result["total_phase_power_kw"])
        for assumption in result["assumptions"]:
            if assumption not in assumptions:
                assumptions.append(assumption)
        for missing in result["missing_inputs"]:
            if missing not in missing_inputs:
                missing_inputs.append(missing)

    return {
        "nominal_power_kw": nominal_power_kw or {},
        "phase_power_kw": results_by_phase,
        "phase_totals_kw": phase_totals_kw,
        "assumptions": assumptions,
        "missing_inputs": missing_inputs,
    }


def estimate_subsystem_weights_from_inputs(
    inputs: Mapping[str, Any],
    *,
    overrides: Optional[Mapping[str, Any]] = None,
) -> dict[str, Any]:
    """Estimate subsystem masses from the worked-example sizing dictionary."""
    context = derive_system_context_from_inputs(inputs, overrides=overrides)
    overrides = _as_mapping(overrides)
    systems = _as_mapping(inputs.get("systems"))
    assumptions = list(context.get("assumptions", []))
    missing_inputs: list[str] = []
    weights_kg: dict[str, float] = {}

    aircraft_class = str(
        _coalesce(
            overrides.get("fuel_system_aircraft_class"),
            systems.get("fuel_system_aircraft_class"),
            inputs.get("fuel_system_aircraft_class"),
            "transport",
        )
    ).strip().lower()
    n_fuel_tanks = _coalesce(
        overrides.get("n_fuel_tanks"),
        systems.get("n_fuel_tanks"),
        inputs.get("n_fuel_tanks"),
    )

    if context["max_fuel_capacity_kg"] is not None and context["n_engines"] is not None:
        fuel_kwargs: dict[str, Any] = {"aircraft_class": aircraft_class}
        if aircraft_class == "transport":
            if context["v_max_mach"] is None:
                missing_inputs.append(
                    "v_max_mach required for transport fuel-system weight"
                )
            else:
                fuel_kwargs["v_max_mach"] = context["v_max_mach"]
        if aircraft_class == "fighter_attack":
            if n_fuel_tanks is None:
                missing_inputs.append(
                    "n_fuel_tanks required for fighter_attack fuel-system weight"
                )
            else:
                fuel_kwargs["n_tanks"] = int(n_fuel_tanks)

        if "v_max_mach required for transport fuel-system weight" not in missing_inputs and (
            aircraft_class != "fighter_attack"
            or "n_fuel_tanks required for fighter_attack fuel-system weight" not in missing_inputs
        ):
            weights_kg["fuel_system"] = fuel_system_weight_kg(
                context["max_fuel_capacity_kg"],
                int(context["n_engines"]),
                **fuel_kwargs,
            )
    else:
        missing_inputs.append("max_fuel_capacity_kg and n_engines required for fuel-system weight")

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["wing_area_m2"] is not None
        and context["v_max_mach"] is not None
    ):
        weights_kg["hydraulic_system"] = hydraulic_system_weight_kg(
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            context["wing_area_m2"],
            context["v_max_mach"],
            n_wing_engines=int(context["n_wing_engines"] or 0),
            n_fuselage_engines=int(context["n_fuselage_engines"] or 0),
            n_fuselages=int(context["n_fuselages"] or 1),
            hydraulic_pressure_psi=float(context["hydraulic_pressure_psi"]),
            variable_sweep_factor=float(context["variable_sweep_factor"]),
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, wing_area_m2, and v_max_mach required for hydraulic-system weight"
        )

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["n_engines"] is not None
        and context["n_passengers"] is not None
        and context["n_flight_crew"] is not None
    ):
        weights_kg["electrical_system"] = electrical_system_weight_kg(
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            int(context["n_engines"]),
            int(context["n_passengers"]),
            int(context["n_flight_crew"]),
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, n_engines, n_passengers, and n_flight_crew required for electrical-system weight"
        )

    if (
        context["design_range_m"] is not None
        and context["n_flight_crew"] is not None
        and context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
    ):
        weights_kg["avionics"] = avionics_system_weight_kg(
            context["design_range_m"],
            int(context["n_flight_crew"]),
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "design_range_m, n_flight_crew, fuselage_length_m, and fuselage_width_m required for avionics weight"
        )

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["n_passengers"] is not None
    ):
        weights_kg["apu"] = auxiliary_power_unit_weight_kg(
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            int(context["n_passengers"]),
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, and n_passengers required for APU weight"
        )

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["v_max_mach"] is not None
        and context["n_flight_crew"] is not None
    ):
        weights_kg["instruments"] = instruments_system_weight_kg(
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            context["v_max_mach"],
            int(context["n_flight_crew"]),
            n_wing_engines=int(context["n_wing_engines"] or 0),
            n_fuselage_engines=int(context["n_fuselage_engines"] or 0),
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, v_max_mach, and n_flight_crew required for instruments weight"
        )

    if (
        context["fuselage_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["fuselage_depth_m"] is not None
        and context["n_passengers"] is not None
        and context["v_max_mach"] is not None
        and weights_kg.get("avionics") is not None
    ):
        weights_kg["air_conditioning"] = air_conditioning_system_weight_kg(
            context["fuselage_length_m"],
            context["fuselage_width_m"],
            context["fuselage_depth_m"],
            int(context["n_passengers"]),
            context["v_max_mach"],
            weights_kg["avionics"],
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "fuselage_length_m, fuselage_width_m, fuselage_depth_m, n_passengers, v_max_mach, and avionics weight required for air-conditioning weight"
        )

    if (
        context["wing_span_m"] is not None
        and context["wing_sweep_quarter_chord_deg"] is not None
        and context["n_engines"] is not None
        and context["engine_diameter_m"] is not None
        and context["fuselage_width_m"] is not None
    ):
        weights_kg["ice_protection"] = ice_protection_system_weight_kg(
            context["wing_span_m"],
            context["wing_sweep_quarter_chord_deg"],
            int(context["n_engines"]),
            context["engine_diameter_m"],
            context["fuselage_width_m"],
        )
    else:
        missing_inputs.append(
            "wing_span_m, wing_sweep_quarter_chord_deg, n_engines, engine_diameter_m, and fuselage_width_m required for ice-protection weight"
        )

    if (
        context["n_flight_crew"] is not None
        and context["passenger_compartment_length_m"] is not None
        and context["fuselage_width_m"] is not None
        and context["fuselage_depth_m"] is not None
        and context["n_first_class_passengers"] is not None
        and context["n_business_class_passengers"] is not None
        and context["n_tourist_class_passengers"] is not None
    ):
        weights_kg["furnishings_floops"] = furnishings_weight_kg(
            int(context["n_flight_crew"]),
            context["passenger_compartment_length_m"],
            context["fuselage_width_m"],
            context["fuselage_depth_m"],
            n_first_class_passengers=int(context["n_first_class_passengers"]),
            n_business_class_passengers=int(context["n_business_class_passengers"]),
            n_tourist_class_passengers=int(context["n_tourist_class_passengers"]),
            n_fuselages=int(context["n_fuselages"] or 1),
        )
    else:
        missing_inputs.append(
            "n_flight_crew, passenger_compartment_length_m, fuselage_width_m, fuselage_depth_m, and passenger-class counts required for FLOPS furnishings weight"
        )

    if (
        context["n_flight_crew"] is not None
        and context["n_passengers"] is not None
        and context["cabin_volume_m3"] is not None
    ):
        weights_kg["furnishings_mohan"] = galley_entertainment_furnishing_weight_mohan_kg(
            int(context["n_flight_crew"]),
            int(context["n_passengers"]),
            context["cabin_volume_m3"],
        )
    else:
        missing_inputs.append(
            "n_flight_crew, n_passengers, and cabin_volume_m3 required for Mohan furnishings weight"
        )

    return {
        "weights_kg": weights_kg,
        "total_weight_kg": sum(weights_kg.values()),
        "assumptions": assumptions,
        "missing_inputs": missing_inputs,
    }
