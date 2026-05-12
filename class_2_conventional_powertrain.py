
# Implements equations shown in section V-F (31, 32, 33, 34, 35–38, 40, 65)
# Each equation is a separate function.

import math
from typing import Literal, Optional

# -----------------------------
# Helpers
# -----------------------------
def kw_to_hp(P_kw: float) -> float:
    return P_kw / 0.745699872

def hp_to_kw(P_hp: float) -> float:
    return P_hp * 0.745699872

def N_to_lbf(F_N: float) -> float:
    return F_N / 4.4482216152605

def lbf_to_N(F_lbf: float) -> float:
    return F_lbf * 4.4482216152605

def kg_to_lb(m_kg: float) -> float:
    return m_kg * 2.20462262185

def lb_to_kg(m_lb: float) -> float:
    return m_lb / 2.20462262185


# -----------------------------
# Eq. (31) Uninstalled engine mass
# -----------------------------
_ENGINE_CONST = {
    # Values as shown in  Table 10 (metric forms):
    "piston":    {"K_engine": 0.814,  "m0": 23.2,   "kind": "power_kw"},   # kg/kW, kg
    "turboprop": {"K_engine": 0.225,  "m0": -4.4,   "kind": "power_kw"},
    "turboshaft":{"K_engine": 0.077,  "m0": 101.1,  "kind": "power_kw"},
    "turbofan":  {"K_engine": 17.55,  "m0": 256.6,  "kind": "thrust_kN"},  # kg/kN, kg
}

def uninstalled_engine_mass_eq31(
    engine_type: Literal["piston", "turboprop", "turboshaft", "turbofan"],
    *,
    P_rated_kw: Optional[float] = None,
    T_rated_kN: Optional[float] = None,
) -> float:
    """
    Eq. (31):
      m_engine = K_engine * P_rated + m0  (piston/turboprop/turboshaft)
      m_engine = K_engine * T_rated + m0  (turbofan)

    Returns mass of ONE uninstalled engine [kg].
    """
    et = engine_type.lower()
    if et not in _ENGINE_CONST:
        raise ValueError("engine_type must be one of: piston, turboprop, turboshaft, turbofan")

    K = _ENGINE_CONST[et]["K_engine"]
    m0 = _ENGINE_CONST[et]["m0"]
    kind = _ENGINE_CONST[et]["kind"]

    if kind == "power_kw":
        if P_rated_kw is None:
            raise ValueError("Provide P_rated_kw for piston/turboprop/turboshaft.")
        return K * float(P_rated_kw) + m0

    # turbofan:
    if T_rated_kN is None:
        raise ValueError("Provide T_rated_kN for turbofan.")
    return K * float(T_rated_kN) + m0


# -----------------------------
# Eq. (32) Installed engine mass (no prop/gearbox)
# -----------------------------
_INSTALLED_MULT = {
    "piston": 1.223,
    "turboprop": 1.205,
    "turbofan": 1.128,
    # Note: your text says Eq. 32 does not include turboshaft explicitly.
}

def installed_engine_mass_eq32(
    engine_type: Literal["piston", "turboprop", "turbofan"],
    m_engine_kg: float,
    N_engines: int,
) -> float:
    """
    Eq. (32):
      m_installed = c * m_engine * N_engines
    Returns installed engine mass [kg] (excluding propeller/gearbox).
    """
    et = engine_type.lower()
    if et not in _INSTALLED_MULT:
        raise ValueError("engine_type must be piston, turboprop, or turbofan for Eq. 32.")
    c = _INSTALLED_MULT[et]
    return c * float(m_engine_kg) * int(N_engines)


# -----------------------------
# Eq. (33) Propeller mass for piston engines (if used)
# -----------------------------
def propeller_mass_piston_eq33(
    m_engine_kg: float,
    N_engines: int,
    K_prop: float = 0.221,
) -> float:
    """
    Eq. (33): m_propellers = K_prop * m_engine * N_engines
    Text: K_prop = 0.221 for piston engines.
    """
    return float(K_prop) * float(m_engine_kg) * int(N_engines)


