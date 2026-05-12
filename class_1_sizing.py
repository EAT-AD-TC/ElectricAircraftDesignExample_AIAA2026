import math
# Operating empty mass estimation specifically for electric aircraft and hybrid-electric aircraft with high battery mass fraction. From equation 21
OE_TABLE = {
    (1, 1): {"C_mpl": 1.25, "C_mto": 0.20, "m_fix": 500},
    (1, 2): {"C_mpl": 1.50, "C_mto": 0.21, "m_fix": 600},
    (2, 4): {"C_mpl": 1.75, "C_mto": 0.22, "m_fix": 700},
}

def available_configs():
    """Return valid (decks, aisles) combinations."""
    return sorted(OE_TABLE.keys())

def oe_mass(m_pl: float, m_mto: float, decks: int, aisles: int) -> float:
    """
    m_OE = C_mpl*m_PL + C_mto*m_MTO + m_fix
    User selects decks and aisles. Errors if not in table.
    """
    if m_pl < 0:
        raise ValueError("m_pl must be >= 0.")
    if m_mto <= 0:
        raise ValueError("m_mto must be > 0.")

    key = (int(decks), int(aisles))
    if key not in OE_TABLE:
        raise ValueError(
            f"Invalid selection (decks={decks}, aisles={aisles}). "
            f"Valid options: {available_configs()}"
        )

    c = OE_TABLE[key]
    return c["C_mpl"] * m_pl + c["C_mto"] * m_mto + c["m_fix"]

decks=1 # Set the number of decks
aisles=1 # Set the number of aisles

def compute_E0_tot_electric_single_phase(phase_range_m, W_OE_N, W_PL_N, L_D, eta_2, eta_3, e_bat_J_per_kg, g=9.81):
    """
    Pure-electric Breguet (Eq. 20) solved for E0_bat for ONE phase.
    """
    K = eta_2 * eta_3 * L_D * (e_bat_J_per_kg / g)  # [m]
    W = W_OE_N + W_PL_N                              # [N]

    if phase_range_m >= K:
        raise ValueError(f"Phase infeasible: range={phase_range_m} m >= K={K} m")

    E0_bat = (e_bat_J_per_kg / g) * (phase_range_m * W) / (K - phase_range_m)  # [J]
    return E0_bat


def compute_E0_tot_hybrid_single_phase(
    R,
    W_OE,
    W_PL,
    L_D,
    eta_1,
    eta_2,
    eta_3,
    Phi,
    e_bat,
    e_f,
    g=9.81
):
    """
    Compute total initial onboard energy E0_tot from range equation.

    Returns
    -------
    E0_tot : float [J]
    """

    # --- phi check ---
    #if abs(1 - Phi) < 1e-12:
        #raise ValueError("Phi cannot be 1")

    # --- intermediate variables ---
    A = W_OE + W_PL
    B = g / e_bat
    M = Phi + (e_bat / e_f) * (1 - Phi)

    K = eta_3 * (e_f / g) * L_D * (eta_1 + eta_2 * Phi / (1 - Phi))

    if abs(K) < 1e-12:
        raise ValueError("K too small")

    q = math.exp(R / K)

    denom = B*(M-q*Phi)  #B * (q * Phi - M) - old but still correct if the A*(1-Q) term is also multiplied by -1
    if abs(denom) < 1e-12:
        raise ValueError("Singular solution")

    # --- final result ---
    E0_tot = A * (q - 1) / denom

    return E0_tot

#depreciated - do not use- use mission_E0_bat_by_phase_electric or mission_E0_bat_by_phase_hybrid as neede
def mission_E0_bat_by_phase(mission, W_OE_N, W_PL_N, eta_2, eta_3, e_bat_J_per_kg,g=9.81):
    """
    For phases climb/cruise/loiter/descend:
      - read 'range' (meters)
      - read 'l_d'   (L/D)
    compute E0_bat for each phase, and return total + per-phase results.
    """
    phases_to_use = ["climb", "cruise", "loiter", "descend"]

    results = []
    total_E0 = 0.0

    for ph in mission:
        phase_name = ph.get("phase", "").lower()

        if phase_name in phases_to_use:
            # Simple parsing:
            R = float(ph["range"])
            L_D = float(ph["l_d"])

            if mode == "electric":
                

                E0 = compute_E0_tot_electric_single_phase(R, W_OE_N, W_PL_N, L_D, eta_2, eta_3, e_bat_J_per_kg, g=g)
            else:
                E0 = compute_E0_tot_hybrid_single_phase(R,W_OE,W_PL,L_D,eta_1,eta_2,eta_3,Phi,e_bat,e_f,g=g)

            results.append({"phase": phase_name, "range_m": R, "L_D": L_D, "E0_bat_J": E0})
            total_E0 += E0

    return total_E0, results

