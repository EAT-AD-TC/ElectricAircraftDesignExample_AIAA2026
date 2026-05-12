import math
from typing import Optional


def isa_density_kg_per_m3(altitude_m: float) -> float:
    """
    Return ISA air density [kg/m^3] for a geometric altitude in meters.

    A simple troposphere/lower-stratosphere model is sufficient here because
    the function is only used for conceptual sizing.
    """
    g0 = 9.80665
    r_air = 287.05287
    t0 = 288.15
    p0 = 101325.0
    lapse = 0.0065

    h = max(0.0, float(altitude_m))

    if h <= 11000.0:
        t = t0 - lapse * h
        p = p0 * (t / t0) ** (g0 / (r_air * lapse))
    else:
        t = 216.65
        t11 = t0 - lapse * 11000.0
        p11 = p0 * (t11 / t0) ** (g0 / (r_air * lapse))
        p = p11 * math.exp(-g0 * (h - 11000.0) / (r_air * t))

    return p / (r_air * t)


def density_scaled_turboshaft_power(
    rated_power_reference_w: float,
    rho_altitude_kg_per_m3: float,
    rho_reference_kg_per_m3: float = 1.225,
    xi: float = 1.0,
) -> dict:
    """
    Scale rated turboshaft power with density ratio using:

      P_z = P_ref * (rho_z / rho_ref)^xi

    Parameters
    ----------
    rated_power_reference_w : float
        Rated power at the reference density [W].
    rho_altitude_kg_per_m3 : float
        Air density at the target altitude [kg/m^3].
    rho_reference_kg_per_m3 : float, optional
        Reference air density [kg/m^3]. Defaults to ISA sea level.
    xi : float, optional
        Empirical density exponent [-].
    """
    p_ref = float(rated_power_reference_w)
    rho_z = float(rho_altitude_kg_per_m3)
    rho_ref = float(rho_reference_kg_per_m3)
    xi_value = float(xi)

    if p_ref < 0.0:
        raise ValueError("rated_power_reference_w must be >= 0")
    if rho_z <= 0.0:
        raise ValueError("rho_altitude_kg_per_m3 must be > 0")
    if rho_ref <= 0.0:
        raise ValueError("rho_reference_kg_per_m3 must be > 0")

    density_ratio = rho_z / rho_ref
    rated_power_altitude_w = p_ref * (density_ratio ** xi_value)

    return {
        "rated_power_altitude_W": rated_power_altitude_w,
        "rated_power_altitude_kW": rated_power_altitude_w / 1000.0,
        "density_ratio": density_ratio,
        "rho_altitude_kg_per_m3": rho_z,
        "rho_reference_kg_per_m3": rho_ref,
        "xi": xi_value,
    }


def density_scaled_turboshaft_power_from_altitude(
    rated_power_reference_w: float,
    altitude_m: float,
    rho_reference_kg_per_m3: float = 1.225,
    xi: float = 1.0,
) -> dict:
    """
    Convenience wrapper for density_scaled_turboshaft_power that computes ISA
    density from altitude first.
    """
    altitude = float(altitude_m)
    rho_altitude = isa_density_kg_per_m3(altitude)
    out = density_scaled_turboshaft_power(
        rated_power_reference_w=rated_power_reference_w,
        rho_altitude_kg_per_m3=rho_altitude,
        rho_reference_kg_per_m3=rho_reference_kg_per_m3,
        xi=xi,
    )
    out["altitude_m"] = altitude
    return out


def parallel_thermal_engine_power(
    P_p: float,
    Phi: float,
    eta_p: float,
    eta_gb: float,
    eta_te: float,
    eta_em: float,
) -> float:
    """
    Parallel-hybrid thermal-engine power, P_te [W].

    Implements:
      P_te = P_p / (eta_p * eta_gb * ((Phi / (1 - Phi)) * (eta_em / eta_te) + 1))
    """
    return P_p / (eta_p * eta_gb * (((Phi / (1.0 - Phi)) * (eta_em / eta_te)) + 1.0))


def parallel_electric_motor_power(
    P_p: float,
    Phi: float,
    eta_p: float,
    eta_gb: float,
    eta_te: float,
    eta_em: float,
) -> float:
    """
    Parallel-hybrid electric-motor power, P_em [W].

    Implements:
      P_em = P_p / (eta_p * eta_gb * (1 + ((1 - Phi) / Phi) * (eta_te / eta_em)))
    """
    return P_p / (eta_p * eta_gb * (1.0 + (((1.0 - Phi) / Phi) * (eta_te / eta_em))))


def parallel_battery_power(
    P_p: float,
    Phi: float,
    eta_p: float,
    eta_gb: float,
    eta_te: float,
    eta_em: float,
) -> float:
    """
    Parallel-hybrid battery power, P_bat [W].

    Implements:
      P_bat = P_p / (eta_p * eta_gb * (eta_em + ((1 - Phi) / Phi) * eta_te))
    """
    return P_p / (eta_p * eta_gb * (eta_em + (((1.0 - Phi) / Phi) * eta_te)))


def inverter_mass_and_cooling_from_hybrid_inputs(
    W_over_Pp: float,
    Phi: float,
    eta_p: float,
    eta_gb: float,
    eta_te: float,
    eta_em: float,
    mtom_kg: float,
    g: float,
    inverter_specific_power_W_per_kg: float,
    eta_inverter: float,
    P_d_inverterCooling_kW_per_kg: float = 1.25,
) -> dict:
    """
    Return inverter power, inverter mass, and inverter cooling mass for a
    parallel-hybrid sizing point.

    The inverter power is taken from the electric-motor branch of the parallel
    hybrid power-loading relation, then converted to installed power using the
    current aircraft mass.
    """
    import class_2_battery_sizing
    import powertrain_component_sizing

    w_p_inverter = powertrain_component_sizing.WP_em_parallel(
        W_over_Pp=W_over_Pp,
        Phi=Phi,
        eta_p=eta_p,
        eta_gb=eta_gb,
        eta_te=eta_te,
        eta_em=eta_em,
    )
    p_inverter_w = (1.0 / float(w_p_inverter)) * float(mtom_kg) * float(g)

    inverter_mass_kg = class_2_battery_sizing.inverter_mass(
        P_inverter=p_inverter_w,
        P_d_invereter=inverter_specific_power_W_per_kg,
    )
    inverter_cooling_mass_kg = class_2_battery_sizing.inverter_cooling_mass_eq66(
        P_battery_kW=p_inverter_w / 1000.0,
        eta_inverter=float(eta_inverter),
        P_d_inverterCooling_kW_per_kg=P_d_inverterCooling_kW_per_kg,
    )

    mass_breakdown_kg = {
        "Inverter": inverter_mass_kg,
        "Inverter cooling": inverter_cooling_mass_kg,
    }

    return {
        "p_inverter_W": p_inverter_w,
        "w_p_inverter": float(w_p_inverter),
        "total_mass_kg": sum(mass_breakdown_kg.values()),
        "mass_breakdown_kg": mass_breakdown_kg,
        "inputs": {
            "W_over_Pp": float(W_over_Pp),
            "Phi": float(Phi),
            "eta_p": float(eta_p),
            "eta_gb": float(eta_gb),
            "eta_te": float(eta_te),
            "eta_em": float(eta_em),
            "mtom_kg": float(mtom_kg),
            "g": float(g),
            "inverter_specific_power_W_per_kg": float(inverter_specific_power_W_per_kg),
            "eta_inverter": float(eta_inverter),
            "P_d_inverterCooling_kW_per_kg": float(P_d_inverterCooling_kW_per_kg),
        },
    }


def estimate_propeller_cruise_power_loading(
    cruise_speed_mps: float,
    eta_propulsive: float,
    lift_to_drag: Optional[float] = None,
    wing_loading_n_per_m2: Optional[float] = None,
    rho_kg_per_m3: Optional[float] = None,
    cd0: Optional[float] = None,
    aspect_ratio: Optional[float] = None,
    oswald_efficiency: Optional[float] = None,
) -> dict:
    """
    Estimate cruise P/W [W/N] for a propeller aircraft.

    Preferred method:
      Use a drag-polar estimate with the current wing loading.

    Fallback method:
      Use the simpler conceptual relation P/W = V / (eta * L/D).
    """
    v = float(cruise_speed_mps)
    eta = float(eta_propulsive)

    if v <= 0.0:
        raise ValueError("cruise_speed_mps must be > 0")
    if eta <= 0.0:
        raise ValueError("eta_propulsive must be > 0")

    drag_polar_inputs = (
        wing_loading_n_per_m2,
        rho_kg_per_m3,
        cd0,
        aspect_ratio,
        oswald_efficiency,
    )

    if all(value is not None for value in drag_polar_inputs):
        wing_loading = float(wing_loading_n_per_m2)
        rho = float(rho_kg_per_m3)
        cd0_value = float(cd0)
        ar = float(aspect_ratio)
        e = float(oswald_efficiency)

        if wing_loading <= 0.0 or rho <= 0.0 or cd0_value <= 0.0 or ar <= 0.0 or e <= 0.0:
            raise ValueError("drag-polar cruise sizing inputs must be > 0")

        q = 0.5 * rho * v * v
        induced_factor = 1.0 / (math.pi * ar * e)
        p_w = (v / eta) * ((q * cd0_value / wing_loading) + (induced_factor * wing_loading / q))
        return {
            "method": "drag_polar",
            "P_W_cruise": p_w,
            "W_P_cruise": 1.0 / p_w,
        }

    if lift_to_drag is not None:
        l_d = float(lift_to_drag)
        if l_d <= 0.0:
            raise ValueError("lift_to_drag must be > 0")
        p_w = v / (eta * l_d)
        return {
            "method": "lift_to_drag",
            "P_W_cruise": p_w,
            "W_P_cruise": 1.0 / p_w,
        }

    raise KeyError(
        "Insufficient cruise-sizing inputs. Provide either lift_to_drag or "
        "the full drag-polar set with wing_loading_n_per_m2, rho_kg_per_m3, "
        "cd0, aspect_ratio, and oswald_efficiency."
    )


