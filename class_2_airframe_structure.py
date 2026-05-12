# weights_structures.py
# Implements the equations from section V-E 

import math


# ----------------------------
# Wing mass (Eq. 22)
# ----------------------------
def wing_mass_eq22(
    W_G_kg: float,
    b_m: float,
    S_m2: float,
    t_root_m: float,
    sweep_half_chord_deg: float,
    n_ult: float,
    *,
    category: str = "light",  # "light" or "large_transport"
    engines_wing_mounted: int = 0,  # 0, 2, or 4
    main_gear_attached_to_wing: bool = True,
    b_ref_m: float = 1.905,
) -> float:
    """
    Returns wing mass W_w [kg].

    Eq. (22): Ww/WG = k_w * b^0.75 * (1 + sqrt(b_ref/bs)) * n_ult^0.55 * ((bs/t_r)/(W_G/S))^0.30
      where bs = b / cos(Lambda_0.5c)
    Coefficients from text:
      - large_transport: k_w = 6.67e-3 (W_G > 12500 lb)
      - light:          k_w = 4.90e-3 (W_G < 12500 lb)
    """
    if category not in ("light", "large_transport"):
        raise ValueError("category must be 'light' or 'large_transport'")

    k_w = 4.90e-3 if category == "light" else 6.67e-3

    lam = math.radians(sweep_half_chord_deg)
    bs = b_m / math.cos(lam)  # structural span
    WG_over_S = W_G_kg / S_m2  # "W_G/S" in kg/m^2 as used in the source

    ratio = (bs / t_root_m) / WG_over_S
    Ww_over_WG = (
        k_w
        * (b_m ** 0.75)
        * (1.0 + math.sqrt(b_ref_m / bs))
        * (n_ult ** 0.55)
        * (ratio ** 0.30)
    )

    W_w = Ww_over_WG * W_G_kg

    # Reductions from text
    if engines_wing_mounted not in (0, 2, 4):
        raise ValueError("engines_wing_mounted must be 0, 2, or 4")
    if engines_wing_mounted == 2:
        W_w *= 0.95
    elif engines_wing_mounted == 4:
        W_w *= 0.90

    if not main_gear_attached_to_wing:
        W_w *= 0.95

    return W_w


# ----------------------------
# Tail mass (Eq. 23) — light, low-speed
# ----------------------------
def tail_mass_light_eq23(S_tail_m2: float, n_ult: float, k_wt: float = 0.64) -> float:
    """
    Returns total tail mass W_tail [kg] for light, low-speed aircraft.
    Eq. (23): W_tail = k_wt * (n_ult * S_tail^2)^0.75
    """
    return k_wt * ((n_ult * (S_tail_m2 ** 2)) ** 0.75)


# ----------------------------
# Tail surface mass (Eq. 24 + 25) — transport polynomial method
# ----------------------------
def tail_x_eq24(V_D_kts: float, S_surface_m2: float, sweep_half_chord_deg: float) -> float:
    """
    Eq. (24): x = (V_D/1000) * S_surface^0.2 / sqrt(cos(Lambda_0.5c))
    V_D in knots (EAS)
    """
    lam = math.radians(sweep_half_chord_deg)
    return (V_D_kts / 1000.0) * (S_surface_m2 ** 0.2) / math.sqrt(math.cos(lam))


def k_v_eq26(S_h_m2: float, h_h_m: float, S_v_m2: float, b_v_m: float) -> float:
    """
    Eq. (26): k_v = 1 + 0.15 * (S_h * h_h) / (S_v * b_v)
    Used for vertical tail when horizontal tail is fin-mounted (T-tail).
    """
    return 1.0 + 0.15 * (S_h_m2 * h_h_m) / (S_v_m2 * b_v_m)


def tail_surface_mass_eq25(S_surface_m2: float, x: float, k_surface: float = 1.0) -> float:
    """
    Eq. (25): W_tailsurface = k_surface * S_surface * (0.408x^4 - 3.4945x^3 + 7.8427x^2 - 2.5529x + 1.2754)
    Returns mass [kg].
    """
    poly = (
        0.408 * x**4
        - 3.4945 * x**3
        + 7.8427 * x**2
        - 2.5529 * x
        + 1.2754
    )
    return k_surface * S_surface_m2 * poly


# ----------------------------
# Fuselage mass (Eq. 27)
# ----------------------------
def fuselage_mass_eq27(
    V_D_mps: float,
    l_t_m: float,
    b_f_m: float,
    h_f_m: float,
    S_G_m2: float,
    *,
    k_wf: float = 0.23,
    pressurized: bool = False,
    fuselage_mounted_engines: bool = False,
    main_gear_attached_to_fuselage: bool = False,
    freighter: bool = False,
    no_attachment_structure_or_gear_bay: bool = False,
) -> float:
    """
    Eq. (27): W_f = k_wf * sqrt( V_D * l_t / (b_f + h_f) ) * S_G^1.2
    V_D in m/s (EAS). Returns mass [kg].

    Adjustments from text:
      +8%  pressurization
      +4%  fuselage-mounted engines
      +7%  main landing gear attached to fuselage
      +10% freighter
      -4%  no attachment structure / no landing gear bay
    """
    base = k_wf * math.sqrt(V_D_mps * l_t_m / (b_f_m + h_f_m)) * (S_G_m2 ** 1.2)

    factor = 1.0
    if pressurized:
        factor *= 1.08
    if fuselage_mounted_engines:
        factor *= 1.04
    if main_gear_attached_to_fuselage:
        factor *= 1.07
    if freighter:
        factor *= 1.10
    if no_attachment_structure_or_gear_bay:
        factor *= 0.96

    return base * factor