def mission_E0_bat_by_phase_electric(mission, W_OE, W_PL, eta_2, eta_3, e_bat_J_per_kg,g=9.81):
    """
    For phases climb/cruise/loiter/descend:
      - read 'range' (meters)
      - read 'l_d'   (L/D)
    compute E0_bat for each phase, and return total + per-phase results.
    """
    phases_to_use = ["climb", "cruise", "loiter", "descend"]
    W_OE_N=W_OE*g
    W_PL_N=W_PL*g
    results = []
    total_E0 = 0.0

    for ph in mission:
        phase_name = ph.get("phase", "").lower()

        if phase_name in phases_to_use:
            # Simple parsing:
            R = float(ph["range"])
            L_D = float(ph["l_d"])

            
                

            E0 = compute_E0_tot_electric_single_phase(R, W_OE_N, W_PL_N, L_D, eta_2, eta_3, e_bat_J_per_kg, g=9.81)
            
                

            results.append({"phase": phase_name, "range_m": R, "L_D": L_D, "E0_bat_J": E0})
            total_E0 += E0

    return total_E0, results




def mission_E0_bat_by_phase_hybrid(mission,W_OE,W_PL,L_D,eta_1,eta_2,eta_3,e_bat,e_f,g=9.81):
    """
    For phases climb/cruise/loiter/descend:
      - read 'range' (meters)
      - read 'l_d'   (L/D)
    compute E0_bat for each phase, and return total + per-phase results.
    """
    phases_to_use = ["climb", "cruise", "loiter", "descend"]
    W_OE_N=W_OE*g
    W_PL_N= W_PL*g
    e_bat_J_per_kg=e_bat
    E0_array=[]
    E0_fuel_array=[]
    E0_bat_array=[]
    W_f_array=[]
    W_batt_array=[]

    results = []
    total_E0 = 0.0

    for ph in mission:
        phase_name = ph.get("phase", "").lower()

        if phase_name in phases_to_use:
            # Simple parsing:
            R = float(ph["range"])
            L_D = float(ph["l_d"])
            Phi= float(ph["Phi"])

            
                

            E0 = compute_E0_tot_hybrid_single_phase(R, W_OE_N, W_PL_N, L_D,eta_1, eta_2, eta_3,Phi, e_bat_J_per_kg,e_f, g=g)
            E0_fuel=(1-Phi)*E0
            E0_bat=Phi*E0
            W_f=E0_fuel/e_f
            W_bat=E0_bat/e_bat
            E0_array.append(E0)
            E0_fuel_array.append(E0_fuel)
            E0_bat_array.append(E0_bat)
            W_f_array.append(W_f)
            W_batt_array.append(W_bat)
            

            results.append({
                "phase": phase_name,
                "range_m": R,
                "L_D": L_D,
                "E0_total_J": E0,
                "E0_fuel_J": E0_fuel,
                "E0_bat_J": E0_bat,
                "fuel_mass_kg": W_f,
                "battery_mass_kg": W_bat
            })
            total_E0 += E0

    total_fuel=sum(W_f_array)
    total_bat=sum(W_batt_array)
    total_E0_bat=sum(E0_bat_array)
    total_E0_fuel=sum(E0_fuel_array)

    return total_E0, results,total_fuel,total_bat,total_E0_bat,total_E0_fuel

def battery_pack_mass(E_req_J, e_bat_chem_J_per_kg, k_bat):
    """
    Class I battery pack mass estimation.

    Parameters
    ----------
    E_req_J : float
        Required usable battery energy [J]
    e_bat_chem_J_per_kg : float
        Cell-level specific energy [J/kg]
    k_bat : float
        Pack overhead factor (typically 1.15–1.20)

    Returns
    -------
    M_bat_pack : float
        Battery pack mass [kg]
    """
    return k_bat * E_req_J / e_bat_chem_J_per_kg