def cruise_w_p_from_dicts(
    mission,
    constraint_analysis_inputs,
    wing_loading_n_per_m2: Optional[float] = None,
    phase_name: str = "cruise",
) -> dict:
    """
    Compute phase W/P directly from the mission dict and the constraint-input dict.

    Preferred method:
      Use the drag-polar cruise relation when wing loading and aerodynamic data
      are available.

    Fallback method:
      Use the phase L/D value together with propulsive efficiency.
    """
    target_phase_name = str(phase_name).lower()
    cruise_phase = next(
        (phase for phase in mission if str(phase.get("phase", "")).lower() == target_phase_name),
        None,
    )
    if cruise_phase is None:
        raise KeyError(f"Mission must include a '{target_phase_name}' phase")

    cruise_speed = (
        cruise_phase.get("cruise_speed")
        or cruise_phase.get("climb_speed")
        or cruise_phase.get("speed")
        or constraint_analysis_inputs.get("cruise_speed")
    )
    if cruise_speed is None:
        raise KeyError("Cruise speed not found in mission or constraint inputs")

    lift_to_drag = cruise_phase.get("l_d")
    rho_cruise = (
        cruise_phase.get("rho")
        or cruise_phase.get("rho_cruise")
        or constraint_analysis_inputs.get("rho_cruise")
    )
    cd0 = (
        cruise_phase.get("CD_0")
        or cruise_phase.get("cd0")
        or constraint_analysis_inputs.get("CD_0")
        or constraint_analysis_inputs.get("cd0")
        or constraint_analysis_inputs.get("cd_0")
    )
    aspect_ratio = (
        cruise_phase.get("AR")
        or cruise_phase.get("A")
        or constraint_analysis_inputs.get("AR")
        or constraint_analysis_inputs.get("aspect_ratio")
    )
    oswald_efficiency = (
        cruise_phase.get("oswald_efficiency")
        or cruise_phase.get("e_oswald")
        or constraint_analysis_inputs.get("oswald efficiency")
        or constraint_analysis_inputs.get("oswald_efficiency")
        or constraint_analysis_inputs.get("e_oswald")
    )
    eta_propulsive = (
        cruise_phase.get("propeller_efficiency")
        or constraint_analysis_inputs.get("propeller_efficiency")
        or constraint_analysis_inputs.get("eta_p")
    )

    out = estimate_propeller_cruise_power_loading(
        cruise_speed_mps=float(cruise_speed),
        eta_propulsive=float(eta_propulsive),
        lift_to_drag=None if lift_to_drag is None else float(lift_to_drag),
        wing_loading_n_per_m2=wing_loading_n_per_m2,
        rho_kg_per_m3=None if rho_cruise is None else float(rho_cruise),
        cd0=None if cd0 is None else float(cd0),
        aspect_ratio=None if aspect_ratio is None else float(aspect_ratio),
        oswald_efficiency=None if oswald_efficiency is None else float(oswald_efficiency),
    )
    out.update(
        {
            "phase_name": target_phase_name,
            "cruise_speed_mps": float(cruise_speed),
            "L_D": None if lift_to_drag is None else float(lift_to_drag),
        }
    )
    return out

def conventional_breguet_weight_fraction_psfc(
    range_m: float,
    lift_to_drag: float,
    eta_propulsive: float,
    psfc_kg_per_kwh: float,
    g: float = 9.81,
) -> dict:
    """
    Standard propeller-aircraft Breguet weight fraction using PSFC.

    Uses:
      R = (eta_propulsive / (psfc * g)) * (L/D) * ln(W_i / W_f)

    where:
      psfc is converted internally from kg/kWh to kg/J
    """
    r = max(0.0, float(range_m))
    l_d = float(lift_to_drag)
    eta = float(eta_propulsive)
    psfc_kwh = float(psfc_kg_per_kwh)
    g_local = float(g)

    if l_d <= 0.0 or eta <= 0.0 or psfc_kwh <= 0.0 or g_local <= 0.0:
        raise ValueError("PSFC Breguet inputs must be > 0")

    psfc_kg_per_j = psfc_kwh / (1000.0 * 3600.0)

    range_constant = (eta / (psfc_kg_per_j * g_local)) * l_d
    weight_fraction = math.exp(-r / range_constant)

    return {
        "range_constant_m": range_constant,
        "weight_fraction": weight_fraction,
        "fuel_fraction": 1.0 - weight_fraction,
    }






def conventional_breguet_weight_fraction(
    range_m: float,
    lift_to_drag: float,
    eta_total: float,
    fuel_specific_energy_J_per_kg: float,
    g: float = 9.81,
) -> dict:
    """
    Standard conceptual Breguet prop-aircraft weight fraction.

    Uses the energy-based form:
      R = eta_total * (h_f / g) * (L/D) * ln(W_i / W_f)
    """
    r = max(0.0, float(range_m))
    l_d = float(lift_to_drag)
    eta = float(eta_total)
    h_f = float(fuel_specific_energy_J_per_kg)
    g_local = float(g)

    if l_d <= 0.0 or eta <= 0.0 or h_f <= 0.0 or g_local <= 0.0:
        raise ValueError("Breguet inputs must be > 0")

    range_constant = eta * (h_f / g_local) * l_d
    weight_fraction = math.exp(-r / range_constant)

    return {
        "range_constant_m": range_constant,
        "weight_fraction": weight_fraction,
        "fuel_fraction": 1.0 - weight_fraction,
    }


def breguet_fuel_fraction_from_phase(
    ph,
    constraint_analysis_inputs,
    fuel_specific_energy_J_per_kg: Optional[float] = None,
    eta_total: Optional[float] = None,
    g: float = 9.81,
) -> dict:
    """
    Compute standard Breguet weight and fuel fractions for a mission phase dict.

    Parameters
    ----------
    ph : dict
        Current mission phase dict. Expected to contain at least:
        - "phase"
        - "range"
        - "l_d"
    constraint_analysis_inputs : dict
        Constraint-analysis input dict. Used as a fallback source for
        propulsive efficiency and other phase metadata.
    fuel_specific_energy_J_per_kg : float, optional
        Fuel specific energy [J/kg]. If omitted, tries:
        - constraint_analysis_inputs["fuel_specific_energy_J_per_kg"]
        - constraint_analysis_inputs["e_f"]
    eta_total : float, optional
        Overall efficiency used in the energy-form Breguet relation.
        If omitted, tries:
        - ph["eta_total"]
        - constraint_analysis_inputs["eta_total"]
        - constraint_analysis_inputs["propeller_efficiency"]
        - constraint_analysis_inputs["eta_p"]
    g : float
        Gravity [m/s^2]
    """
    phase_name = str(ph.get("phase", "")).lower()
    range_m = ph.get("range")
    lift_to_drag = ph.get("l_d")

    if range_m is None:
        raise KeyError(f"Phase '{phase_name}' must define 'range'")
    if lift_to_drag is None:
        raise KeyError(f"Phase '{phase_name}' must define 'l_d'")

    if fuel_specific_energy_J_per_kg is None:
        fuel_specific_energy_J_per_kg = (
            ph.get("fuel_specific_energy_J_per_kg")
            or ph.get("e_f")
            or constraint_analysis_inputs.get("fuel_specific_energy_J_per_kg")
            or constraint_analysis_inputs.get("e_f")
        )
    if fuel_specific_energy_J_per_kg is None:
        raise KeyError(
            "Fuel specific energy not found. Pass fuel_specific_energy_J_per_kg "
            "or provide it in the phase/constraint dict."
        )

    if eta_total is None:
        eta_total = (
            ph.get("eta_total")
            or constraint_analysis_inputs.get("eta_total")
            or constraint_analysis_inputs.get("propeller_efficiency")
            or constraint_analysis_inputs.get("eta_p")
        )
    if eta_total is None:
        raise KeyError(
            "eta_total not found. Pass eta_total or provide "
            "'propeller_efficiency'/'eta_p' in constraint_analysis_inputs."
        )

    out = conventional_breguet_weight_fraction(
        range_m=float(range_m),
        lift_to_drag=float(lift_to_drag),
        eta_total=float(eta_total),
        fuel_specific_energy_J_per_kg=float(fuel_specific_energy_J_per_kg),
        g=g,
    )

    out.update(
        {
            "phase": phase_name,
            "range_m": float(range_m),
            "L_D": float(lift_to_drag),
            "eta_total": float(eta_total),
            "fuel_specific_energy_J_per_kg": float(fuel_specific_energy_J_per_kg),
        }
    )
    return out


def conventional_breguet_loiter_weight_fraction(
    loiter_time_s: float,
    loiter_speed_mps: float,
    lift_to_drag: float,
    eta_total: float,
    fuel_specific_energy_J_per_kg: float,
    g: float = 9.81,
) -> dict:
    """
    Compute Breguet loiter weight and fuel fractions by converting loiter time
    to an equivalent range using the loiter speed.

    This keeps the result consistent with the existing energy-based Breguet
    range helper already used elsewhere in the codebase.
    """
    time_s = float(loiter_time_s)
    speed_mps = float(loiter_speed_mps)

    if time_s < 0.0:
        raise ValueError("loiter_time_s must be >= 0")
    if speed_mps <= 0.0:
        raise ValueError("loiter_speed_mps must be > 0")

    equivalent_range_m = time_s * speed_mps
    out = conventional_breguet_weight_fraction(
        range_m=equivalent_range_m,
        lift_to_drag=lift_to_drag,
        eta_total=eta_total,
        fuel_specific_energy_J_per_kg=fuel_specific_energy_J_per_kg,
        g=g,
    )
    out.update(
        {
            "loiter_time_s": time_s,
            "loiter_time_min": time_s / 60.0,
            "loiter_speed_mps": speed_mps,
            "equivalent_range_m": equivalent_range_m,
            "equivalent_range_km": equivalent_range_m / 1000.0,
        }
    )
    return out