# ----------------------------
# Landing gear mass (Eq. 28)
# ----------------------------
def landing_gear_mass_eq28(
    W_to_kg: float,
    *,
    gear: str,                 # "nose" or "main"
    wing: str = "low",         # "low" or "high"
    retractable: bool = True,
) -> float:
    """
    Eq. (28): W_uc = k_uc * (A + B*W_to^(3/4) + C*W_to + D*W_to^(2/3))

    Coefficients from text (retractable only):
      - nose: A=9.1,  B=0.082, C=0,     D=2.97e-6
      - main: A=18.1, B=0.131, C=0.019, D=2.23e-5
    k_uc = 1.00 (low wing), 1.08 (high wing)
    """
    if not retractable:
        raise NotImplementedError("Only retractable gear coefficients provided in your excerpt.")

    gear = gear.lower()
    if gear not in ("nose", "main"):
        raise ValueError("gear must be 'nose' or 'main'")

    wing = wing.lower()
    if wing not in ("low", "high"):
        raise ValueError("wing must be 'low' or 'high'")

    k_uc = 1.0 if wing == "low" else 1.08

    if gear == "nose":
        A, B, C, D = 9.1, 0.082, 0.0, 2.97e-6
    else:
        A, B, C, D = 18.1, 0.131, 0.019, 2.23e-5

    term = (
        A
        + B * (W_to_kg ** (3.0 / 4.0))
        + C * W_to_kg
        + D * (W_to_kg ** (2.0 / 3.0))
    )
    return k_uc * term


# ----------------------------
# Nacelle & pylon mass (Eq. 29) — propeller case
# ----------------------------
def nacelle_mass_prop_eq29(
    ESHP_to_hp: float,
    *,
    gear_retracts_into_nacelle: bool = False,
    over_wing_exhaust: bool = False,
) -> float:
    """
    Eq. (29): W_n = 0.0635 * ESHP_to   (kg), ESHP in horsepower
    Additions (text):
      +0.018 kg per hp if landing gear retractable into nacelle
      +0.05 kg per hp for over-wing exhausts
    """
    Wn = 0.0635 * ESHP_to_hp
    if gear_retracts_into_nacelle:
        Wn += 0.018 * ESHP_to_hp
    if over_wing_exhaust:
        Wn += 0.05 * ESHP_to_hp
    return Wn


# ----------------------------
# Nacelle & pylon mass (Eq. 30) — jet/turbofan case
# ----------------------------
def nacelle_mass_jet_eq30(
    T_to_N: float,
    *,
    k_n: float = 0.055,          # 0.055 pod-mounted turbojet/turbofan, 0.065 high-bypass turbofan
    thrust_reverser: bool = True,
) -> float:
    """
    Eq. (30): W_n = k_n * T_to
    Reduction: -10% if no thrust reverser present.
    """
    Wn = k_n * T_to_N
    if not thrust_reverser:
        Wn *= 0.90
    return Wn


def total_struct_weight(
    # --- Wing ---
    W_G, b, S, t_root, sweep, n_ult,
    wing_category="light",
    engines_wing_mounted=0,
    main_gear_attached_to_wing=True,

    # --- Tail (light method) ---
    S_tail=None,

    # --- Fuselage ---
    V_D=None, l_t=None, b_f=None, h_f=None, S_G=None,
    pressurized=False,
    fuselage_mounted_engines=False,
    main_gear_attached_to_fuselage=False,
    freighter=False,

    # --- Landing gear ---
    W_to=None,
    wing_position="low",

    # --- Nacelle ---
    nacelle_type="jet",   # "jet" or "prop"
    T_to=None,            # for jet
    ESHP_to=None          # for prop
):
    if None in (V_D, l_t, b_f, h_f, S_G, W_to):
        raise ValueError("V_D, l_t, b_f, h_f, S_G, and W_to must all be provided.")

    # Wing
    W_w = wing_mass_eq22(
        W_G, b, S, t_root, sweep, n_ult,
        category=wing_category,
        engines_wing_mounted=engines_wing_mounted,
        main_gear_attached_to_wing=main_gear_attached_to_wing
    )

    # Tail (light aircraft assumption)
    W_tail = tail_mass_light_eq23(S_tail, n_ult)

    # Fuselage
    W_f = fuselage_mass_eq27(
        V_D, l_t, b_f, h_f, S_G,
        pressurized=pressurized,
        fuselage_mounted_engines=fuselage_mounted_engines,
        main_gear_attached_to_fuselage=main_gear_attached_to_fuselage,
        freighter=freighter
    )

    # Landing gear
    W_nose = landing_gear_mass_eq28(W_to, gear="nose", wing=wing_position)
    W_main = landing_gear_mass_eq28(W_to, gear="main", wing=wing_position)
    W_lg = W_nose + W_main

    # Nacelle
    if nacelle_type == "jet":
        W_n = nacelle_mass_jet_eq30(T_to)
    else:
        W_n = nacelle_mass_prop_eq29(ESHP_to)

    # Total
    W_total = W_w + W_tail + W_f + W_lg + W_n

    return W_total

# ----------------------------
# Helper function - unpacks the parameters from a dictionary and passes them to total_struct_weight
# ----------------------------