def converge_mtom_hybrid(inputs):
    mission    = inputs["mission"]
    payload    = inputs["payload"]
    eta_1      = inputs["eta_1"]
    eta_2      = inputs["eta_2"]
    eta_3      = inputs["eta_3"]
    #Phi        = inputs["Phi"]
    e_bat      = inputs["e_bat"]
    e_f        = inputs["e_f"]
    k_bat      = inputs["k_bat"]
    mtom_guess = inputs["mtom_guess"]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)
    oe_args  = inputs.get("oe_args", (1, 1))

    err = 1e9
    i = 0
    history = []

    while err > tol and i < max_iter:
        OE = oe_mass(payload, mtom_guess, *oe_args)

        E0_total, phase_results,total_fuel,total_bat,total_E0_bat,total_E0_fuel = mission_E0_bat_by_phase_hybrid(
            mission=mission,
            W_OE=OE,
            W_PL=payload,
            L_D=None,
            eta_1=eta_1,
            eta_2=eta_2,
            eta_3=eta_3,
            e_bat=e_bat,
            e_f=e_f,
            g=g
        )

        M_batt = battery_pack_mass(total_E0_bat, e_bat, k_bat)

        mtom_new_raw = OE + M_batt + payload + total_fuel
        mtom_new = relax * mtom_new_raw + (1 - relax) * mtom_guess

        err = abs(mtom_new - mtom_guess)

        history.append({
            "iter": i + 1,
            "MTOM_guess": mtom_guess,
            "OE": OE,
            "E0_total_J": E0_total,
            "M_batt": M_batt,
            "MTOM_new": mtom_new,
            "error": err
        })

        mtom_guess = mtom_new
        i += 1

    return {
        "MTOM": mtom_guess,
        "OE": OE,
        "M_batt": M_batt,
        "E0_total": E0_total,
        "total_E0_bat": total_E0_bat,
        "phase_results": phase_results,
        "iterations": i,
        "error": err,
        "history": history,
        "total_fuel":total_fuel,
        "total_bat":total_bat
    }

def converge_mtom_electric(inputs):
    mission    = inputs["mission"]
    payload    = inputs["payload"]
    eta_1      = inputs["eta_1"]
    eta_2      = inputs["eta_2"]
    eta_3      = inputs["eta_3"]
    #Phi        = inputs["Phi"]
    e_bat      = inputs["e_bat"]
    e_f        = inputs["e_f"]
    k_bat      = inputs["k_bat"]
    mtom_guess = inputs["mtom_guess"]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)
    oe_args  = inputs.get("oe_args", (1, 1))

    err = 1e9
    i = 0
    history = []

    while err > tol and i < max_iter:
        OE = oe_mass(payload, mtom_guess, *oe_args)

        E0_total, phase_results = mission_E0_bat_by_phase_electric(
            mission=mission,
            W_OE=OE,
            W_PL=payload,
            eta_2=eta_2,
            eta_3=eta_3,
            e_bat_J_per_kg=e_bat,
            g=g
        )
        
        M_batt = battery_pack_mass(E0_total, e_bat, k_bat)

        mtom_new_raw = OE + M_batt + payload 
        mtom_new = relax * mtom_new_raw + (1 - relax) * mtom_guess

        err = abs(mtom_new - mtom_guess)

        history.append({
            "iter": i + 1,
            "MTOM_guess": mtom_guess,
            "OE": OE,
            "E0_total_J": E0_total,
            "M_batt": M_batt,
            "MTOM_new": mtom_new,
            "error": err
        })

        mtom_guess = mtom_new
        i += 1

    return {
        "MTOM": mtom_guess,
        "OE": OE,
        "M_batt": M_batt,
        "E0_total": E0_total,
        "phase_results": phase_results,
        "iterations": i,
        "error": err,
        "history": history
    }