def conventional_breguet_loiter_weight_fraction_psfc(
    loiter_time_s: float,
    loiter_speed_mps: float,
    lift_to_drag: float,
    eta_propulsive: float,
    psfc_kg_per_kwh: float,
    g: float = 9.81,
) -> dict:
    """
    Propeller-aircraft Breguet loiter weight fraction using the endurance form.

    Uses:
      t = (eta_propulsive / (psfc * g * V)) * (L/D) * ln(W_i / W_f)

    where psfc is provided in kg/kWh and converted internally to kg/J.
    """
    time_s = float(loiter_time_s)
    speed_mps = float(loiter_speed_mps)
    l_d = float(lift_to_drag)
    eta = float(eta_propulsive)
    psfc_kwh = float(psfc_kg_per_kwh)
    g_local = float(g)

    if time_s < 0.0:
        raise ValueError("loiter_time_s must be >= 0")
    if speed_mps <= 0.0 or l_d <= 0.0 or eta <= 0.0 or psfc_kwh <= 0.0 or g_local <= 0.0:
        raise ValueError("Loiter Breguet inputs must be > 0")

    psfc_kg_per_j = psfc_kwh / (1000.0 * 3600.0)

    endurance_constant_s = (eta / (psfc_kg_per_j * g_local * speed_mps)) * l_d
    weight_fraction = math.exp(-time_s / endurance_constant_s)

    return {
        "endurance_constant_s": endurance_constant_s,
        "endurance_constant_min": endurance_constant_s / 60.0,
        "weight_fraction": weight_fraction,
        "fuel_fraction": 1.0 - weight_fraction,
        "loiter_time_s": time_s,
        "loiter_time_min": time_s / 60.0,
        "loiter_speed_mps": speed_mps,
    }

















    

def breguet_loiter_fuel_fraction_from_phase(
    ph,
    constraint_analysis_inputs,
    loiter_time_min: float = 45.0,
    fuel_specific_energy_J_per_kg: Optional[float] = None,
    eta_total: Optional[float] = None,
    loiter_speed_mps: Optional[float] = None,
    g: float = 9.81,
) -> dict:
    """
    Compute a Breguet loiter fuel fraction for a mission phase using a loiter
    time and whichever phase speed is available in the mission dict.

    Speed fallback order:
    - phase['loiter_speed']
    - phase['cruise_speed']
    - phase['speed']
    - phase['climb_speed']
    - constraint_analysis_inputs['loiter_speed']
    - constraint_analysis_inputs['cruise_speed']
    """
    phase_name = str(ph.get("phase", "")).lower()
    lift_to_drag = ph.get("l_d")
    if lift_to_drag is None:
        raise KeyError(f"Phase '{phase_name}' must define 'l_d'")

    if fuel_specific_energy_J_per_kg is None:
        fuel_specific_energy_J_per_kg = (
            ph.get("fuel_specific_energy_J_per_kg")
            or ph.get("e_f")
            or constraint_analysis_inputs.get("fuel_specific_energy_J_per_kg")
            or constraint_analysis_inputs.get("e_f")
        )
    if fuel_specific_energy_J_per_kg is None:
        raise KeyError(
            "Fuel specific energy not found. Pass fuel_specific_energy_J_per_kg "
            "or provide it in the phase/constraint dict."
        )

    if eta_total is None:
        eta_total = (
            ph.get("eta_total")
            or constraint_analysis_inputs.get("eta_total")
            or constraint_analysis_inputs.get("propeller_efficiency")
            or constraint_analysis_inputs.get("eta_p")
        )
    if eta_total is None:
        raise KeyError(
            "eta_total not found. Pass eta_total or provide "
            "'propeller_efficiency'/'eta_p' in constraint_analysis_inputs."
        )

    if loiter_speed_mps is None:
        loiter_speed_mps = (
            ph.get("loiter_speed")
            or ph.get("cruise_speed")
            or ph.get("speed")
            or ph.get("climb_speed")
            or constraint_analysis_inputs.get("loiter_speed")
            or constraint_analysis_inputs.get("cruise_speed")
        )
    if loiter_speed_mps is None:
        raise KeyError(
            f"No usable loiter speed found for phase '{phase_name}'. "
            "Pass loiter_speed_mps or add a speed to the phase/constraint dict."
        )

    out = conventional_breguet_loiter_weight_fraction(
        loiter_time_s=60.0 * float(loiter_time_min),
        loiter_speed_mps=float(loiter_speed_mps),
        lift_to_drag=float(lift_to_drag),
        eta_total=float(eta_total),
        fuel_specific_energy_J_per_kg=float(fuel_specific_energy_J_per_kg),
        g=g,
    )
    out.update(
        {
            "phase": phase_name,
            "L_D": float(lift_to_drag),
            "eta_total": float(eta_total),
            "fuel_specific_energy_J_per_kg": float(fuel_specific_energy_J_per_kg),
        }
    )
    return out


def conventional_breguet_fuel_required_from_final_mass(
    final_mass_kg: float,
    range_m: float,
    lift_to_drag: float,
    eta_total: float,
    fuel_specific_energy_J_per_kg: float,
    g: float = 9.81,
) -> dict:
    """
    Compute the fuel required to complete a range segment when the landing/end
    mass for that segment is known.
    """
    final_mass = float(final_mass_kg)
    if final_mass < 0.0:
        raise ValueError("final_mass_kg must be >= 0")

    if range_m <= 0.0:
        return {
            "initial_mass_kg": final_mass,
            "final_mass_kg": final_mass,
            "fuel_mass_kg": 0.0,
            "weight_fraction": 1.0,
            "fuel_fraction": 0.0,
            "range_constant_m": math.inf,
        }

    weight_fraction_out = conventional_breguet_weight_fraction(
        range_m=range_m,
        lift_to_drag=lift_to_drag,
        eta_total=eta_total,
        fuel_specific_energy_J_per_kg=fuel_specific_energy_J_per_kg,
        g=g,
    )

    weight_fraction = weight_fraction_out["weight_fraction"]
    initial_mass = final_mass / weight_fraction
    fuel_mass = initial_mass - final_mass

    return {
        "initial_mass_kg": initial_mass,
        "final_mass_kg": final_mass,
        "fuel_mass_kg": fuel_mass,
        "weight_fraction": weight_fraction,
        "fuel_fraction": weight_fraction_out["fuel_fraction"],
        "range_constant_m": weight_fraction_out["range_constant_m"],
    }


def conventional_breguet_fuel_required_from_final_mass_psfc(
    final_mass_kg: float,
    range_m: float,
    lift_to_drag: float,
    eta_propulsive: float,
    psfc_kg_per_j: float,
    g: float = 9.81,
) -> dict:
    """
    Propeller-aircraft Breguet fuel requirement using power specific fuel
    consumption.

    Uses:
      R = (eta_propulsive / (psfc * g)) * (L/D) * ln(W_i / W_f)

    where psfc is expressed in kg/J, equivalent to kg/(W*s).
    """
    final_mass = float(final_mass_kg)
    r = max(0.0, float(range_m))
    l_d = float(lift_to_drag)
    eta = float(eta_propulsive)
    psfc = float(psfc_kg_per_j)
    g_local = float(g)

    if final_mass < 0.0:
        raise ValueError("final_mass_kg must be >= 0")
    if r <= 0.0:
        return {
            "initial_mass_kg": final_mass,
            "final_mass_kg": final_mass,
            "fuel_mass_kg": 0.0,
            "weight_fraction": 1.0,
            "fuel_fraction": 0.0,
            "range_constant_m": math.inf,
        }
    if l_d <= 0.0 or eta <= 0.0 or psfc <= 0.0 or g_local <= 0.0:
        raise ValueError("PSFC Breguet inputs must be > 0")

    range_constant = (eta / (psfc * g_local)) * l_d
    weight_fraction = math.exp(-r / range_constant)
    initial_mass = final_mass / weight_fraction
    fuel_mass = initial_mass - final_mass

    return {
        "initial_mass_kg": initial_mass,
        "final_mass_kg": final_mass,
        "fuel_mass_kg": fuel_mass,
        "weight_fraction": weight_fraction,
        "fuel_fraction": 1.0 - weight_fraction,
        "range_constant_m": range_constant,
    }


def subsystem_nominal_powers_kw(
    fuselage_length_m: float,
    wing_area_m2: float,
    cabin_volume_m3: float,
    n_engines: int,
) -> dict:
    """
    Nominal subsystem powers from the provided correlations.

    All returned powers are in kW.
    """
    l_fuselage = float(fuselage_length_m)
    s_wing = float(wing_area_m2)
    v_cabin = float(cabin_volume_m3)
    n_eng = int(n_engines)

    if l_fuselage <= 0.0 or s_wing <= 0.0 or v_cabin <= 0.0 or n_eng <= 0:
        raise ValueError("All subsystem sizing inputs must be positive")

    powers_kw = {
        "lights": 0.31 * l_fuselage,
        "avionics_instruments": 0.02 * (l_fuselage ** 1.55),
        "ice_protection": 0.035 * s_wing + 2.02,
        "air_conditioning": 0.077 * v_cabin - 0.40,
        "fuel_system": 2.88 * math.exp((0.0399 * l_fuselage) / n_eng),
    }

    powers_kw["total_without_fuel_system"] = (
        powers_kw["lights"]
        + powers_kw["avionics_instruments"]
        + powers_kw["ice_protection"]
        + powers_kw["air_conditioning"]
    )
    powers_kw["total_with_fuel_system"] = powers_kw["total_without_fuel_system"] + powers_kw["fuel_system"]
    return powers_kw


