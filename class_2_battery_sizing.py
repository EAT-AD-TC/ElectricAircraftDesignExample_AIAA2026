import math
from typing import Optional

def battery_pack_mass_from_cells(
    E_bat_cell_J: float,
    e_bat_cell_J_per_kg: float,
    n_series: int,
    n_parallel: int,
    k_bat: float,
) -> float:
    """
    Compute battery pack mass from cell-level quantities.

    Eq: M_bat,pack = k_bat * (E_bat_cell / e_bat_cell) * n_s * n_p

    Parameters
    ----------
    E_bat_cell_J : float
        Energy per cell [J]
    e_bat_cell_J_per_kg : float
        Specific energy of cell [J/kg]
    n_series : int
        Number of cells in series
    n_parallel : int
        Number of cells in parallel
    k_bat : float
        Packaging factor (>1 accounts for casing, wiring, etc.)
    Advanced packs have a 15-20% overhead (1.15 ≤ 𝑘𝑏𝑎𝑡 ≤ 1.2)

    Returns
    -------
    M_bat_pack : float
        Battery pack mass [kg]
    """

    if e_bat_cell_J_per_kg <= 0:
        raise ValueError("Specific energy must be > 0")

    nps = n_series * n_parallel
    M_bat_pack = k_bat * (E_bat_cell_J / e_bat_cell_J_per_kg) * nps

    return M_bat_pack

def supercapacitor_energy_from_cells(
    C_cell_F: float,
    V_sc_V: float,
    N_series: int,
    N_parallel: int
) -> float:
    """
    Eq (47): E_sc = (3/8) * (N_p / N_s) * C_cell * V_sc^2

    Returns energy in Joules.
    """

    if N_series <= 0 or N_parallel <= 0:
        raise ValueError("Number of cells must be positive")

    E_sc = (3.0 / 8.0) * (N_parallel / N_series) * C_cell_F * (V_sc_V ** 2)

    return E_sc


def supercapacitor_mass_from_energy(
    E_sc_J: float,
    rho_sc_Wh_per_kg: float,
    eta_sc: float,
) -> float:
    """
    Eq (48): m_sc = E_sc / rho_sc
    """

    rho_sc_J_per_kg = rho_sc_Wh_per_kg * 3600
    return E_sc_J / (rho_sc_J_per_kg*eta_sc)

def motor_generator_mass(
    P_motor: float,
    T_density: float,
    rpm:float
   
) -> float:
    """
    Eq. (50) conceptual form:
        M_motor = P_motor / (T_torque_density * omega)

    where T_torque_density is in N m / kg and omega is in rad / s.

    """
    if P_motor < 0:
        raise ValueError("P_motor must be >= 0")
    if T_density <= 0:
        raise ValueError("T_density must be > 0")
    if rpm <= 0:
        raise ValueError("rpm must be > 0")

    omega = (2 * math.pi * rpm) / 60
    M_motor = P_motor / (T_density * omega)

    return M_motor 

def inverter_mass(
    P_inverter: float,
    P_d_invereter: float
) -> float:
    """
    Eq (51) M_inverter=P_invereter/P_d_inverter

    """
    M_inverter=P_inverter/P_d_invereter
    return M_inverter

def M_cable_analytical(length: float,
                      rho_c: float, 
                      A_c: float,
                      rho_i: float,
                      A_i: float) -> float: 
    """
    Eq (52) M_cable=L*(rho_c*A_c+rho_i*A_i)

    """
    M_cable=length*(rho_c*A_c+rho_i*A_i)

    return M_cable