def total_struct_weight_from_dict(inp):
    nacelle_type = inp["configuration"]["nacelle_type"]

    # Reads design wing loading
    w_s_sel=inp["wing"]["w_s_sel"]

    #Pulls current MTOM estimate
    W_G=inp["wing"]["W_G_kg"]

    #Recomputes wing area in m2 based on current MTOM estimate
    S_m2=W_G/ w_s_sel #meters2
    #Recomputes span from Aspect Ratio and recomputed wing area
    b_wing = math.sqrt(inp["wing"]["A"] * S_m2)
    

    # Read aircraft geometry prameters
    lam = inp["wing"]["lam"]
    inp["wing"]["S_m2"] = S_m2
    inp["wing"]["b_m"] = b_wing
    t_c_root=inp["wing"]["t_c_root"]
   

    
    # Compute updated root chord and root thickness using t_c_root
    c_root = (2.0 * S_m2) / (b_wing * (1.0 + lam))
    c_tip = lam * c_root
    t_root = t_c_root * c_root
    inp["wing"]["t_root_m"]=t_root

    inp["wing"]["c_root"] = c_root
    inp["wing"]["c_tip"] = c_tip

    #declare inputs for tail sizing
    tail_inputs = {
    "MTOM_kg": inp["wing"]["W_G_kg"],
    "S_w_m2": inp["wing"]["S_m2"],
    "b_w_m": inp["wing"]["b_m"],
    "c_bar_w_m": 0.5 * (inp["wing"]["c_root"] + inp["wing"]["c_tip"]),
    "c_ht": inp["tail"]["c_ht"],
    "c_vt": inp["tail"]["c_vt"],
    "a_fus": inp["tail"]["a_fus"],
    "c_fus": inp["tail"]["c_fus"],
    "ht_arm_fraction": inp["tail"]["ht_arm_fraction"],
    "vt_arm_fraction": inp["tail"]["vt_arm_fraction"],
    }
    #Estimate HT and VT areas in m2 
    tail_out = tail_areas_from_volume_coefficients(**tail_inputs)
    S_ht_m2= tail_out["S_ht_m2"]
    S_vt_m2= tail_out["S_vt_m2"]
    S_tail_total= S_ht_m2 + S_vt_m2

    #Update total tail area into input to class 2 structural sizing
    inp["tail"]["S_tail_m2"] = S_tail_total

    

    return total_struct_weight(
        # --- Wing ---
        W_G=inp["wing"]["W_G_kg"],
        b=inp["wing"]["b_m"],
        S=inp["wing"]["S_m2"],
        t_root=inp["wing"]["t_root_m"],
        sweep=inp["wing"]["sweep_half_chord_deg"],
        n_ult=inp["wing"]["n_ult"],
        wing_category=inp["wing"]["category"],
        engines_wing_mounted=inp["wing"]["engines_wing_mounted"],
        main_gear_attached_to_wing=inp["wing"]["main_gear_attached_to_wing"],

        # --- Tail ---
        S_tail=inp["tail"]["S_tail_m2"],

        # --- Fuselage ---
        V_D=inp["fuselage"]["V_D_mps"],
        l_t=inp["fuselage"]["l_t_m"],
        b_f=inp["fuselage"]["b_f_m"],
        h_f=inp["fuselage"]["h_f_m"],
        S_G=inp["fuselage"]["S_G_m2"],
        pressurized=inp["fuselage"]["pressurized"],
        fuselage_mounted_engines=inp["fuselage"]["fuselage_mounted_engines"],
        main_gear_attached_to_fuselage=inp["fuselage"]["main_gear_attached_to_fuselage"],
        freighter=inp["fuselage"]["freighter"],

        # --- Landing gear ---
        W_to=inp["landing_gear"]["W_to_kg"],
        wing_position=inp["landing_gear"]["wing"],

        # --- Nacelle ---
        nacelle_type=nacelle_type,
        T_to=inp["engine"]["T_to_N"],
        ESHP_to=inp["nacelle"]["ESHP_to_hp"],
    )

def tail_areas_from_volume_coefficients(
    MTOM_kg,
    S_w_m2,
    b_w_m,
    c_bar_w_m,
    c_ht,
    c_vt,
    a_fus,
    c_fus,
    ht_arm_fraction,
    vt_arm_fraction,
):
    """
    Estimate horizontal and vertical tail surface areas.

    Parameters
    ----------
    MTOM_kg : float
        Maximum takeoff mass [kg]
    S_w_m2 : float
        Wing reference area [m^2]
    b_w_m : float
        Wing span [m]
    c_bar_w_m : float
        Mean aerodynamic chord of wing [m]
    c_ht : float
        Horizontal tail volume coefficient [-]
    c_vt : float
        Vertical tail volume coefficient [-]
    a_fus : float
        Empirical fuselage-length coefficient
    c_fus : float
        Empirical fuselage-length exponent
    ht_arm_fraction : float
        Horizontal tail arm as fraction of fuselage length [-]
        e.g. 0.50 to 0.55 for wing-mounted engines
    vt_arm_fraction : float
        Vertical tail arm as fraction of fuselage length [-]
        often taken similar to horizontal if no better estimate exists

    Returns
    -------
    dict
        Dictionary containing fuselage length, tail arms,
        horizontal tail area, and vertical tail area.
    """

    # Fuselage length estimate
    l_f_m = a_fus * (MTOM_kg ** c_fus)

    # Tail arm estimates
    L_ht_m = ht_arm_fraction * l_f_m
    L_vt_m = vt_arm_fraction * l_f_m

    # Tail areas
    S_ht_m2 = (c_ht * c_bar_w_m * S_w_m2) / L_ht_m
    S_vt_m2 = (c_vt * b_w_m * S_w_m2) / L_vt_m

    return {
        "l_f_m": l_f_m,
        "L_ht_m": L_ht_m,
        "L_vt_m": L_vt_m,
        "S_ht_m2": S_ht_m2,
        "S_vt_m2": S_vt_m2,
    }

# ---------------------------------------------------------------------------------------------- #
# Beginning of section with converger functions
# ---------------------------------------------------------------------------------------------- #