def subsystem_power_energy_from_mission(
    mission,
    fuselage_length_m: float,
    wing_area_m2: float,
    cabin_volume_m3: float,
    n_engines: int,
    phase_names=("climb", "cruise", "ifr"),
    fuel_system_phases=("ifr",),
) -> dict:
    """
    Compute subsystem powers and energies for mission phases using the phase
    range and the available phase speed.

    - `climb` uses `climb_speed`
    - `cruise` uses `cruise_speed`
    - `ifr` falls back through `cruise_speed`, `loiter_speed`, then the cruise
      phase speed if no explicit speed is present in the IFR phase dict

    Powers are returned in both kW and W. Energies are returned in both J and
    kWh.
    """
    target_phases = {str(name).lower() for name in phase_names}
    fuel_phases = {str(name).lower() for name in fuel_system_phases}
    powers_kw_nominal = subsystem_nominal_powers_kw(
        fuselage_length_m=fuselage_length_m,
        wing_area_m2=wing_area_m2,
        cabin_volume_m3=cabin_volume_m3,
        n_engines=n_engines,
    )

    cruise_phase = next(
        (phase for phase in mission if str(phase.get("phase", "")).lower() == "cruise"),
        None,
    )
    cruise_speed_fallback = None if cruise_phase is None else cruise_phase.get("cruise_speed")

    def phase_speed_mps(phase_name: str, phase: dict) -> float:
        if phase_name == "climb":
            speed = phase.get("climb_speed") or phase.get("speed") or cruise_speed_fallback
        elif phase_name == "cruise":
            speed = phase.get("cruise_speed") or phase.get("speed") or cruise_speed_fallback
        elif phase_name == "ifr":
            speed = (
                phase.get("cruise_speed")
                or phase.get("loiter_speed")
                or phase.get("speed")
                or cruise_speed_fallback
            )
        else:
            speed = phase.get("speed") or cruise_speed_fallback

        if speed is None:
            raise KeyError(f"No usable speed found for phase '{phase_name}'")

        speed = float(speed)
        if speed <= 0.0:
            raise ValueError(f"Phase '{phase_name}' speed must be > 0")
        return speed

    phase_results = []
    total_energy_j_by_subsystem = {
        "lights": 0.0,
        "avionics_instruments": 0.0,
        "ice_protection": 0.0,
        "air_conditioning": 0.0,
        "fuel_system": 0.0,
    }
    total_time_s = 0.0

    for phase in mission:
        name = str(phase.get("phase", "")).lower()
        if name not in target_phases:
            continue
        if "range" not in phase:
            continue

        range_m = float(phase["range"])
        speed_mps = phase_speed_mps(name, phase)
        time_s = range_m / speed_mps
        total_time_s += time_s

        power_kw = {
            "lights": powers_kw_nominal["lights"],
            "avionics_instruments": powers_kw_nominal["avionics_instruments"],
            "ice_protection": powers_kw_nominal["ice_protection"],
            "air_conditioning": powers_kw_nominal["air_conditioning"],
            "fuel_system": powers_kw_nominal["fuel_system"] if name in fuel_phases else 0.0,
        }
        power_kw["total"] = sum(power_kw.values())

        power_w = {key: value * 1000.0 for key, value in power_kw.items()}
        energy_j = {key: power_w[key] * time_s for key in power_kw}
        energy_kwh = {key: energy_j[key] / 3.6e6 for key in power_kw}

        for subsystem in total_energy_j_by_subsystem:
            total_energy_j_by_subsystem[subsystem] += energy_j[subsystem]

        phase_results.append(
            {
                "phase": name,
                "range_m": range_m,
                "speed_mps": speed_mps,
                "time_s": time_s,
                "time_min": time_s / 60.0,
                "power_kw": power_kw,
                "power_w": power_w,
                "energy_j": energy_j,
                "energy_kwh": energy_kwh,
            }
        )

    total_energy_j = dict(total_energy_j_by_subsystem)
    total_energy_j["total"] = sum(total_energy_j_by_subsystem.values())
    total_energy_kwh = {key: value / 3.6e6 for key, value in total_energy_j.items()}

    return {
        "nominal_powers_kw": powers_kw_nominal,
        "phase_results": phase_results,
        "total_time_s": total_time_s,
        "total_time_min": total_time_s / 60.0,
        "total_energy_j": total_energy_j,
        "total_energy_kwh": total_energy_kwh,
    }


def subsystem_power_energy_from_class2_inputs(
    class_2_sizing_inputs,
    fuselage_length_m: Optional[float] = None,
    cabin_volume_m3: Optional[float] = None,
    cabin_fill_fraction: float = 0.5,
    phase_names=("climb", "cruise", "ifr"),
    fuel_system_phases=("ifr",),
) -> dict:
    """
    Wrapper around `subsystem_power_energy_from_mission(...)` that
    extracts geometry and mission data from `class_2_sizing_inputs`.

    Required keys in `class_2_sizing_inputs`
    ----------------------------------------
    - `mission`
    - `wing["S_m2"]`
    - `engine["N_engines"]`
    - `fuselage["b_f_m"]`
    - `fuselage["h_f_m"]`

    Fuselage length priority
    ------------------------
    1. explicit `fuselage_length_m` argument
    2. `fuselage["l_f_m"]`, `fuselage["l_fuselage_m"]`, `fuselage["length_m"]`
    3. inferred from `fuselage["l_t_m"] / tail["ht_arm_fraction"]`
    4. inferred from `fuselage["l_t_m"] / tail["vt_arm_fraction"]`

    Cabin volume priority
    ---------------------
    1. explicit `cabin_volume_m3` argument
    2. `fuselage["V_cabin_m3"]`, `fuselage["cabin_volume_m3"]`
    3. estimated as `cabin_fill_fraction * l_fuselage * b_f * h_f`
    """
    mission = class_2_sizing_inputs["mission"]
    wing = class_2_sizing_inputs["wing"]
    fuselage = class_2_sizing_inputs["fuselage"]
    engine = class_2_sizing_inputs["engine"]
    tail = class_2_sizing_inputs.get("tail", {})

    wing_area_m2 = float(wing["S_m2"])
    n_engines = int(engine["N_engines"])
    b_f_m = float(fuselage["b_f_m"])
    h_f_m = float(fuselage["h_f_m"])

    if fuselage_length_m is None:
        fuselage_length_m = (
            fuselage.get("l_f_m")
            or fuselage.get("l_fuselage_m")
            or fuselage.get("length_m")
            or tail.get("l_f_m")
            or tail.get("fuselage_length_m")
        )

    if fuselage_length_m is None:
        l_t_m = fuselage.get("l_t_m")
        ht_arm_fraction = tail.get("ht_arm_fraction")
        vt_arm_fraction = tail.get("vt_arm_fraction")

        if l_t_m is not None and ht_arm_fraction not in (None, 0):
            fuselage_length_m = float(l_t_m) / float(ht_arm_fraction)
        elif l_t_m is not None and vt_arm_fraction not in (None, 0):
            fuselage_length_m = float(l_t_m) / float(vt_arm_fraction)

    if fuselage_length_m is None:
        raise KeyError(
            "Could not determine fuselage length from class_2_sizing_inputs. "
            "Pass fuselage_length_m explicitly or add fuselage/tail length data."
        )

    if cabin_volume_m3 is None:
        cabin_volume_m3 = fuselage.get("V_cabin_m3") or fuselage.get("cabin_volume_m3")

    if cabin_volume_m3 is None:
        cabin_volume_m3 = float(cabin_fill_fraction) * float(fuselage_length_m) * b_f_m * h_f_m

    out = subsystem_power_energy_from_mission(
        mission=mission,
        fuselage_length_m=float(fuselage_length_m),
        wing_area_m2=wing_area_m2,
        cabin_volume_m3=float(cabin_volume_m3),
        n_engines=n_engines,
        phase_names=phase_names,
        fuel_system_phases=fuel_system_phases,
    )

    out["geometry_used"] = {
        "fuselage_length_m": float(fuselage_length_m),
        "wing_area_m2": wing_area_m2,
        "cabin_volume_m3": float(cabin_volume_m3),
        "n_engines": n_engines,
        "b_f_m": b_f_m,
        "h_f_m": h_f_m,
        "cabin_fill_fraction": float(cabin_fill_fraction),
    }
    return out


