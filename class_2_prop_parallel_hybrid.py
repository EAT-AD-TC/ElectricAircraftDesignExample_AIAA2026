def propulsion_system_mass_parallel_hybrid(
    P_rated_ElectricMotors_W,
    P_rated_Turboprops_W,
    E_fuel_J,
    N_engines,
    N_FuelTanks,
    fuel_specific_energy_J_per_kg,
    motor_specific_power_W_per_kg,
    motor_controller_specific_power_W_per_kg,
):
    """
    Standalone Class-II propulsion-system mass model for a parallel hybrid twin-turboprop.
    

    Assumptions
    -----------
    - Conventional twin-engine configuration
    - Parallel hybrid-electric powertrain
    - Li-ion batteries + gas turbines
    - Propulsion system includes:
        2 turboprops + 2 propellers + fuel system + 2 electric motors + motor controllers

    Inputs
    ------
    P_rated_ElectricMotors_W : float
        Total rated electric-motor power [W]
    P_rated_Turboprops_W : float
        Total rated turboprop power [W]
    E_fuel_J : float
        Total onboard fuel energy [J]
    N_engines : int
        Number of engines / motors
    N_FuelTanks : int
        Number of fuel tanks

    Returns
    -------
    dict
        {
            "mass_breakdown_kg": {...},
            "total_mass_kg": ...,
            "intermediate": {...}
        }
    """

    if P_rated_ElectricMotors_W < 0:
        raise ValueError("P_rated_ElectricMotors_W must be >= 0")
    if P_rated_Turboprops_W < 0:
        raise ValueError("P_rated_Turboprops_W must be >= 0")
    if E_fuel_J < 0:
        raise ValueError("E_fuel_J must be >= 0")
    if N_engines < 1:
        raise ValueError("N_engines must be >= 1")
    if N_FuelTanks < 1:
        raise ValueError("N_FuelTanks must be >= 1")

    # Per-engine powers
    P_rated_ElectricMotors_PerMotor = P_rated_ElectricMotors_W / N_engines
    P_rated_Turboprops_PerEngine = P_rated_Turboprops_W / N_engines

    # Uninstalled turboprop engine mass, kg. Mass of 1 engine.
    K_engine = 0.225 / 1000  # kg/W
    m0_engine = -4.4         # kg
    m_UninstalledTurboprop = (K_engine * P_rated_Turboprops_PerEngine) + m0_engine

    # Installed turboprop engine mass, kg. Mass of all engines.
    m_InstalledTurboprops = 1.205 * m_UninstalledTurboprop * N_engines

    # Propeller mass, kg. Mass of all propellers.
    K_prop = 1.003 * (1 / 1000) ** 0.678
    m_Propellers = K_prop * (P_rated_Turboprops_PerEngine ** 0.678) * N_engines

    # Fuel-system mass.
    K_fs = 0.454
    m_fuel = E_fuel_J / fuel_specific_energy_J_per_kg
    m_FuelSystem = K_fs * (m_fuel ** 0.48) * 10 ** (0.297 * N_engines + 0.028 * N_FuelTanks)

    # Electric-motor mass.
    m_Motors = (N_engines * P_rated_ElectricMotors_PerMotor) / motor_specific_power_W_per_kg

    # Motor-controller mass.
    m_MotorControllers = (
        (N_engines * P_rated_ElectricMotors_PerMotor)
        / motor_controller_specific_power_W_per_kg
    )

    mass_breakdown = {
        "Turboprops (installed)": m_InstalledTurboprops,
        "Propellers": m_Propellers,
        "Fuel system": m_FuelSystem,
        "Electric motors": m_Motors,
        "Motor controllers": m_MotorControllers,
    }

    total_mass = sum(mass_breakdown.values())

    return {
        "mass_breakdown_kg": mass_breakdown,
        "total_mass_kg": total_mass,
        "intermediate": {
            "P_rated_ElectricMotors_PerMotor_W": P_rated_ElectricMotors_PerMotor,
            "P_rated_Turboprops_PerEngine_W": P_rated_Turboprops_PerEngine,
            "m_UninstalledTurboprop_PerEngine_kg": m_UninstalledTurboprop,
            "m_fuel_kg": m_fuel,
        },
    }


def print_propulsion_system_mass_summary(result):
    masses = result["mass_breakdown_kg"]
    total = result["total_mass_kg"]

    ml = len(max(masses.keys(), key=len))

    print()
    print("Component".ljust(ml) + "\tMass (kg)")
    print()
    for component, mass in masses.items():
        print((component + ":").ljust(ml) + "\t" + f"{mass:.1f}")
    print()
    print("Total:".ljust(ml) + "\t" + f"{total:.1f}")
