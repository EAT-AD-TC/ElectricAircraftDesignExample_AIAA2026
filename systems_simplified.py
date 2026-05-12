import math

FT2_PER_M2 = 10.763910416709722
LB_PER_KG = 2.20462262185
KG_PER_LB = 1.0 / LB_PER_KG
PSF_PER_PA = 0.020885434233150127
PA_PER_PSF = 1.0 / PSF_PER_PA

def compute_systems_electrical_power_E19(l_fuse,s_wing,V_cabin,N_eng, cruise_range, cruise_speed):
    p_lights=0.31*l_fuse # power demand in kW
    p_avionics_nom=0.02*l_fuse**1.55 # power demand in kW
    p_fuel_system= 2.88 * math.exp((0.0399 * l_fuse) / N_eng)  # power demand in kW
    cruise_time=cruise_range/cruise_speed

    total_power=p_lights+p_avionics_nom+p_fuel_system

    total_energy_j=total_power * 1000 * cruise_time # convert from kW to joules

    return {"total_energy_j": total_energy_j,
        "total_power_kw": total_power,
        "cruise_time_s": cruise_time,
        "p_lights_kw": p_lights,
        "p_avionics_kw": p_avionics_nom,
        "p_fuel_system_kw": p_fuel_system,}


def dive_dynamic_pressure_pa(delta, v_max_mach):
    """
    Estimate dive dynamic pressure from the FLOPS-style relation:

        QDIVE = 1481.35 * DELTA * VMAX^2

    where:
    - DELTA is the atmospheric pressure ratio [-]
    - VMAX is the maximum Mach number [-]

    Returns dive dynamic pressure in Pa.
    """
    delta_ratio = float(delta)
    mach = float(v_max_mach)

    if delta_ratio <= 0.0:
        raise ValueError("delta must be > 0")
    if mach <= 0.0:
        raise ValueError("v_max_mach must be > 0")

    q_dive_psf = 1481.35 * delta_ratio * mach**2
    return q_dive_psf * PA_PER_PSF


def flight_control_system_weight_kg(
    wing_reference_area_m2,
    design_gross_mass_kg,
    q_dive_pa=None,
    ultimate_load_factor=3.75,
    delta=None,
    v_max_mach=None,
):
    """
    Estimate flight-control system mass using the FLOPS-style WSC correlation.

    All inputs are SI:
    - wing_reference_area_m2: reference wing area [m^2]
    - design_gross_mass_kg: design gross mass [kg]
    - q_dive_pa: dive dynamic pressure [Pa]
    - ultimate_load_factor: structural ultimate load factor [-]
    - delta: atmospheric pressure ratio [-]
    - v_max_mach: maximum Mach number [-]

    Provide either:
    - q_dive_pa directly, or
    - delta and v_max_mach so the function can estimate QDIVE internally.

    Internally the correlation is evaluated in the published imperial units:
    - SW in ft^2
    - DG in lb
    - QDIVE in psf

    Returns flight-control system mass in kg.
    """
    sw_m2 = float(wing_reference_area_m2)
    dg_kg = float(design_gross_mass_kg)
    ulf = float(ultimate_load_factor)

    if sw_m2 <= 0.0:
        raise ValueError("wing_reference_area_m2 must be > 0")
    if dg_kg <= 0.0:
        raise ValueError("design_gross_mass_kg must be > 0")
    if ulf <= 0.0:
        raise ValueError("ultimate_load_factor must be > 0")

    using_q_dive = q_dive_pa is not None
    using_delta_mach = delta is not None or v_max_mach is not None

    if using_q_dive and using_delta_mach:
        raise ValueError(
            "Provide either q_dive_pa or delta/v_max_mach, not both"
        )
    if not using_q_dive and not using_delta_mach:
        raise ValueError(
            "Provide q_dive_pa directly or provide both delta and v_max_mach"
        )

    if using_q_dive:
        q_pa = float(q_dive_pa)
        if q_pa <= 0.0:
            raise ValueError("q_dive_pa must be > 0")
    else:
        if delta is None or v_max_mach is None:
            raise ValueError(
                "Both delta and v_max_mach are required when q_dive_pa is not provided"
            )
        q_pa = dive_dynamic_pressure_pa(delta, v_max_mach)

    sw_ft2 = sw_m2 * FT2_PER_M2
    dg_lb = dg_kg * LB_PER_KG
    q_dive_psf = q_pa * PSF_PER_PA

    wsc_lb = (
        0.404
        * sw_ft2**0.317
        * (dg_lb / 1000.0) ** 0.602
        * ulf**0.525
        * q_dive_psf**0.345
    )

    return wsc_lb * KG_PER_LB

def mechanical_fcs_weight(aileron_total_area, rudder_total_area, elevator_total_area):
    m_aileron=0.0256*(14445*aileron_total_area-247)**0.67
    m_rudder=0.0256*(13814*rudder_total_area-12708)**0.67
    m_elevator=0.0256*(9112.9*elevator_total_area-12098)**0.67

    return m_aileron+m_rudder+m_elevator
    