#Converges MTOM using class 2 mass estimate for OEM and uses hybrid range equation
def converge_mtom_hybrid_struct(inputs):
    import class_1_sizing
    import powertrain_component_sizing
    import class_2_prop_parallel_hybrid
    import powertrain_component_sizing
    import class_2_battery_sizing
    import special_functions


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
    engine = inputs["engine"]
    powertrain_type=inputs["powertrain_type"]
    eta_p=inputs["eta_p"]
    eta_gb=inputs["eta_gb"]
    eta_gen=engine["eta_gen"]
    phases_to_evaluate=inputs["phases_to_evaluate"]
    E19_MISSION=inputs['E19_replicate']
    energy_allowances_e19=0
    if E19_MISSION == 'yes':
        energy_allowances=233.28e+06 #Joules


    

    w_p_sel=inputs["w_p_sel"]

    
    k_n = engine["k_n"]
    thrust_reverser = engine["thrust_reverser"]

    E_fuel = engine["E_fuel"] #fuel energy in Joules
    N_engines = engine["N_engines"] #number of engines
    N_FuelTanks = engine["N_FuelTanks"] #number of fuel tanks

    fuel_specific_energy = engine["fuel_specific_energy_J_per_kg"] #fuel specific energy
    motor_specific_power = engine["motor_specific_power_W_per_kg"] #motor specific energy
    motor_controller_specific_power = engine["motor_controller_specific_power_W_per_kg"] #motor controller specific energy
    wf=0
    p_w_array_mot=[]
    p_w_cont_array_mot=[]
    p_w_array_te=[]
    p_w_array_batt=[]
    #p_w_cont_array_te=[]
    p_w_cont_array_batt=[]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)

    err = 1e9
    i = 0
    history = []
    mtom_tracker=[] #debugging variable
    for ph in mission:
        phase_name = ph.get("phase", "").lower()
        if phase_name in phases_to_evaluate:
            Phi = float(ph["Phi"])
        
            w_p_out=powertrain_component_sizing.power_loading_components(w_p_sel,Phi,eta_p,eta_3,eta_1,eta_2,powertrain_type,eta_gen) # Note to self: figure out the right order of etas

            w_p_out_batt=powertrain_component_sizing.WP_batt_parallel(w_p_sel, Phi, eta_p, eta_1, eta_2, eta_3) # need to make sure the etas correspond to the right component!
            w_p_motor= w_p_out["W_over_Pem"] # w_p motor from powertrain_component_sizing
            
            w_p_te= w_p_out["W_over_Pte"] # w_p thermal engine from powertrain_component_sizing
            p_w_motor=1/w_p_motor
            p_w_te=1/w_p_te
            p_w_batt=1/w_p_out_batt
            p_w_array_te.append(p_w_te)  # collecting p/w for each misison phase
            p_w_array_batt.append(p_w_batt)# collecting p/w for each misison phase
            print("thermal engine power is",p_w_array_te)
            print("thermal engine power is",p_w_array_te)
            p_w_array_mot.append(p_w_motor) # collecting p/w for each misison phase
            print("thermal engine power is",p_w_array_mot)
            if phase_name in ("climb", "cruise", "loiter","ifr"):
                p_w_cont_array_mot.append(p_w_motor)
                p_w_cont_array_batt.append(p_w_batt)
                
    """ Determine max and continuous motor power"""
    p_w_max_mot=max(p_w_array_mot) # get max motor power
    p_w_max_cont_mot=max(p_w_cont_array_mot) # get max continuour motor power
    power_to_prop_sizing_mot=max(p_w_max_mot,1.2*p_w_max_cont_mot) #input to class 2 prop sizing 
    
    p_w_max_batt_max=max(p_w_array_batt) # get max battery power
    p_w_max_cont_batt=max(p_w_cont_array_batt) # get max continuous battery power
    power_to_prop_sizing_bat=max(p_w_max_batt_max,p_w_max_cont_batt) #input to class 2 prop sizing 
    
    p_w_max_te=max(p_w_array_te) # get max thermal engine power
    power_to_prop_sizing_te=p_w_max_te #input to class 2 prop sizing

    aux_power_out = special_functions.subsystem_power_energy_from_class2_inputs(inputs)
    energy_aux_power=aux_power_out["total_energy_j"]["total"]

    

    systems_out = special_functions.installed_system_weights_from_class2_inputs(inputs)
    total_systems_weight_kg = systems_out["total_weight_kg"]

    sys_weight_breakdown=systems_out["weight_breakdown_kg"]
    print("total systems weight is",total_systems_weight_kg)
    print("sys_weight_breakdown",sys_weight_breakdown)




    total_fuel_mass = 0.0
    E0_total = 0.0
    phase_results = []
    OE = None
    M_batt = None
    em_mot_mass = None
    p_rated_em = None
    p_rated_te = None
    prop_mass = None
    prop_mass_breakddown = None

    while err > tol and i < max_iter:

        # --- Update MTOM-dependent fields ---
        inputs["wing"]["W_G_kg"] = mtom_guess
        inputs["landing_gear"]["W_to_kg"] = mtom_guess
        for ph in inputs["mission"]:
            ph["MTOM_limit"] = mtom_guess

        # --- Structural weight ---
        OE = total_struct_weight_from_dict(inputs)

        E0_total, phase_results,total_fuel,total_bat,total_E0_bat,total_E0_fuel = class_1_sizing.mission_E0_bat_by_phase_hybrid(
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
        p_rated_em= power_to_prop_sizing_mot * (mtom_guess)  #w
        p_rated_te= power_to_prop_sizing_te * (mtom_guess)  #W
        prop_mass_out=class_2_prop_parallel_hybrid.propulsion_system_mass_parallel_hybrid( p_rated_em,p_rated_te,total_E0_fuel,N_engines,N_FuelTanks,e_f,motor_specific_power,motor_controller_specific_power)
        prop_mass_breakddown=prop_mass_out["mass_breakdown_kg"] # prop mass breakdown is a lower level key in the results dict
        turboprop_installed_mass=prop_mass_breakddown["Turboprops (installed)"]
        propeller_mass=prop_mass_breakddown["Propellers"]
        fuel_system_mass=prop_mass_breakddown["Fuel system"]
        motor_controller_mass=prop_mass_breakddown["Motor controllers"]


        
        #prop_mass=prop_mass_out["total_mass_kg"] #kg
    
        M_batt = class_1_sizing.battery_pack_mass(total_E0_bat+energy_aux_power+energy_allowances, e_bat, k_bat) # still using class 1 battery sizing - if n_parallel,n_series and E_bat_cell are known then // use battery_pack_mass_from_cells from class 2 battery_sizing //
        #M_batt = class_2_battery_sizing. battery_pack_mass_from_cells(total_E0_bat/(128*40),e_bat,128,40,k_bat) #ns=128, np=40 ( Assuming redundant packs as a single pack) from Chin et al. (2019), Battery performance modelling on the X-57 Maxwell (https://openmdao.org/pubs/chin_battery_performance_x57_2019.pdf - Table 1)
        
 

        mtom_new_raw = OE + M_batt + payload + total_fuel + turboprop_installed_mass+propeller_mass+fuel_system_mass+ motor_controller_mass+total_systems_weight_kg
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
        "total_bat":total_bat,
        "propulsion_mass":prop_mass,
        "turboprop_installed_mass":turboprop_installed_mass,
        "propeller_mass":propeller_mass,
        "fuel_system_mass": fuel_system_mass,
        "motor_controller_mass": motor_controller_mass,
        "p_rated_em": p_rated_em,
        "p_rated_te":p_rated_te,
        
        
    }