# -----------------------------
# Eq. (34) Propeller mass for turboprop engines (if used)
# -----------------------------
def propeller_mass_turboprop_eq34(
    P_rated_kw: float,
    N_engines: int,
    K_prop: float = 1.003,  # kg / kW^0.678
) -> float:
    """
    Eq. (34): m_propellers = K_prop * P_rated^0.678 * N_engines
    Text: K_prop = 1.003 kg/kW^0.678 for turboprops.
    """
    return float(K_prop) * (float(P_rated_kw) ** 0.678) * int(N_engines)


# -----------------------------
# Gearbox relations (Eq. 35–38)
# IMPORTANT: Eq. (35) and Eq. (38) are proportional (∝) in your excerpt.
# So we implement:
#   - a "relative gearbox mass index" (dimensionless), and
#   - an optional scaled mass with user-provided calibration constant K_gb.
# -----------------------------
def gearbox_mass_index_eq35(HP: float, RPM_in: float, RPM_out: float) -> float:
    """
    Eq. (35) (proportional form in excerpt):
      M ∝ HP^0.76 * (RPM_in^0.13 / RPM_out^0.89)
    Returns an index (no units) because constant of proportionality is not given.
    """
    return (float(HP) ** 0.76) * ((float(RPM_in) ** 0.13) / (float(RPM_out) ** 0.89))


def output_torque_eq36(P_W: float, omega_out_rad_s: float) -> float:
    """
    Eq. (36): P = T_out * omega_out  ->  T_out = P / omega_out
    Returns T_out [N*m].
    """
    return float(P_W) / float(omega_out_rad_s)


def gear_ratio_eq37(omega_in_rad_s: float, omega_out_rad_s: float) -> float:
    """
    Eq. (37): r = omega_in / omega_out
    """
    return float(omega_in_rad_s) / float(omega_out_rad_s)


def gearbox_mass_index_eq38(T_out_Nm: float, r: float) -> float:
    """
    Eq. (38) (proportional form in excerpt):
      M ∝ T_out^0.76 * r^0.13
    Returns an index (no units).
    """
    return (float(T_out_Nm) ** 0.76) * (float(r) ** 0.13)


def gearbox_mass_scaled_from_index(index: float, K_gb: float) -> float:
    """
    Converts a gearbox mass index into an actual mass [kg] using a calibration constant K_gb.
    You determine K_gb from one known gearbox data point:
      K_gb = m_known / index_known
    """
    return float(K_gb) * float(index)


# -----------------------------
# Eq. (40) Fuel tank volume
# -----------------------------
_K_TANK_TABLE11 = {
    # Values from your Table 11 (internal volume constant), by tank type and location.
    ("discrete", "fuselage"): 1.00,
    ("integral", "wing"): 1.18,
    ("integral", "fuselage"): 1.09,
    ("bladder", "wing"): 1.30,
    ("bladder", "fuselage"): 1.20,
}

def fuel_tank_volume_eq40(
    m_fuel_kg: float,
    rho_fuel_kg_per_L: float,
    *,
    tank_type: Literal["discrete", "integral", "bladder"] = "discrete",
    location: Literal["wing", "fuselage"] = "fuselage",
    K_temp: float = 1.04,
    K_tank: Optional[float] = None,
) -> float:
    """
    Eq. (40): Q_tank = K_tank * K_temp * (m_fuel / rho_fuel)

    - m_fuel includes trapped fuel (text mentions ~6% typical; you handle that upstream if desired).
    - rho_fuel in kg/L (e.g., 0.710 avgas, 0.808 jet fuel).
    - If K_tank is not provided, we pick it from Table 11 (tank_type + location).
    Returns Q_tank in liters [L].
    """
    tt = tank_type.lower()
    loc = location.lower()

    if K_tank is None:
        key = (tt, loc)
        if key not in _K_TANK_TABLE11:
            raise ValueError("No K_tank available for that (tank_type, location). Provide K_tank explicitly.")
        K_tank = _K_TANK_TABLE11[key]

    return float(K_tank) * float(K_temp) * (float(m_fuel_kg) / float(rho_fuel_kg_per_L))