def installed_system_weights_from_class2_inputs(
    class_2_sizing_inputs,
    n_flight_crew: int = 2,
    n_passengers: int = 19,
    cabin_fill_fraction: float = 0.5,
    passenger_compartment_fraction: float = 0.5,
    v_max_mach: Optional[float] = None,
    engine_diameter_m: Optional[float] = None,
) -> dict:
    """
    Estimate installed systems mass from the class-2 sizing dictionary.

    Returns both the total weight and a breakdown for:
    - electrical
    - avionics
    - APU
    - instruments
    - air conditioning
    - ice protection
    - furnishings
    - galley / entertainment furnishings
    """
    import class_2_systems as cs

    inputs = class_2_sizing_inputs
    common = cs.derive_system_context_from_inputs(
        inputs,
        overrides={
            "n_flight_crew": int(n_flight_crew),
            "n_passengers": int(n_passengers),
        },
    )

    mission = inputs.get("mission", [])
    wing = inputs["wing"]
    fuselage = inputs["fuselage"]
    engine = inputs["engine"]
    constraint_inputs = inputs.get("constraint_analysis_inputs", {})

    fuselage_length_m = float(common["fuselage_length_m"])
    fuselage_width_m = float(common["fuselage_width_m"])
    fuselage_depth_m = float(common["fuselage_depth_m"])
    n_engines = int(engine["N_engines"])

    if v_max_mach is None:
        raw_v_max_mach = constraint_inputs.get("v_max_mach") or inputs.get("v_max_mach")
        if raw_v_max_mach is not None:
            v_max_mach = float(raw_v_max_mach)
        else:
            common_v_max_mach = common.get("v_max_mach")
            if common_v_max_mach is not None and float(common_v_max_mach) <= 2.0:
                v_max_mach = float(common_v_max_mach)
    if v_max_mach is None:
        cruise_phase = next(
            (ph for ph in mission if str(ph.get("phase", "")).lower() == "cruise"),
            {},
        )
        cruise_speed = cruise_phase.get("cruise_speed") or constraint_inputs.get("cruise_speed")
        if cruise_speed is None:
            raise KeyError("Could not determine v_max_mach from inputs or cruise phase")
        v_max_mach = float(cruise_speed) / 340.0
    v_max_mach = float(v_max_mach)

    if common.get("cabin_volume_m3") is None:
        cabin_volume_m3 = (
            float(cabin_fill_fraction) * fuselage_length_m * fuselage_width_m * fuselage_depth_m
        )
    else:
        cabin_volume_m3 = float(common["cabin_volume_m3"])

    if common.get("passenger_compartment_length_m") is None:
        passenger_compartment_length_m = (
            float(passenger_compartment_fraction) * fuselage_length_m
        )
    else:
        passenger_compartment_length_m = float(common["passenger_compartment_length_m"])

    wing_mount_flag = wing.get("engines_wing_mounted")
    fuselage_mount_flag = fuselage.get("fuselage_mounted_engines")
    n_wing_engines = n_engines if wing_mount_flag else 0
    n_fuselage_engines = n_engines if fuselage_mount_flag else 0

    if engine_diameter_m is None:
        engine_diameter_m = (
            inputs.get("engine_diameter_m")
            or engine.get("diameter_m")
            or common.get("engine_diameter_m")
        )
    if engine_diameter_m is None:
        engine_diameter_m = 0.35 * fuselage_width_m
    engine_diameter_m = float(engine_diameter_m)

    design_range_m = common.get("design_range_m")
    if design_range_m is None:
        cruise_phase = next(
            (ph for ph in mission if str(ph.get("phase", "")).lower() == "cruise"),
            {},
        )
        design_range_m = cruise_phase.get("range")
    if design_range_m is None:
        raise KeyError("Could not determine design_range_m from inputs or cruise phase")
    design_range_m = float(design_range_m)

    quarter_chord_sweep_deg = (
        constraint_inputs.get("Quarter chord sweep")
        or wing.get("sweep_quarter_chord_deg")
        or wing.get("sweep_half_chord_deg")
    )
    if quarter_chord_sweep_deg is None:
        raise KeyError("Could not determine quarter-chord sweep for ice-protection sizing")
    quarter_chord_sweep_deg = float(quarter_chord_sweep_deg)

    avionics_weight = cs.avionics_system_weight_kg(
        design_range_m,
        int(n_flight_crew),
        fuselage_length_m,
        fuselage_width_m,
    )

    breakdown_kg = {
        "electrical_system_weight_kg": cs.electrical_system_weight_kg(
            fuselage_length_m,
            fuselage_width_m,
            n_engines,
            int(n_passengers),
            int(n_flight_crew),
        ),
        "avionics_system_weight_kg": avionics_weight,
        "auxiliary_power_unit_weight_kg": cs.auxiliary_power_unit_weight_kg(
            fuselage_length_m,
            fuselage_width_m,
            int(n_passengers),
        ),
        "instruments_system_weight_kg": cs.instruments_system_weight_kg(
            fuselage_length_m,
            fuselage_width_m,
            v_max_mach,
            int(n_flight_crew),
            n_wing_engines=n_wing_engines,
            n_fuselage_engines=n_fuselage_engines,
        ),
        "air_conditioning_system_weight_kg": cs.air_conditioning_system_weight_kg(
            fuselage_length_m,
            fuselage_width_m,
            fuselage_depth_m,
            int(n_passengers),
            v_max_mach,
            avionics_weight,
        ),
        "ice_protection_system_weight_kg": cs.ice_protection_system_weight_kg(
            float(wing["b_m"]),
            quarter_chord_sweep_deg,
            n_engines,
            engine_diameter_m,
            fuselage_width_m,
        ),
        # Keep the Mohan furnishing estimate and omit the general FLOPS furnishing term.
        "furnishings_weight_kg": 0.0,
        "galley_entertainment_furnishing_weight_mohan_kg": (
            cs.galley_entertainment_furnishing_weight_mohan_kg(
                int(n_flight_crew),
                int(n_passengers),
                cabin_volume_m3,
            )
        ),
    }

    return {
        "total_weight_kg": sum(breakdown_kg.values()),
        "weight_breakdown_kg": breakdown_kg,
        "derived_inputs": {
            "fuselage_length_m": fuselage_length_m,
            "fuselage_width_m": fuselage_width_m,
            "fuselage_depth_m": fuselage_depth_m,
            "cabin_volume_m3": cabin_volume_m3,
            "passenger_compartment_length_m": passenger_compartment_length_m,
            "design_range_m": design_range_m,
            "v_max_mach": v_max_mach,
            "n_engines": n_engines,
            "n_wing_engines": n_wing_engines,
            "n_fuselage_engines": n_fuselage_engines,
            "engine_diameter_m": engine_diameter_m,
            "quarter_chord_sweep_deg": quarter_chord_sweep_deg,
        },
    }


def display_class1_convergence_tables(
    *,
    mtom_kg: float,
    oe_kg: float,
    battery_mass_kg: float,
    e0_total_j: float,
    fuel_mass_kg: float,
    iterations: int,
    error_kg: float,
    history,
    e0_fuel_j=None,
) -> dict:
    """
    Build and display notebook-friendly Class I summary and convergence tables.

    Returns
    -------
    dict
        Contains ``summary_df`` and ``history_df`` pandas DataFrames.
    """
    import pandas as pd
    from IPython.display import display

    summary_rows = [
        {
            "Parameter": "MTOM",
            "Value": float(mtom_kg),
            "Units": "kg",
            "Notes": "Final converged Class I MTOM",
        },
        {
            "Parameter": "OE",
            "Value": float(oe_kg),
            "Units": "kg",
            "Notes": "Final converged operating empty mass",
        },
        {
            "Parameter": "Battery mass",
            "Value": float(battery_mass_kg),
            "Units": "kg",
            "Notes": "Final converged battery mass",
        },
        {
            "Parameter": "Mission E0 total",
            "Value": float(e0_total_j),
            "Units": "J",
            "Notes": "Final onboard mission energy",
        },
        {
            "Parameter": "Mission E0 total",
            "Value": float(e0_total_j) / 1e6,
            "Units": "MJ",
            "Notes": "Final onboard mission energy",
        },
        {
            "Parameter": "Fuel mass",
            "Value": float(fuel_mass_kg),
            "Units": "kg",
            "Notes": "Total fuel mass",
        },
        {
            "Parameter": "Iterations",
            "Value": int(iterations),
            "Units": "-",
            "Notes": "Number of iterations",
        },
        {
            "Parameter": "Final error",
            "Value": float(error_kg),
            "Units": "kg",
            "Notes": "Final MTOM residual",
        },
    ]
    if e0_fuel_j is not None:
        summary_rows.append(
            {
                "Parameter": "Mission E0 fuel",
                "Value": float(e0_fuel_j),
                "Units": "J",
                "Notes": "Fuel-backed mission energy",
            }
        )
        summary_rows.append(
            {
                "Parameter": "Mission E0 fuel",
                "Value": float(e0_fuel_j) / 1e6,
                "Units": "MJ",
                "Notes": "Fuel-backed mission energy",
            }
        )

    summary_df = pd.DataFrame(summary_rows, columns=["Parameter", "Value", "Units", "Notes"])

    history_df = pd.DataFrame(list(history or []))
    if not history_df.empty:
        preferred_columns = [
            "iter",
            "MTOM_guess",
            "OE",
            "E0_total_J",
            "M_batt",
            "fuel_mass_kg",
            "MTOM_new",
            "error",
        ]
        ordered_columns = [col for col in preferred_columns if col in history_df.columns]
        ordered_columns += [col for col in history_df.columns if col not in ordered_columns]
        history_df = history_df[ordered_columns]

        history_df = history_df.rename(
            columns={
                "iter": "Iter",
                "MTOM_guess": "MTOM guess [kg]",
                "OE": "OE [kg]",
                "E0_total_J": "E0_total [J]",
                "M_batt": "Battery [kg]",
                "fuel_mass_kg": "Fuel [kg]",
                "MTOM_new": "MTOM new [kg]",
                "error": "Error [kg]",
            }
        )

    display(summary_df)
    display(history_df)

    return {
        "summary_df": summary_df,
        "history_df": history_df,
    }