#Converges MTOM using class 2 mass estimate for OEM and uses electric range equation ( systems mass not included yet) 
def converge_mtom_electric_struct(inputs):
    import class_1_sizing
    import powertrain_component_sizing
    import class_2_prop_parallel_hybrid
    import powertrain_component_sizing
    import class_2_battery_sizing


    
    # Inputs dervied from notebook
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
    engine = inputs["engine"]
    powertrain_type=inputs["powertrain_type"]
    eta_p=inputs["eta_p"]
    eta_gb=inputs["eta_gb"]
    eta_gen=engine["eta_gen"]
    phases_to_evaluate=inputs["phases_to_evaluate"]


    
    #design W/P ratio from constraint analysis
    w_p_sel=inputs["w_p_sel"]

    
    k_n = engine["k_n"]
    thrust_reverser = engine["thrust_reverser"]

    E_fuel = engine["E_fuel"] #fuel energy in Joules
    N_engines = engine["N_engines"] #number of engines
    N_FuelTanks = engine["N_FuelTanks"] #number of fuel tanks

    fuel_specific_energy = engine["fuel_specific_energy_J_per_kg"] #fuel specific energy
    motor_specific_power = engine["motor_specific_power_W_per_kg"] #motor specific energy
    motor_controller_specific_power = engine["motor_controller_specific_power_W_per_kg"] #motor controller specific energy
    wf=0

    #init some arrays to store results
    p_w_array_mot=[]
    p_w_cont_array_mot=[]
    p_w_array_te=[]
    p_w_array_batt=[]
    #p_w_cont_array_te=[]
    p_w_cont_array_batt=[]

    g        = inputs.get("g", 9.81)

    #convergence params
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)
    err = 1e9
    i = 0
    history = []
    mtom_tracker=[] #debugging variable - comment out when done using this
    phi_eps = 1e-6
    for ph in mission: #loops through each phase in mission
        phase_name = ph.get("phase", "").lower()
        if phase_name in phases_to_evaluate:
            # Keep the per-phase loop for later extensions, but allow
            # pure-electric missions to omit Phi or specify Phi=1.
            Phi = float(ph.get("Phi", 1.0 - phi_eps))
            Phi = min(max(Phi, phi_eps), 1.0 - phi_eps)

            #computes component W/Ps from Table 10 of the EADG paper
            w_p_out=powertrain_component_sizing.power_loading_components(w_p_sel,Phi,eta_p,eta_3,eta_1,eta_2,powertrain_type,eta_gen) # Note to #self: figure out the right order of etas
                

            #computes batt4ery power using same component sizing table as above
            w_p_out_batt=powertrain_component_sizing.WP_batt_parallel(w_p_sel, Phi, eta_p, eta_1, eta_2, eta_3) # need to make sure the etas correspond to the right component!

            #retreives EM W/P
            w_p_motor= w_p_out["W_over_Pem"] # w_p motor from powertrain_component_sizing
            w_p_te= w_p_out["W_over_Pte"] # w_p thermal engine from powertrain_component_sizing
            p_w_motor=1/w_p_motor
            p_w_te=1/w_p_te
            p_w_batt=1/w_p_out_batt
            p_w_array_te.append(p_w_te)  # collecting p/w for each misison phase
            p_w_array_batt.append(p_w_batt)# collecting p/w for each misison phase
            print(p_w_array_te)
            p_w_array_mot.append(p_w_motor) # collecting p/w for each misison phase
            if phase_name in ("climb", "cruise", "loiter","descend"):
                p_w_cont_array_mot.append(p_w_motor)
                p_w_cont_array_batt.append(p_w_batt)
    """ Determine max and continuous motor power"""
    p_w_max_mot=max(p_w_array_mot) # get max motor power
    p_w_max_cont_mot=max(p_w_cont_array_mot) # get max continuour motor power
    power_to_prop_sizing_mot=max(p_w_max_mot,1.2*p_w_max_cont_mot) #input to class 2 prop sizing 
    
    p_w_max_batt_max=max(p_w_array_batt) # get max battery power
    p_w_max_cont_batt=max(p_w_cont_array_batt) # get max continuous battery power
    power_to_prop_sizing_bat=max(p_w_max_batt_max,p_w_max_cont_batt) #input to class 2 prop sizing 
    
    p_w_max_te=max(p_w_array_te) # get max thermal engine power
    power_to_prop_sizing_te=p_w_max_te #input to class 2 prop sizing


    


    while err > tol and i < max_iter:

        # --- Update MTOM-dependent fields ---
        inputs["wing"]["W_G_kg"] = mtom_guess
        inputs["landing_gear"]["W_to_kg"] = mtom_guess
        for ph in inputs["mission"]:
            ph["MTOM_limit"] = mtom_guess

        # --- Structural weight ---
        OE = total_struct_weight_from_dict(inputs)

        E0_total, phase_results = class_1_sizing.mission_E0_bat_by_phase_electric(
            mission=mission,
            W_OE=OE,
            W_PL=payload,     
            eta_2=eta_2,
            eta_3=eta_3,
            e_bat_J_per_kg=e_bat,
            g=g,
        )
        p_rated_em= power_to_prop_sizing_mot * (mtom_guess) #Watts - check again
        em_mot_mass=class_2_battery_sizing.motor_generator_mass(p_rated_em,5.65,20000) * 2 # assuming two electric motors - replace withh N_EM parameter, asumed torque density
        #p_rated_te= power_to_prop_sizing_te * (mtom_guess) #W
        #prop_mass_out=class_2_prop_parallel_hybrid.propulsion_system_mass_parallel_hybrid( p_rated_em,p_rated_te,total_E0_fuel,N_engines,N_FuelTanks,e_f,motor_specific_power,motor_controller_specific_power)
        #prop_mass_breakddown=prop_mass_out["mass_breakdown_kg"] # prop mass breakdown is a lower level key in the results dict
        #turboprop_installed_mass=prop_mass_breakddown["Turboprops (installed)"]
        #propeller_mass=prop_mass_breakddown["Propellers"]
        #fuel_system_mass=prop_mass_breakddown["Fuel system"]
        #motor_controller_mass=prop_mass_breakddown["Motor controllers"]


        
        #prop_mass=prop_mass_out["total_mass_kg"] #kg
    
        M_batt = class_1_sizing.battery_pack_mass(E0_total, e_bat, k_bat)

        mtom_new_raw = OE + M_batt + payload + em_mot_mass
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
        "history": history,
        "total_em_mass":em_mot_mass,
        "p_rated_em": p_rated_em
        
        
    }

# -------------------------------------------------------------------------------------------------------------------------------------- #
# Beginning of special section which tailors the above two functions ( methods) for the E-19 ( all electric range + range extender case)
# -------------------------------------------------------------------------------------------------------------------------------------- #