# -----------------------------
# Eq. (65) Fuel system weight
# -----------------------------
def fuel_system_weight_eq65(
    W_F_lb: float,
    N_eng: int,
    N_tanks: int,
) -> float:
    """
    Eq. (65): log(W_FS) = 0.480 log(W_F) + 0.297 N_eng + 0.028 N_t - 0.164

    In aircraft weight correlations, 'log' here is almost always log10.
    This function uses log10 and returns W_FS in pounds [lb].
    """
    W_F_lb = float(W_F_lb)
    if W_F_lb <= 0:
        raise ValueError("W_F_lb must be > 0")

    rhs = 0.480 * math.log10(W_F_lb) + 0.297 * int(N_eng) + 0.028 * int(N_tanks) - 0.164
    W_FS_lb = 10 ** rhs
    return W_FS_lb


def fuel_system_mass_from_fuel_mass_eq65(
    m_fuel_kg: float,
    N_eng: int,
    N_tanks: int,
) -> float:
    """
    Convenience wrapper:
      - converts fuel mass [kg] -> [lb]
      - computes W_FS [lb] from Eq. (65)
      - converts back to mass [kg] (treating lb as lbm)
    """
    W_F_lb = kg_to_lb(float(m_fuel_kg))
    W_FS_lb = fuel_system_weight_eq65(W_F_lb, N_eng, N_tanks)
    return lb_to_kg(W_FS_lb)


def mass_from_specific_power(
    P_rated_W: float,
    specific_power_W_per_kg: float,
) -> float:
    """
    Convert a rated power into a component mass using a specific-power assumption.

    Parameters
    ----------
    P_rated_W : float
        Rated power [W].
    specific_power_W_per_kg : float
        Specific power [W/kg].

    Returns
    -------
    float
        Component mass [kg].
    """
    if P_rated_W < 0:
        raise ValueError("P_rated_W must be >= 0")
    if specific_power_W_per_kg <= 0:
        raise ValueError("specific_power_W_per_kg must be > 0")
    return float(P_rated_W) / float(specific_power_W_per_kg)