def display_class2_convergence_tables(class2_out: dict) -> dict:
    """
    Build and display notebook-friendly Class II summary and convergence tables.

    Parameters
    ----------
    class2_out : dict
        Output dictionary returned by the Class II converger.

    Returns
    -------
    dict
        Contains ``summary_df`` and ``history_df`` pandas DataFrames.
    """
    import math
    import pandas as pd
    from IPython.display import display

    out = dict(class2_out or {})
    history = list(out.get("history") or [])
    struct_breakdown = dict(out.get("struct_mass_breakdown_kg") or {})
    tail_out = dict(out.get("tail_out") or {})
    geometry = dict(out.get("geometry") or {})
    mass_accounting = dict(out.get("mass_accounting_kg") or {})
    system_energy_breakdown = dict(out.get("system_energy_breakdown") or {})
    last_history = history[-1] if history else {}

    def _finite_float(value):
        try:
            if value is None or isinstance(value, bool):
                return None
            value = float(value)
            return value if math.isfinite(value) else None
        except (TypeError, ValueError):
            return None

    summary_rows = []

    def _add(parameter, value, units="", notes=""):
        value = _finite_float(value)
        if value is None:
            return
        summary_rows.append(
            {
                "Parameter": parameter,
                "Value": value,
                "Units": units,
                "Notes": notes,
            }
        )

    _add("MTOM", out.get("MTOM"), "kg", "Final converged Class II MTOM")
    _add("OE", out.get("OE"), "kg", "Airframe structure subtotal returned by the Class II loop")
    _add("Battery mass", out.get("M_batt"), "kg", "Final converged battery mass")
    _add("Mission E0 total", out.get("E0_total"), "J", "Final onboard mission energy")
    e0_total = _finite_float(out.get("E0_total"))
    if e0_total is not None:
        _add("Mission E0 total", e0_total / 1e6, "MJ", "Final onboard mission energy")
    _add("Fuel mass", out.get("fuel_mass_kg"), "kg", "Final fuel mass")
    _add("Iterations", out.get("iterations"), "-", "Number of iterations")
    _add("Final error", out.get("error"), "kg", "Final MTOM residual")

    _add("Turbo-prop mass", last_history.get("turbo_prop_mass"), "kg", "Final iteration propulsion breakdown")
    _add("Propeller mass", last_history.get("propeler_mass"), "kg", "Final iteration propulsion breakdown")
    _add("Fuel system mass", last_history.get("fuel_system_mass"), "kg", "Final iteration propulsion breakdown")
    _add("Motor mass", last_history.get("motor_mass"), "kg", "Final iteration propulsion breakdown")
    _add(
        "Motor controller mass",
        last_history.get("motor_controller_mass"),
        "kg",
        "Final iteration propulsion breakdown",
    )
    _add(
        "Motor power per motor",
        last_history.get("motor_power_per_motor"),
        "kW",
        "Final iteration propulsion breakdown",
    )
    _add(
        "Turboprop power",
        last_history.get("turboprop_power"),
        "kW",
        "Final iteration propulsion breakdown",
    )

    _add("Wing mass", struct_breakdown.get("wing"), "kg", "Structural mass breakdown")
    _add("Tail mass", struct_breakdown.get("tail"), "kg", "Structural mass breakdown")
    _add("Fuselage mass", struct_breakdown.get("fuselage"), "kg", "Structural mass breakdown")
    _add("Landing gear mass", struct_breakdown.get("landing_gear"), "kg", "Structural mass breakdown")
    _add("Nacelle mass", struct_breakdown.get("nacelle"), "kg", "Structural mass breakdown")

    _add("Fuselage length", tail_out.get("l_f_m"), "m", "Tail sizing output")
    _add("Horizontal tail arm", tail_out.get("L_ht_m"), "m", "Tail sizing output")
    _add("Vertical tail arm", tail_out.get("L_vt_m"), "m", "Tail sizing output")
    _add("Horizontal tail area", tail_out.get("S_ht_m2"), "m^2", "Tail sizing output")
    _add("Vertical tail area", tail_out.get("S_vt_m2"), "m^2", "Tail sizing output")

    _add("Wing area", geometry.get("S_m2"), "m^2", "Final geometry")
    _add("Wing span", geometry.get("b_m"), "m", "Final geometry")
    _add("Root chord", geometry.get("c_root"), "m", "Final geometry")
    _add("Tip chord", geometry.get("c_tip"), "m", "Final geometry")
    _add("Root thickness", geometry.get("t_root_m"), "m", "Final geometry")
    _add("Mean chord estimate", geometry.get("c_bar_w_m"), "m", "Final geometry")
    _add("Total tail area", geometry.get("S_tail_m2"), "m^2", "Final geometry")

    _add("Systems base mass", mass_accounting.get("systems_mass_kg"), "kg", "Base systems mass used in the MTOM loop")
    _add("Furnishings mass", mass_accounting.get("furnishings_mass_kg"), "kg", "Furnishings mass used in the MTOM loop")
    _add("Operator items", mass_accounting.get("operator_items_mass_kg"), "kg", "Operator items mass used in the MTOM loop")
    _add("Power distribution mass", mass_accounting.get("power_distribution_mass_kg"), "kg", "Power distribution mass used in the MTOM loop")
    _add(
        "Mechanical FCS mass",
        mass_accounting.get("mechanical_fcs_mass_kg"),
        "kg",
        "Computed diagnostic; currently netted out of the base systems mass in the MTOM loop",
    )
    _add("Inverter mass", mass_accounting.get("inverter_mass_kg"), "kg", "Inverter mass used in the MTOM loop")
    _add("Motor cooling mass", mass_accounting.get("motor_cooling_mass_kg"), "kg", "Motor cooling mass used in the MTOM loop")
    _add("Inverter cooling mass", mass_accounting.get("inverter_cooling_mass_kg"), "kg", "Inverter cooling mass used in the MTOM loop")
    _add("BTMS mass", mass_accounting.get("btms_mass_kg"), "kg", "Battery thermal management mass used in the MTOM loop")

    systems_energy_j = _finite_float(system_energy_breakdown.get("total_energy_j"))
    if systems_energy_j is not None:
        _add("Systems electrical offtake", systems_energy_j, "J", "Electrical systems energy added to battery sizing")
        _add("Systems electrical offtake", systems_energy_j / 1e6, "MJ", "Electrical systems energy added to battery sizing")

    summary_df = pd.DataFrame(summary_rows, columns=["Parameter", "Value", "Units", "Notes"])

    history_df = pd.DataFrame(history)
    if not history_df.empty:
        preferred_columns = [
            "iter",
            "MTOM_guess",
            "OE",
            "E0_total_J",
            "M_batt",
            "fuel_mass_kg",
            "MTOM_new",
            "error",
            "turbo_prop_mass",
            "propeler_mass",
            "fuel_system_mass",
            "motor_mass",
            "motor_controller_mass",
            "motor_power_per_motor",
            "turboprop_power",
        ]
        ordered_columns = [col for col in preferred_columns if col in history_df.columns]
        ordered_columns += [col for col in history_df.columns if col not in ordered_columns]
        history_df = history_df[ordered_columns]

        history_df = history_df.rename(
            columns={
                "iter": "Iter",
                "MTOM_guess": "MTOM guess [kg]",
                "OE": "OE [kg]",
                "E0_total_J": "E0_total [J]",
                "M_batt": "Battery [kg]",
                "fuel_mass_kg": "Fuel [kg]",
                "MTOM_new": "MTOM new [kg]",
                "error": "Error [kg]",
                "turbo_prop_mass": "Turbo-prop [kg]",
                "propeler_mass": "Propeller [kg]",
                "fuel_system_mass": "Fuel system [kg]",
                "motor_mass": "Motor [kg]",
                "motor_controller_mass": "Motor controller [kg]",
                "motor_power_per_motor": "Motor power / motor [kW]",
                "turboprop_power": "Turboprop power [kW]",
            }
        )

    display(summary_df)
    display(history_df)

    return {
        "summary_df": summary_df,
        "history_df": history_df,
    }