def M_cable_heuristic(
    cable_length_m: float,
    current_A: float,
    n_parallel_runs: int = 1,
    mass_per_length_override_kg_per_m: Optional[float] = None,
) -> float:
    """
    Heuristic estimate of installed cable mass based on page 25 and 26 of EADG Paper

    Based on rule-of-thumb mass-per-length values for ~800 V aircraft power systems:
      - 300 to 400 A  -> 0.5 to 0.8 kg/m
      - 450 to 650 A  -> 0.9 to 1.5 kg/m
      - very high current / large cross-section / parallel conductors -> 1.5 to 3.0 kg/m

    Parameters
    ----------
    cable_length_m : float
        Length of one cable run [m].
    current_A : float
        Current carried by one run [A].
    n_parallel_runs : int, optional
        Number of parallel cable runs. Default is 1.
    mass_per_length_override_kg_per_m : float or None, optional
        If given, use this value directly instead of the built-in heuristic.

    Returns
    -------
    M_cable : float
        Estimated installed cable mass [kg].
    """

    if cable_length_m < 0:
        raise ValueError("cable_length_m must be >= 0")
    if current_A < 0:
        raise ValueError("current_A must be >= 0")
    if n_parallel_runs < 1:
        raise ValueError("n_parallel_runs must be >= 1")

    if mass_per_length_override_kg_per_m is not None:
        if mass_per_length_override_kg_per_m <= 0:
            raise ValueError("mass_per_length_override_kg_per_m must be > 0")
        mass_per_length = mass_per_length_override_kg_per_m

    else:
        # midpoint values of the stated heuristic ranges
        if 300 <= current_A <= 400:
            mass_per_length = 0.65   # midpoint of 0.5–0.8
        elif 450 <= current_A <= 650:
            mass_per_length = 1.20   # midpoint of 0.9–1.5
        elif current_A > 650 or n_parallel_runs > 1:
            mass_per_length = 2.25   # midpoint of 1.5–3.0
        else:
            # simple extrapolation for lower-current conceptual estimate
            # keeps result conservative but not excessive
            mass_per_length = 0.65 * (current_A / 300) if current_A > 0 else 0.0
            mass_per_length = max(0.1, mass_per_length)

    M_cable = cable_length_m * n_parallel_runs * mass_per_length
    return M_cable

def motor_cooling_mass_eq63(
    P_inverter_kW: float,
    eta_motor: float,
    P_d_motorCooling_kW_per_kg: float = 0.8,
) -> float:
    """
    Estimate motor cooling system mass using Eq. (53).

    Eq. (53):
        M_motorCooling = P_inverter * (1 - eta_motor) / P_d_motorCooling

    Parameters
    ----------
    P_inverter_kW : float
        Inverter power [kW]
    eta_motor : float
        Motor efficiency [-]
    P_d_motorCooling_kW_per_kg : float, optional
        Cooling system specific heat rejection / power density [kW/kg].
        Conservative default = 0.8 kW/kg.

    Returns
    -------
    float
        Motor cooling system mass [kg]
    """
    if P_inverter_kW < 0:
        raise ValueError("P_inverter_kW must be >= 0")
    if not (0 < eta_motor <= 1):
        raise ValueError("eta_motor must be between 0 and 1")
    if P_d_motorCooling_kW_per_kg <= 0:
        raise ValueError("P_d_motorCooling_kW_per_kg must be > 0")

    return P_inverter_kW * (1.0 - eta_motor) / P_d_motorCooling_kW_per_kg

def inverter_cooling_mass_eq66(
    P_battery_kW: float,
    eta_inverter: float,
    P_d_inverterCooling_kW_per_kg: float = 1.25,
) -> float:
    """
    Estimate inverter cooling system mass using Eq. (56).

    Eq. (56):
        M_inverterCooling = P_battery * (1 - eta_inverter) / P_d_inverterCooling

    Parameters
    ----------
    P_battery_kW : float
        Electrical power supplied by battery [kW]
    eta_inverter : float
        Inverter efficiency [-]
    P_d_inverterCooling_kW_per_kg : float, optional
        Cooling system power density [kW/kg]
        Typical range: 1.25 to 5 kW/kg
        Default = 1.25 (conservative) - this needs to be updated - see comment on page 27 of the EADG paper

    Returns
    -------
    float
        Inverter cooling mass [kg]
    """

    if P_battery_kW < 0:
        raise ValueError("P_battery_kW must be >= 0")
    if not (0 < eta_inverter <= 1):
        raise ValueError("eta_inverter must be between 0 and 1")
    if P_d_inverterCooling_kW_per_kg <= 0:
        raise ValueError("P_d_inverterCooling_kW_per_kg must be > 0")

    return P_battery_kW * (1.0 - eta_inverter) / P_d_inverterCooling_kW_per_kg