# based on Arthur's implementation - use this
def parallel_hybrid_turboprop_propulsion_mass_breakdown(
    P_rated_electric_motors_W: float,
    P_rated_turboprops_W: float,
    *,
    N_engines: int = 2,
    N_fuel_tanks: int = 2,
    E_fuel_J: Optional[float] = None,
    m_fuel_kg: Optional[float] = None,
    fuel_specific_energy_J_per_kg: float = 42.8e6,
    electric_motor_specific_power_W_per_kg: float = 4.94e3,
    motor_controller_specific_power_W_per_kg: float = 115e3,
) -> dict:
    """
    Estimate the Class-II propulsion-system mass for a parallel hybrid twin-turboprop.

    Inputs assumed
    --------------------
    - N turboprop engines
    - N propellers
    - fuel system
    - N electric motors
    - motor controllers

    Notes
    -----
    - Turboprop engine mass uses Eq. (31) + Eq. (32).
    - Propeller mass uses Eq. (34).
    - Fuel-system mass uses Eq. (65).
    - Electric motor and motor-controller masses use simple specific-power assumptions.
    - Either `E_fuel_J` or `m_fuel_kg` must be provided.

    Parameters
    ----------
    P_rated_electric_motors_W : float
        Total rated electric-motor power for the propulsion system [W].
    P_rated_turboprops_W : float
        Total rated turboprop shaft power for the propulsion system [W].
    N_engines : int, optional
        Number of turboprop engines / electric motors. Default is 2.
    N_fuel_tanks : int, optional
        Number of fuel tanks. Default is 2.
    E_fuel_J : float or None, optional
        Total onboard fuel energy [J].
    m_fuel_kg : float or None, optional
        Total fuel mass [kg]. If provided, this is used directly.
    fuel_specific_energy_J_per_kg : float, optional
        Fuel specific energy [J/kg]. Default is 42.8e6 for Jet-A.
    electric_motor_specific_power_W_per_kg : float, optional
        Electric motor specific power [W/kg].
    motor_controller_specific_power_W_per_kg : float, optional
        Motor controller specific power [W/kg].

    Returns
    -------
    dict
        Mass breakdown and key intermediate quantities.
    """
    if P_rated_electric_motors_W < 0:
        raise ValueError("P_rated_electric_motors_W must be >= 0")
    if P_rated_turboprops_W < 0:
        raise ValueError("P_rated_turboprops_W must be >= 0")
    if N_engines < 1:
        raise ValueError("N_engines must be >= 1")
    if N_fuel_tanks < 1:
        raise ValueError("N_fuel_tanks must be >= 1")
    if fuel_specific_energy_J_per_kg <= 0:
        raise ValueError("fuel_specific_energy_J_per_kg must be > 0")

    if m_fuel_kg is None:
        if E_fuel_J is None:
            raise ValueError("Provide either E_fuel_J or m_fuel_kg.")
        if E_fuel_J < 0:
            raise ValueError("E_fuel_J must be >= 0")
        m_fuel_kg = float(E_fuel_J) / float(fuel_specific_energy_J_per_kg)
    else:
        if m_fuel_kg < 0:
            raise ValueError("m_fuel_kg must be >= 0")

    P_rated_electric_motors_per_motor_kW = float(P_rated_electric_motors_W) / int(N_engines) / 1000.0
    P_rated_turboprops_per_engine_kW = float(P_rated_turboprops_W) / int(N_engines) / 1000.0

    m_uninstalled_turboprop_per_engine_kg = uninstalled_engine_mass_eq31(
        "turboprop",
        P_rated_kw=P_rated_turboprops_per_engine_kW,
    )
    m_installed_turboprops_kg = installed_engine_mass_eq32(
        "turboprop",
        m_uninstalled_turboprop_per_engine_kg,
        int(N_engines),
    )
    m_propellers_kg = propeller_mass_turboprop_eq34(
        P_rated_turboprops_per_engine_kW,
        int(N_engines),
    )
    m_fuel_system_kg = fuel_system_mass_from_fuel_mass_eq65(
        float(m_fuel_kg),
        int(N_engines),
        int(N_fuel_tanks),
    )
    m_electric_motors_kg = mass_from_specific_power(
        float(P_rated_electric_motors_W),
        float(electric_motor_specific_power_W_per_kg),
    )
    m_motor_controllers_kg = mass_from_specific_power(
        float(P_rated_electric_motors_W),
        float(motor_controller_specific_power_W_per_kg),
    )

    mass_breakdown = {
        "Turboprops (installed)": m_installed_turboprops_kg,
        "Propellers": m_propellers_kg,
        "Fuel system": m_fuel_system_kg,
        "Electric motors": m_electric_motors_kg,
        "Motor controllers": m_motor_controllers_kg,
    }

    return {
        "inputs": {
            "P_rated_electric_motors_W": float(P_rated_electric_motors_W),
            "P_rated_turboprops_W": float(P_rated_turboprops_W),
            "N_engines": int(N_engines),
            "N_fuel_tanks": int(N_fuel_tanks),
            "m_fuel_kg": float(m_fuel_kg),
            "fuel_specific_energy_J_per_kg": float(fuel_specific_energy_J_per_kg),
            "electric_motor_specific_power_W_per_kg": float(electric_motor_specific_power_W_per_kg),
            "motor_controller_specific_power_W_per_kg": float(motor_controller_specific_power_W_per_kg),
        },
        "per_engine": {
            "P_rated_turboprop_per_engine_kW": P_rated_turboprops_per_engine_kW,
            "P_rated_electric_motor_per_motor_kW": P_rated_electric_motors_per_motor_kW,
            "m_uninstalled_turboprop_per_engine_kg": m_uninstalled_turboprop_per_engine_kg,
        },
        "mass_breakdown_kg": mass_breakdown,
        "total_mass_kg": sum(mass_breakdown.values()),
    }