#Note- this is specifically tailored to the E-19 case and is to be used only in the E-19 worked example
def converge_mtom_electric_E19(inputs):
    mission    = inputs["mission"]
    payload    = inputs["payload"]
    eta_1      = inputs["eta_1"]
    eta_2      = inputs["eta_2"]
    eta_3      = inputs["eta_3"]
    #Phi        = inputs["Phi"]
    e_bat      = inputs["e_bat"]
    e_f        = inputs["e_f"]
    k_bat      = inputs["k_bat"]
    mtom_guess = inputs["mtom_guess"]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)
    oe_args  = inputs.get("oe_args", (1, 1))

    err = 1e9
    i = 0
    history = []
    energy_allowances_e19=233.28e+06 #hardcoded values for taxi, warmup energy etc. from slide 8, #https://elib.dlr.de/132771/1/eCommuter.pdf

    while err > tol and i < max_iter:
        OE = oe_mass(payload, mtom_guess, *oe_args)

        E0_total, phase_results,W_f = mission_E0_bat_by_phase_electric_E19(
            mission=mission,
            W_OE=OE,
            W_PL=payload,
            eta_1=eta_1,
            eta_2=eta_2,
            eta_3=eta_3,
            e_bat_J_per_kg=e_bat,
            e_f=e_f,
            g=g,
        )
        
        M_batt = battery_pack_mass(E0_total+energy_allowances_e19, e_bat, k_bat)

        mtom_new_raw = OE + M_batt + payload + W_f 
        mtom_new = relax * mtom_new_raw + (1 - relax) * mtom_guess

        err = abs(mtom_new - mtom_guess)

        history.append({
            "iter": i + 1,
            "MTOM_guess": mtom_guess,
            "OE": OE,
            "E0_total_J": E0_total,
            "M_batt": M_batt,
            "MTOM_new": mtom_new,
            "error": err
        })

        mtom_guess = mtom_new
        i += 1

    return {
        "MTOM": mtom_guess,
        "OE": OE,
        "M_batt": M_batt,
        "E0_total": E0_total,
        "phase_results": phase_results,
        "iterations": i,
        "error": err,
        "history": history
    }




#Note- this is specifically tailored to the E-19 case and is to be used only in the E-19 worked example
def mission_E0_bat_by_phase_electric_E19(
    mission,
    W_OE,
    W_PL,
    eta_1,
    eta_2,
    eta_3,
    e_bat_J_per_kg,
    e_f,
    g=9.81,
):
    """
    Compute required battery energy by mission phase for the E19-style
    electric mission sizing path.

    Standard mission phases are treated as pure-electric. Any phase with a
    provided Phi < 1 is treated with the hybrid single-phase relation so the
    phase can contribute both battery and fuel energy while still returning the
    battery energy that drives pack sizing.
    """
    electric_phases = {"climb", "cruise", "loiter", "descend"}
    phi_eps = 1e-6

    W_OE_N = W_OE * g
    W_PL_N = W_PL * g
    results = []
    total_E0_bat = 0.0
    total_fuel_mass = 0.0
    
    for ph in mission:
        phase_name = ph.get("phase", "").lower()
        if "range" not in ph or "l_d" not in ph:
            results.append({
                "phase": phase_name,
                "mode": "skipped",
                "E0_total_J": 0.0,
                "E0_bat_J": 0.0,
                "E0_fuel_J": 0.0,
                "fuel_mass_kg": 0.0,
            })
            continue

        R = float(ph["range"])
        L_D = float(ph["l_d"])

        phi_raw = ph.get("Phi", ph.get("phi"))
        use_pure_electric = phase_name in electric_phases and (
            phi_raw is None or float(phi_raw) >= 1.0 - phi_eps
        )

        if use_pure_electric:
            E0_bat = compute_E0_tot_electric_single_phase(
                R,
                W_OE_N,
                W_PL_N,
                L_D,
                eta_2,
                eta_3,
                e_bat_J_per_kg,
                g=g,
            )
            total_E0_bat += E0_bat 
            results.append({
                "phase": phase_name,
                "mode": "electric",
                "range_m": R,
                "L_D": L_D,
                "E0_total_J": E0_bat,
                "E0_bat_J": E0_bat,
                "E0_fuel_J": 0.0,
                "fuel_mass_kg": 0.0,
            })
            continue

        if phi_raw is None:
            raise KeyError(
                f"Phase '{phase_name}' must define 'Phi' when it is not treated as pure-electric."
            )

        Phi = float(phi_raw)
        if not (0.0 <= Phi < 1.0):
            raise ValueError("Phi must satisfy 0 <= Phi < 1 for non-electric E19 phases.")

        E0_phase = compute_E0_tot_hybrid_single_phase(
            R,
            W_OE_N,
            W_PL_N,
            L_D,
            eta_1,
            eta_2,
            eta_3,
            Phi,
            e_bat_J_per_kg,
            e_f,
            g=g,
        )
        E0_fuel = (1 - Phi) * E0_phase
        E0_bat = Phi * E0_phase
        W_f = E0_fuel / e_f

        total_E0_bat += E0_bat
        total_fuel_mass += W_f
        results.append({
            "phase": phase_name,
            "mode": "hybrid_split",
            "range_m": R,
            "L_D": L_D,
            "Phi": Phi,
            "E0_total_J": E0_phase,
            "E0_bat_J": E0_bat,
            "E0_fuel_J": E0_fuel,
            "fuel_mass_kg": W_f,
        })

    return total_E0_bat, results, total_fuel_mass