def _deprecated_build_e19_appendix_summary(
    inputs_class_1,
    class_2_sizing_inputs,
    class_2_out,
    *,
    class_1_out=None,
    tail_out=None,
) -> dict:
    """
    Build appendix-style summary tables for the E19 worked example.

    Returns
    -------
    dict with keys:
      - executive_summary_md
      - tables
      - table_order
      - derived
    """
    import copy
    import pandas as pd
    import class_1_sizing
    import class_2_airframe_structure as c2s
    import class_2_prop_parallel_hybrid as c2prop

    if class_1_out is None:
        class_1_out = class_1_sizing.converge_mtom_electric_E19(inputs_class_1)

    def _phase_lookup(mission, phase_name):
        return next(
            (ph for ph in mission if str(ph.get("phase", "")).lower() == str(phase_name).lower()),
            {},
        )

    def _scalar_table(rows):
        return pd.DataFrame(rows, columns=["Parameter", "Value", "Units", "Notes"])

    def _phase_energy_table(phase_results):
        rows = []
        total_bat = 0.0
        total_fuel = 0.0
        total_energy = 0.0
        total_fuel_mass = 0.0
        for ph in phase_results:
            phase_name = str(ph.get("phase", "")).lower()
            mode = ph.get("mode", "n/a")
            range_m = float(ph.get("range_m", 0.0) or 0.0)
            e_total = float(ph.get("E0_total_J", 0.0) or 0.0)
            e_bat = float(ph.get("E0_bat_J", 0.0) or 0.0)
            e_fuel = float(ph.get("E0_fuel_J", 0.0) or 0.0)
            fuel_mass = float(ph.get("fuel_mass_kg", 0.0) or 0.0)
            total_bat += e_bat
            total_fuel += e_fuel
            total_energy += e_total
            total_fuel_mass += fuel_mass
            rows.append(
                {
                    "Phase": phase_name,
                    "Mode": mode,
                    "Range [km]": round(range_m / 1000.0, 3),
                    "L/D": None if ph.get("L_D") is None else round(float(ph["L_D"]), 3),
                    "Phi": None if ph.get("Phi") is None else round(float(ph["Phi"]), 4),
                    "Battery energy [MJ]": round(e_bat / 1e6, 3),
                    "Fuel energy [MJ]": round(e_fuel / 1e6, 3),
                    "Total energy [MJ]": round(e_total / 1e6, 3),
                    "Fuel mass [kg]": round(fuel_mass, 3),
                }
            )
        rows.append(
            {
                "Phase": "total",
                "Mode": "",
                "Range [km]": round(sum(float(ph.get("range_m", 0.0) or 0.0) for ph in phase_results) / 1000.0, 3),
                "L/D": None,
                "Phi": None,
                "Battery energy [MJ]": round(total_bat / 1e6, 3),
                "Fuel energy [MJ]": round(total_fuel / 1e6, 3),
                "Total energy [MJ]": round(total_energy / 1e6, 3),
                "Fuel mass [kg]": round(total_fuel_mass, 3),
            }
        )
        return pd.DataFrame(rows)

    def _class1_mass_table(out):
        phase_fuel = sum(float(ph.get("fuel_mass_kg", 0.0) or 0.0) for ph in out["phase_results"])
        rows = [
            ("Payload", round(float(inputs_class_1["payload"]), 3), "kg", "Design payload"),
            ("Battery mass", round(float(out["M_batt"]), 3), "kg", "Class I battery mass"),
            ("Fuel mass", round(phase_fuel, 3), "kg", "Reserve / hybrid fuel mass"),
            ("Operating empty mass", round(float(out["OE"]), 3), "kg", "Class I empty mass estimate"),
            ("MTOM", round(float(out["MTOM"]), 3), "kg", "Converged Class I MTOM"),
            ("Iterations", int(out["iterations"]), "-", "Convergence loop count"),
            ("Final error", round(float(out["error"]), 3), "kg", "Convergence tolerance residual"),
        ]
        return _scalar_table(rows)

    def _airframe_breakdown(inp):
        working = copy.deepcopy(inp)
        wing = working["wing"]
        tail = working["tail"]
        fuselage = working["fuselage"]
        landing_gear = working["landing_gear"]
        nacelle = working["nacelle"]
        config = working["configuration"]

        w_s_sel = float(wing["w_s_sel"])
        W_G = float(wing["W_G_kg"])
        S_m2 = W_G / w_s_sel
        b_wing = math.sqrt(float(wing["A"]) * S_m2)
        lam = float(wing["lam"])
        c_root = (2.0 * S_m2) / (b_wing * (1.0 + lam))
        c_tip = lam * c_root
        t_root = float(wing["t_c_root"]) * c_root

        local_tail_out = c2s.tail_areas_from_volume_coefficients(
            MTOM_kg=W_G,
            S_w_m2=S_m2,
            b_w_m=b_wing,
            c_bar_w_m=0.5 * (c_root + c_tip),
            c_ht=tail["c_ht"],
            c_vt=tail["c_vt"],
            a_fus=tail["a_fus"],
            c_fus=tail["c_fus"],
            ht_arm_fraction=tail["ht_arm_fraction"],
            vt_arm_fraction=tail["vt_arm_fraction"],
        )
        S_tail_total = local_tail_out["S_ht_m2"] + local_tail_out["S_vt_m2"]

        wing_mass = c2s.wing_mass_eq22(
            W_G,
            b_wing,
            S_m2,
            t_root,
            float(wing["sweep_half_chord_deg"]),
            float(wing["n_ult"]),
            category=wing["category"],
            engines_wing_mounted=int(wing["engines_wing_mounted"]),
            main_gear_attached_to_wing=bool(wing["main_gear_attached_to_wing"]),
        )
        tail_mass = c2s.tail_mass_light_eq23(S_tail_total, float(wing["n_ult"]))
        fuselage_mass = c2s.fuselage_mass_eq27(
            float(fuselage["V_D_mps"]),
            float(fuselage["l_t_m"]),
            float(fuselage["b_f_m"]),
            float(fuselage["h_f_m"]),
            float(fuselage["S_G_m2"]),
            k_wf=float(fuselage.get("k_wf", 0.23)),
            pressurized=bool(fuselage["pressurized"]),
            fuselage_mounted_engines=bool(fuselage["fuselage_mounted_engines"]),
            main_gear_attached_to_fuselage=bool(fuselage["main_gear_attached_to_fuselage"]),
            freighter=bool(fuselage["freighter"]),
            no_attachment_structure_or_gear_bay=bool(
                fuselage.get("no_attachment_structure_or_gear_bay", False)
            ),
        )
        landing_gear_nose = c2s.landing_gear_mass_eq28(
            float(landing_gear["W_to_kg"]),
            gear="nose",
            wing=landing_gear["wing"],
            retractable=bool(landing_gear["retractable"]),
        )
        landing_gear_main = c2s.landing_gear_mass_eq28(
            float(landing_gear["W_to_kg"]),
            gear="main",
            wing=landing_gear["wing"],
            retractable=bool(landing_gear["retractable"]),
        )
        if str(config["nacelle_type"]).lower() == "jet":
            nacelle_mass = c2s.nacelle_mass_jet_eq30(float(working["engine"]["T_to_N"]))
        else:
            nacelle_mass = c2s.nacelle_mass_prop_eq29(float(nacelle["ESHP_to_hp"]))

        breakdown = {
            "Wing": wing_mass,
            "Tail": tail_mass,
            "Fuselage": fuselage_mass,
            "Landing gear": landing_gear_nose + landing_gear_main,
            "Nacelle / pylons": nacelle_mass,
        }
        return {
            "mass_breakdown_kg": breakdown,
            "total_mass_kg": sum(breakdown.values()),
            "geometry": {
                "wing_area_m2": S_m2,
                "wing_span_m": b_wing,
                "c_root_m": c_root,
                "c_tip_m": c_tip,
                "t_root_m": t_root,
                "fuselage_length_m": local_tail_out["l_f_m"],
                "tail_area_total_m2": S_tail_total,
                "tail_area_horizontal_m2": local_tail_out["S_ht_m2"],
                "tail_area_vertical_m2": local_tail_out["S_vt_m2"],
            },
        }

    def _propulsion_breakdown(inp, out):
        turboprop_installed_mass = float(out.get("turboprop_installed_mass", 0.0) or 0.0)
        propeller_mass = float(out.get("propeller_mass", 0.0) or 0.0)
        fuel_system_mass = float(out.get("fuel_system_mass", 0.0) or 0.0)
        motor_controller_mass = float(out.get("motor_controller_mass", 0.0) or 0.0)
        propulsion_mass = float(out.get("propulsion_mass", 0.0) or 0.0)

        known_components = (
            turboprop_installed_mass
            + propeller_mass
            + fuel_system_mass
            + motor_controller_mass
        )
        electric_motors_mass = max(0.0, propulsion_mass - known_components)

        mass_breakdown_kg = {
            "Turboprops (installed)": turboprop_installed_mass,
            "Propellers": propeller_mass,
            "Fuel system": fuel_system_mass,
            "Electric motors": electric_motors_mass,
            "Motor controllers": motor_controller_mass,
        }
        rows = []
        for name, mass in mass_breakdown_kg.items():
            rows.append(
                {
                    "Component": name,
                    "Mass [kg]": round(float(mass), 3),
                    "Included in current MTOM loop": True,
                }
            )
        return {
            "table": pd.DataFrame(rows),
            "full_total_kg": sum(mass_breakdown_kg.values()),
            "included_total_kg": propulsion_mass,
        }

    mission = class_2_sizing_inputs["mission"]
    constraint_inputs = class_2_sizing_inputs["constraint_analysis_inputs"]
    climb_phase = _phase_lookup(mission, "climb")
    cruise_phase = _phase_lookup(mission, "cruise")
    ifr_phase = _phase_lookup(mission, "ifr")

    airframe = _airframe_breakdown(class_2_sizing_inputs)
    systems = installed_system_weights_from_class2_inputs(class_2_sizing_inputs)
    propulsion = _propulsion_breakdown(class_2_sizing_inputs, class_2_out)
    class2_fuel_mass_in_loop = max(
        0.0,
        float(class_2_out["MTOM"])
        - float(airframe["total_mass_kg"])
        - float(class_2_out["M_batt"])
        - float(class_2_sizing_inputs["payload"])
        - float(propulsion["included_total_kg"])
        - float(systems["total_weight_kg"]),
    )

    selected_wing_loading_n_per_m2 = (
        airframe["geometry"]["wing_area_m2"] and class_2_out["MTOM"] * class_2_sizing_inputs.get("g", 9.81) / airframe["geometry"]["wing_area_m2"]
    )
    selected_power_loading_w_per_n = float(class_2_sizing_inputs["p_w_sel"])

    problem_statement = _scalar_table(
        [
            ("Passengers", 19, "-", "E19 commuter configuration"),
            ("Payload", round(float(class_2_sizing_inputs["payload"]), 3), "kg", "19 passengers including luggage"),
            ("Electric mission range", round(float(cruise_phase.get("range", 0.0)) / 1000.0, 3), "km", "Cruise segment used for battery sizing"),
            ("IFR reserve range", round(float(ifr_phase.get("range", 0.0)) / 1000.0, 3), "km", "Reserve / extended-range segment"),
            ("Take-off field length", round(float(_phase_lookup(mission, "takeoff").get("tofl", 0.0)), 3), "m", "Mission take-off requirement"),
            ("Service ceiling", round(float(climb_phase.get("ceiling_alt", 0.0)), 3), "m", "Mission ceiling input"),
        ]
    )

    requirements_analysis = _scalar_table(
        [
            ("MTOM limit", round(float(climb_phase.get("MTOM", 0.0)), 3), "kg", "Certification / requirement limit used in mission"),
            ("Selected propulsive power loading", round(selected_power_loading_w_per_n, 4), "W/N", "Design-point input"),
            ("Selected wing loading", round(float(selected_wing_loading_n_per_m2), 3), "N/m²", "Implied by converged Class II MTOM and wing area"),
            ("Climb rate requirement", round(float(constraint_inputs.get("rate_of_climb", 0.0)), 3), "m/s", "Constraint-analysis input"),
            ("Climb gradient requirement", round(float(constraint_inputs.get("climb_gradient", 0.0)) * 100.0, 3), "%", "Constraint-analysis input"),
            ("Stall speed", round(float(constraint_inputs.get("stall_speed", 0.0)), 3), "m/s", "Constraint-analysis input"),
        ]
    )

    configuration_selection = _scalar_table(
        [
            ("Powertrain architecture", class_2_sizing_inputs["powertrain_type"], "-", "Parallel hybrid"),
            ("Number of engines", int(class_2_sizing_inputs["engine"]["N_engines"]), "-", "Twin-engine configuration"),
            ("Fuel tanks", int(class_2_sizing_inputs["engine"]["N_FuelTanks"]), "-", "Fuel-system sizing input"),
            ("Aspect ratio", round(float(class_2_sizing_inputs["wing"]["A"]), 3), "-", "Wing planform assumption"),
            ("Taper ratio", round(float(class_2_sizing_inputs["wing"]["lam"]), 3), "-", "Wing planform assumption"),
            ("Wing sweep", round(float(class_2_sizing_inputs["wing"]["sweep_half_chord_deg"]), 3), "deg", "Half-chord sweep"),
            ("Engine mounting", "wing-mounted" if class_2_sizing_inputs["wing"]["engines_wing_mounted"] else "fuselage-mounted", "-", "From Class II inputs"),
            ("Nacelle type", class_2_sizing_inputs["configuration"]["nacelle_type"], "-", "Class II configuration"),
        ]
    )

    aerodynamic_polar = _scalar_table(
        [
            ("CD0", round(float(constraint_inputs.get("CD_0", 0.0)), 5), "-", "Constraint-analysis drag polar"),
            ("Oswald efficiency", round(float(constraint_inputs.get("oswald efficiency", 0.0)), 3), "-", "Constraint-analysis input"),
            ("CLmax (clean)", round(float(constraint_inputs.get("CL_max", 0.0)), 3), "-", "Constraint-analysis input"),
            ("CLmax (TO)", round(float(constraint_inputs.get("CL_max_to", 0.0)), 3), "-", "Constraint-analysis input"),
            ("Cruise L/D", round(float(cruise_phase.get("l_d", 0.0)), 3), "-", "Mission cruise assumption"),
            ("Climb L/D", round(float(climb_phase.get("l_d", 0.0)), 3), "-", "Mission climb assumption"),
            ("IFR L/D", round(float(ifr_phase.get("l_d", 0.0)), 3), "-", "Mission reserve assumption"),
        ]
    )

    powertrain_wing_sizing = _scalar_table(
        [
            ("Selected propulsive power loading", round(selected_power_loading_w_per_n, 4), "W/N", "Notebook design-point choice"),
            ("Selected propulsive W/P", round(1.0 / selected_power_loading_w_per_n, 4), "N/W", "Inverse of selected power loading"),
            ("Converged wing area", round(float(airframe["geometry"]["wing_area_m2"]), 3), "m²", "Recomputed in Class II loop"),
            ("Converged wing span", round(float(airframe["geometry"]["wing_span_m"]), 3), "m", "Based on AR and wing area"),
            ("Converged wing loading", round(float(selected_wing_loading_n_per_m2), 3), "N/m²", "Class II converged point"),
            ("Installed EM power", round(float(class_2_out["p_rated_em"]) / 1000.0, 3), "kW", "Current hybrid loop output"),
            ("Installed TE power", round(float(class_2_out["p_rated_te"]) / 1000.0, 3), "kW", "Current hybrid loop output"),
        ]
    )

    class1_energy = _phase_energy_table(class_1_out["phase_results"])
    class1_mass = _class1_mass_table(class_1_out)
    class2_energy = _phase_energy_table(class_2_out["phase_results"])

    class2_mass_rows = []
    for name, mass in airframe["mass_breakdown_kg"].items():
        class2_mass_rows.append({"Group": "Airframe", "Component": name, "Mass [kg]": round(float(mass), 3), "Included in MTOM loop": True})
    for _, row in propulsion["table"].iterrows():
        class2_mass_rows.append({"Group": "Propulsion", "Component": row["Component"], "Mass [kg]": row["Mass [kg]"], "Included in MTOM loop": row["Included in current MTOM loop"]})
    for name, mass in systems["weight_breakdown_kg"].items():
        class2_mass_rows.append({"Group": "Systems", "Component": name, "Mass [kg]": round(float(mass), 3), "Included in MTOM loop": True})
    class2_mass_rows.extend(
        [
            {"Group": "Mission masses", "Component": "Battery", "Mass [kg]": round(float(class_2_out["M_batt"]), 3), "Included in MTOM loop": True},
            {"Group": "Mission masses", "Component": "Fuel", "Mass [kg]": round(float(class2_fuel_mass_in_loop), 3), "Included in MTOM loop": True},
            {"Group": "Mission masses", "Component": "Payload", "Mass [kg]": round(float(class_2_sizing_inputs["payload"]), 3), "Included in MTOM loop": True},
            {"Group": "Mission masses", "Component": "MTOM", "Mass [kg]": round(float(class_2_out["MTOM"]), 3), "Included in MTOM loop": True},
        ]
    )
    class2_mass = pd.DataFrame(class2_mass_rows)

    final_summary = _scalar_table(
        [
            ("Class I MTOM", round(float(class_1_out["MTOM"]), 3), "kg", "Initial sizing loop"),
            ("Class II MTOM", round(float(class_2_out["MTOM"]), 3), "kg", "Structural / hybrid loop"),
            ("Payload", round(float(class_2_sizing_inputs["payload"]), 3), "kg", "Design payload"),
            ("Battery mass", round(float(class_2_out["M_batt"]), 3), "kg", "Class II converged battery mass"),
            ("Fuel mass", round(float(class2_fuel_mass_in_loop), 3), "kg", "Fuel included in the Class II MTOM loop"),
            ("Systems mass", round(float(systems["total_weight_kg"]), 3), "kg", "Installed systems wrapper"),
            ("Airframe structure mass", round(float(airframe["total_mass_kg"]), 3), "kg", "Wing + tail + fuselage + landing gear + nacelle"),
            ("Propulsion mass included in MTOM loop", round(float(propulsion["included_total_kg"]), 3), "kg", "Includes turboprops, propellers, fuel system, EMs, and controllers"),
            ("Cruise range", round(float(cruise_phase.get("range", 0.0)) / 1000.0, 3), "km", "Battery-backed mission cruise"),
            ("IFR reserve range", round(float(ifr_phase.get("range", 0.0)) / 1000.0, 3), "km", "Fuel-backed reserve"),
            ("Cruise L/D", round(float(cruise_phase.get("l_d", 0.0)), 3), "-", "Cruise mission input"),
            ("Installed EM power", round(float(class_2_out["p_rated_em"]) / 1000.0, 3), "kW", "Current hybrid loop output"),
            ("Installed TE power", round(float(class_2_out["p_rated_te"]) / 1000.0, 3), "kW", "Current hybrid loop output"),
        ]
    )

    class2_structure_plus_systems = airframe["total_mass_kg"] + systems["total_weight_kg"]
    executive_summary_md = (
        f"### Executive Summary\n"
        f"The E19 worked example currently converges to a **Class I MTOM of {class_1_out['MTOM']:.1f} kg** "
        f"and a **Class II MTOM of {class_2_out['MTOM']:.1f} kg**. "
        f"The Class II solution carries **{class_2_sizing_inputs['payload']:.1f} kg** of payload, "
        f"**{class_2_out['M_batt']:.1f} kg** of batteries, and **{class2_fuel_mass_in_loop:.1f} kg** of fuel.\n\n"
        f"The current converged Class II breakdown contains **{airframe['total_mass_kg']:.1f} kg** of airframe structure, "
        f"**{systems['total_weight_kg']:.1f} kg** of systems, and **{propulsion['included_total_kg']:.1f} kg** of propulsion mass "
        f"as counted in the present MTOM loop. The selected design point implies a wing area of "
        f"**{airframe['geometry']['wing_area_m2']:.2f} m²**, a span of **{airframe['geometry']['wing_span_m']:.2f} m**, "
        f"and installed powers of **{class_2_out['p_rated_em']/1000.0:.1f} kW** electric plus "
        f"**{class_2_out['p_rated_te']/1000.0:.1f} kW** thermal.\n\n"
        f"The tables below mirror the Appendix A worked-example structure in the whitepaper: requirements, configuration, "
        f"aerodynamic assumptions, sizing choices, Class I energy and mass, Class II energy and mass, and a final top-level summary. "
        f"Because the current `converge_mtom_hybrid_struct` implementation reports `OE` as structural mass only, "
        f"the appendix tables separate **airframe**, **propulsion**, and **systems** explicitly."
    )

    tables = {
        "Problem Statement": problem_statement,
        "Step 1: Requirements Analysis": requirements_analysis,
        "Step 2: Configuration Selection": configuration_selection,
        "Step 3: Aerodynamic Polar": aerodynamic_polar,
        "Step 4: Powertrain and Wing Sizing": powertrain_wing_sizing,
        "Step 5: Energy Estimation (Class I)": class1_energy,
        "Step 6: Class I Mass Estimation": class1_mass,
        "Step 7: Energy Estimation (Class II)": class2_energy,
        "Step 8: Class II Mass Estimation": class2_mass,
        "Step 9: Final Aircraft Summary": final_summary,
    }

    table_order = list(tables.keys())

    return {
        "executive_summary_md": executive_summary_md,
        "tables": tables,
        "table_order": table_order,
        "derived": {
            "airframe": airframe,
            "systems": systems,
            "propulsion": propulsion,
            "class_1_out": class_1_out,
            "class_2_out": class_2_out,
            "tail_out": tail_out,
            "class2_structure_plus_systems_kg": class2_structure_plus_systems,
        },
    }


#
# Executive-summary generation now lives in executive_summary.py.
# Keep this thin wrapper so existing notebook calls to
# special_functions.build_e19_appendix_summary(...) continue to work.
#
def build_e19_appendix_summary(
    inputs_class_1,
    class_2_sizing_inputs,
    class_2_out,
    *,
    class_1_out=None,
    tail_out=None,
) -> dict:
    import executive_summary

    return executive_summary.build_e19_appendix_summary(
        inputs_class_1=inputs_class_1,
        class_2_sizing_inputs=class_2_sizing_inputs,
        class_2_out=class_2_out,
        class_1_out=class_1_out,
        tail_out=tail_out,
    )