def converge_mtom_hybrid_struct_E19(inputs):
    import class_1_sizing
    import powertrain_component_sizing
    import class_2_prop_parallel_hybrid
    import powertrain_component_sizing
    import class_2_battery_sizing
    import special_functions
    import SMP


    mission    = inputs["mission"]
    payload    = inputs["payload"]
    eta_1      = inputs["eta_1"]
    eta_2      = inputs["eta_2"]
    eta_3      = inputs["eta_3"]
    #Phi        = inputs["Phi"]
    e_bat      = inputs["e_bat"]
    e_f        = inputs["e_f"]
    k_bat      = inputs["k_bat"]
    constraint_analysis_inputs = inputs["constraint_analysis_inputs"]
    mtom_guess = inputs["mtom_guess"]
    engine = inputs["engine"]
    powertrain_type=inputs["powertrain_type"]
    eta_p=inputs["eta_p"]
    eta_gb=inputs["eta_gb"]
    eta_gen=engine["eta_gen"]
    phases_to_evaluate=inputs["phases_to_evaluate"]
    energy_allowances=233.28e+06 #Joules
    


    

    w_p_sel=inputs["w_p_sel"]

    
    k_n = engine["k_n"]
    thrust_reverser = engine["thrust_reverser"]

    E_fuel = engine["E_fuel"] #fuel energy in Joules
    N_engines = engine["N_engines"] #number of engines
    N_FuelTanks = engine["N_FuelTanks"] #number of fuel tanks

    fuel_specific_energy = engine["fuel_specific_energy_J_per_kg"] #fuel specific energy
    motor_specific_power = engine["motor_specific_power_W_per_kg"] #motor specific energy
    motor_controller_specific_power = engine["motor_controller_specific_power_W_per_kg"] #motor controller specific energy
    wf=0
    p_w_array_mot=[]
    p_w_cont_array_mot=[]
    p_w_array_te=[]
    p_w_array_batt=[]
    #p_w_cont_array_te=[]
    p_w_cont_array_batt=[]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)

    err = 1e9
    i = 0
    history = []
    mtom_tracker=[] #debugging variable
    for ph in mission:
        phase_name = ph.get("phase", "").lower()
        if phase_name in phases_to_evaluate:
            Phi = float(ph["Phi"])
        
            w_p_out=powertrain_component_sizing.power_loading_components(w_p_sel,Phi,eta_p,eta_3,eta_1,eta_2,powertrain_type,eta_gen) # Note to self: figure out the right order of etas
             
            w_p_out_batt=powertrain_component_sizing.WP_batt_parallel(w_p_sel, Phi, eta_p, eta_1, eta_2, eta_3) # need to make sure the etas correspond to the right component!
            w_p_motor= w_p_out["W_over_Pem"] # w_p motor from powertrain_component_sizing
            
            w_p_te= w_p_out["W_over_Pte"] # w_p thermal engine from powertrain_component_sizing
            p_w_motor=1/w_p_motor
            p_w_te=1/w_p_te
            p_w_batt=1/w_p_out_batt
            p_w_array_te.append(p_w_te)  # collecting p/w for each misison phase
            p_w_array_batt.append(p_w_batt)# collecting p/w for each misison phase
            #print("thermal engine power is",p_w_array_te)
            #print("thermal engine power is",p_w_array_te)
            p_w_array_mot.append(p_w_motor) # collecting p/w for each misison phase
            #print("thermal engine power is",p_w_array_mot)
            if phase_name in ("climb", "cruise", "loiter","ifr"):
                p_w_cont_array_mot.append(p_w_motor)
                
                p_w_cont_array_batt.append(p_w_batt)
                if phase_name in ("ifr"):
                    w_p_te = special_functions.cruise_w_p_from_dicts(mission, constraint_analysis_inputs, phase_name="ifr")["W_P_cruise"]
                    p_w_array_mot.pop()
                    p_w_cont_array_mot.pop()
                    loiter_out = special_functions.conventional_breguet_loiter_weight_fraction(45.0 * 60.0, float(ph.get("loiter_speed", ph.get("cruise_speed", constraint_analysis_inputs["cruise_speed"]))), float(ph["l_d"]), float(constraint_analysis_inputs["eta_total"]), float(e_f), float(g))

                    fuel_fraction = special_functions.breguet_fuel_fraction_from_phase(ph, constraint_analysis_inputs, fuel_specific_energy_J_per_kg=e_f)["fuel_fraction"]

    """ Determine max and continuous motor power"""
    p_w_max_mot=max(p_w_array_mot) # get max motor power
    p_w_max_cont_mot=max(p_w_cont_array_mot) # get max continuour motor power
    power_to_prop_sizing_mot=max(p_w_max_mot,1.2*p_w_max_cont_mot) #input to class 2 prop sizing 
    
    p_w_max_batt_max=max(p_w_array_batt) # get max battery power
    p_w_max_cont_batt=max(p_w_cont_array_batt) # get max continuous battery power
    power_to_prop_sizing_bat=max(p_w_max_batt_max,p_w_max_cont_batt) #input to class 2 prop sizing 
    
    p_w_max_te=max(p_w_array_te) # get max thermal engine power
    power_to_prop_sizing_te=p_w_max_te #input to class 2 prop sizing

    aux_power_out = special_functions.subsystem_power_energy_from_class2_inputs(inputs)
    energy_aux_power=aux_power_out["total_energy_j"]["total"]

    

    systems_out = special_functions.installed_system_weights_from_class2_inputs(inputs)
    total_systems_weight_kg = systems_out["total_weight_kg"]

    sys_weight_breakdown=systems_out["weight_breakdown_kg"]
    #print("total systems weight is",total_systems_weight_kg)
    #print("sys_weight_breakdown",sys_weight_breakdown)


    total_fuel_mass = 0.0
    E0_total = 0.0
    phase_results = []
    OE = None
    M_batt = None
    em_mot_mass = None
    p_rated_em = None
    p_rated_te = None
    prop_mass = None
    prop_mass_breakddown = None

    while err > tol and i < max_iter:

        # --- Update MTOM-dependent fields ---
        inputs["wing"]["W_G_kg"] = mtom_guess
        inputs["landing_gear"]["W_to_kg"] = mtom_guess
        for ph in inputs["mission"]:
            ph["MTOM_limit"] = mtom_guess

        # --- Structural weight ---
        OE = total_struct_weight_from_dict(inputs)

        E0_total, phase_results,total_fuel,total_bat,total_E0_bat,total_E0_fuel = class_1_sizing.mission_E0_bat_by_phase_hybrid(
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
        
        breguet_fuel=fuel_fraction*mtom_guess 
        loiter_fuel_mass_kg = loiter_out["fuel_fraction"] * mtom_guess
        updated_fuel_E0= total_E0_fuel+(breguet_fuel+loiter_fuel_mass_kg)*e_f
        p_rated_em= power_to_prop_sizing_mot * (mtom_guess) * g   #w
        p_rated_te= (1/w_p_te) * (mtom_guess) * g  #W
        prop_mass_out=class_2_prop_parallel_hybrid.propulsion_system_mass_parallel_hybrid( p_rated_em,p_rated_te,updated_fuel_E0,N_engines,N_FuelTanks,e_f,motor_specific_power,motor_controller_specific_power)
        prop_mass_breakddown=prop_mass_out["mass_breakdown_kg"] # prop mass breakdown is a lower level key in the results dict
        turboprop_installed_mass=prop_mass_breakddown["Turboprops (installed)"]
        propeller_mass=prop_mass_breakddown["Propellers"]
        fuel_system_mass=prop_mass_breakddown["Fuel system"]
        motor_controller_mass=prop_mass_breakddown["Motor controllers"]
        
        
       

        #print("endurance fuel is",loiter_fuel_mass_kg)
        m_electric_motors_kg = prop_mass_breakddown["Electric motors"]


        
        prop_mass= turboprop_installed_mass+propeller_mass+fuel_system_mass+motor_controller_mass+m_electric_motors_kg   #prop_mass_out["total_mass_kg"] #kg
    
        #M_batt = class_1_sizing.battery_pack_mass(total_E0_bat, e_bat, k_bat) # still using class 1 battery sizing - if n_parallel,n_series and E_bat_cell are known then // use battery_pack_mass_from_cells from class 2 battery_sizing //
        M_batt = class_2_battery_sizing. battery_pack_mass_from_cells((total_E0_bat +energy_allowances+ energy_aux_power)/(128*40),e_bat,128,40,k_bat) #ns=128, np=40 ( Assuming redundant packs as a single pack) from Chin et al. (2019), Battery performance modelling on the X-57 Maxwell (https://openmdao.org/pubs/chin_battery_performance_x57_2019.pdf - Table 1)
        
 

        mtom_new_raw = OE + M_batt + payload + total_fuel + prop_mass+breguet_fuel+loiter_fuel_mass_kg+ total_systems_weight_kg
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
        "total_bat":total_bat,
        "propulsion_mass":prop_mass,
        "turboprop_installed_mass":turboprop_installed_mass,
        "propeller_mass":propeller_mass,
        "fuel_system_mass": fuel_system_mass,
        "motor_controller_mass": motor_controller_mass,
        "p_rated_em": p_rated_em,
        "p_rated_te":p_rated_te,
        
        
    }


def converge_mtom_electric_struct_E19(inputs):
    import class_1_sizing
    import powertrain_component_sizing
    import class_2_prop_parallel_hybrid
    import powertrain_component_sizing
    import class_2_battery_sizing
    import special_functions
    import SMP


    mission    = inputs["mission"]
    payload    = inputs["payload"]
    eta_1      = inputs["eta_1"]
    eta_2      = inputs["eta_2"]
    eta_3      = inputs["eta_3"]
    #Phi        = inputs["Phi"]
    e_bat      = inputs["e_bat"]
    e_f        = inputs["e_f"]
    k_bat      = inputs["k_bat"]
    constraint_analysis_inputs = inputs["constraint_analysis_inputs"]
    mtom_guess = inputs["mtom_guess"]
    engine = inputs["engine"]
    powertrain_type=inputs["powertrain_type"]
    eta_p=inputs["eta_p"]
    eta_gb=inputs["eta_gb"]
    eta_gen=engine["eta_gen"]
    phases_to_evaluate=inputs["phases_to_evaluate"]
    energy_allowances=233.28e+06 #Joules
    


    

    w_p_sel=inputs["w_p_sel"]

    
    k_n = engine["k_n"]
    thrust_reverser = engine["thrust_reverser"]

    E_fuel = engine["E_fuel"] #fuel energy in Joules
    N_engines = engine["N_engines"] #number of engines
    N_FuelTanks = engine["N_FuelTanks"] #number of fuel tanks

    fuel_specific_energy = engine["fuel_specific_energy_J_per_kg"] #fuel specific energy
    motor_specific_power = engine["motor_specific_power_W_per_kg"] #motor specific energy
    motor_controller_specific_power = engine["motor_controller_specific_power_W_per_kg"] #motor controller specific energy
    wf=0
    p_w_array_mot=[]
    p_w_cont_array_mot=[]
    p_w_array_te=[]
    p_w_array_batt=[]
    #p_w_cont_array_te=[]
    p_w_cont_array_batt=[]

    g        = inputs.get("g", 9.81)
    tol      = inputs.get("tol", 1.0)
    max_iter = inputs.get("max_iter", 100)
    relax    = inputs.get("relax", 1.0)

    err = 1e9
    i = 0
    history = []
    mtom_tracker=[] #debugging variable
    for ph in mission:
        phase_name = ph.get("phase", "").lower()
        if phase_name in phases_to_evaluate:
            Phi = float(ph["Phi"])
        
            w_p_out=powertrain_component_sizing.power_loading_components(w_p_sel,Phi,eta_p,eta_3,eta_1,eta_2,powertrain_type,eta_gen) # Note to self: figure out the right order of etas
             
            w_p_out_batt=powertrain_component_sizing.WP_batt_parallel(w_p_sel, Phi, eta_p, eta_1, eta_2, eta_3) # need to make sure the etas correspond to the right component!
            w_p_motor= w_p_out["W_over_Pem"] # w_p motor from powertrain_component_sizing
            
            w_p_te= powertrain_component_sizing.WP_therm_eng_parallel_alt(w_p_sel, Phi, eta_p, eta_3, eta_1, eta_2) # alternate w_p thermal engine from powertrain_component_sizing
            p_w_motor=1/w_p_motor
            p_w_te=1/w_p_te
            p_w_batt=1/w_p_out_batt
            p_w_array_te.append(p_w_te)  # collecting p/w for each misison phase
            p_w_array_batt.append(p_w_batt)# collecting p/w for each misison phase
            #print("thermal engine power is",p_w_array_te)
            #print("thermal engine power is",p_w_array_te)
            p_w_array_mot.append(p_w_motor) # collecting p/w for each misison phase
            #print("thermal engine power is",p_w_array_mot)
            if phase_name in ("climb", "cruise", "loiter","ifr"):
                p_w_cont_array_mot.append(p_w_motor)
                
                p_w_cont_array_batt.append(p_w_batt)
                if phase_name in ("ifr"):
                    w_p_te = special_functions.cruise_w_p_from_dicts(mission, constraint_analysis_inputs, phase_name="ifr")["W_P_cruise"]
                    p_w_array_mot.pop()
                    p_w_cont_array_mot.pop()
                    loiter_out = special_functions.conventional_breguet_loiter_weight_fraction(45.0 * 60.0, float(ph.get("loiter_speed", ph.get("cruise_speed", constraint_analysis_inputs["cruise_speed"]))), float(ph["l_d"]), float(constraint_analysis_inputs["eta_total"]), float(e_f), float(g))

                    fuel_fraction = special_functions.breguet_fuel_fraction_from_phase(ph, constraint_analysis_inputs, fuel_specific_energy_J_per_kg=e_f)["fuel_fraction"]

    """ Determine max and continuous motor power"""
    p_w_max_mot=max(p_w_array_mot) # get max motor power
    p_w_max_cont_mot=max(p_w_cont_array_mot) # get max continuour motor power
    power_to_prop_sizing_mot=max(p_w_max_mot,1.2*p_w_max_cont_mot) #input to class 2 prop sizing 
    
    p_w_max_batt_max=max(p_w_array_batt) # get max battery power
    p_w_max_cont_batt=max(p_w_cont_array_batt) # get max continuous battery power
    power_to_prop_sizing_bat=max(p_w_max_batt_max,p_w_max_cont_batt) #input to class 2 prop sizing 
    
    p_w_max_te=max(p_w_array_te) # get max thermal engine power
    power_to_prop_sizing_te=p_w_max_te #input to class 2 prop sizing

    aux_power_out = special_functions.subsystem_power_energy_from_class2_inputs(inputs)
    energy_aux_power=aux_power_out["total_energy_j"]["total"]

    

    systems_out = special_functions.installed_system_weights_from_class2_inputs(inputs)
    total_systems_weight_kg = systems_out["total_weight_kg"]

    sys_weight_breakdown=systems_out["weight_breakdown_kg"]
    #print("total systems weight is",total_systems_weight_kg)
    #print("sys_weight_breakdown",sys_weight_breakdown)


    total_fuel_mass = 0.0
    E0_total = 0.0
    phase_results = []
    OE = None
    M_batt = None
    em_mot_mass = None
    p_rated_em = None
    p_rated_te = None
    prop_mass = None
    prop_mass_breakddown = None

    while err > tol and i < max_iter:

        # --- Update MTOM-dependent fields ---
        inputs["wing"]["W_G_kg"] = mtom_guess
        inputs["landing_gear"]["W_to_kg"] = mtom_guess
        for ph in inputs["mission"]:
            ph["MTOM_limit"] = mtom_guess

        # --- Structural weight ---
        OE = total_struct_weight_from_dict(inputs)

        E0_total, phase_results,total_fuel,total_bat,total_E0_bat,total_E0_fuel = class_1_sizing.mission_E0_bat_by_phase_hybrid(
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
        
        breguet_fuel=fuel_fraction*mtom_guess 
        loiter_fuel_mass_kg = loiter_out["fuel_fraction"] * mtom_guess
        updated_fuel_E0= total_E0_fuel+(breguet_fuel+loiter_fuel_mass_kg)*e_f
        p_rated_em= power_to_prop_sizing_mot * (mtom_guess) * g   #w
        p_rated_te= (1/w_p_te) * (mtom_guess) * g  #W
        
        prop_mass_out=class_2_prop_parallel_hybrid.propulsion_system_mass_parallel_hybrid(p_rated_em,p_rated_te,updated_fuel_E0,N_engines,N_FuelTanks,e_f,motor_specific_power,motor_controller_specific_power)
        prop_mass_breakddown=prop_mass_out["mass_breakdown_kg"] # prop mass breakdown is a lower level key in the results dict
        turboprop_installed_mass=prop_mass_breakddown["Turboprops (installed)"]
        propeller_mass=prop_mass_breakddown["Propellers"]
        fuel_system_mass=prop_mass_breakddown["Fuel system"]
        motor_controller_mass=prop_mass_breakddown["Motor controllers"]
        
        
       

        #print("endurance fuel is",loiter_fuel_mass_kg)
        m_electric_motors_kg = prop_mass_breakddown["Electric motors"]


        
        prop_mass= turboprop_installed_mass+propeller_mass+fuel_system_mass+motor_controller_mass+m_electric_motors_kg   #prop_mass_out["total_mass_kg"] #kg
    
        #M_batt = class_1_sizing.battery_pack_mass(total_E0_bat, e_bat, k_bat) # still using class 1 battery sizing - if n_parallel,n_series and E_bat_cell are known then // use battery_pack_mass_from_cells from class 2 battery_sizing //
        M_batt = class_2_battery_sizing. battery_pack_mass_from_cells((total_E0_bat +energy_allowances+ energy_aux_power)/(128*40),e_bat,128,40,k_bat) #ns=128, np=40 ( Assuming redundant packs as a single pack) from Chin et al. (2019), Battery performance modelling on the X-57 Maxwell (https://openmdao.org/pubs/chin_battery_performance_x57_2019.pdf - Table 1)
        
 

        mtom_new_raw = OE + M_batt + payload + total_fuel + prop_mass+breguet_fuel+loiter_fuel_mass_kg+ total_systems_weight_kg
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
        "total_bat":total_bat,
        "propulsion_mass":prop_mass,
        "turboprop_installed_mass":turboprop_installed_mass,
        "propeller_mass":propeller_mass,
        "fuel_system_mass": fuel_system_mass,
        "motor_controller_mass": motor_controller_mass,
        "p_rated_em": p_rated_em,
        "p_rated_te":p_rated_te,
        
        
    }
