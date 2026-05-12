import math
import numpy as np


# Roskam's climb equations are written in imperial units, so these
# conversions are used inside the helper functions and then converted
# back to SI at the end.
N_M2_PER_PSF = 47.88025898
N_M2_TO_LBF_FT2 = 1.0 / N_M2_PER_PSF
HP_PER_LBF_TO_W_PER_N = 167.94
FPM_PER_MPS = 196.850394
KTS_PER_MPS = 1.9438444924406046


def FAR_23_climb_rate_roskam(
    eta_p,
    W_S_array,
    roc,
    rho_alt,
    rho_sea,
    cl32_cd=None,
    cl_climb=None,
    cd_climb=None,
    A=None,
    e_os=None,
    CD_0=None,
):
    """
    Roskam FAR 23 rate-of-climb sizing using Eq. (3.24).

    Internal units:
    - RC in ft/min
    - W/S in lbf/ft^2
    - P/W in hp/lbf

    Final output:
    - P/W in W/N
    """
    if eta_p <= 0:
        raise ValueError("eta_p must be > 0")
    if rho_alt <= 0 or rho_sea <= 0:
        raise ValueError("rho_alt and rho_sea must be > 0")

    W_S_array = np.asarray(W_S_array, dtype=float)
    roc = np.asarray(roc, dtype=float)

    if cl32_cd is None:
        if cl_climb is not None and cd_climb is not None:
            cl32_cd = (cl_climb ** 1.5) / cd_climb
        else:
            if A is None or e_os is None or CD_0 is None:
                raise ValueError(
                    "Provide cl32_cd directly, or provide (cl_climb, cd_climb), "
                    "or provide (A, e_os, CD_0)."
                )
            cl32_cd = 1.345 * (A * e_os) ** 0.75 / (CD_0 ** 0.25)

    sigma = rho_alt / rho_sea
    W_S_lb_ft2 = W_S_array * N_M2_TO_LBF_FT2

    # Roskam's rate-of-climb parameter RCP is defined in hp/lbf.
    rcp = (roc * FPM_PER_MPS) / 33000.0

    # Breaking down equation 3.24 to make it easier to solve
   
    A=rcp+np.sqrt(W_S_lb_ft2)
    B=19.0 * cl32_cd * np.sqrt(sigma)
    C= A/B
    W_P=eta_p/C
    #drag_term = np.sqrt(W_S_lb_ft2) / (19.0 * cl32_cd * np.sqrt(sigma))

    # invert for P/W, still in hp/lbf at this point.
    p_w_hp_per_lbf = 1/W_P
    return p_w_hp_per_lbf * HP_PER_LBF_TO_W_PER_N


def FAR_23_climb_gradient_roskam(
    eta_p,
    W_S_array,
    cgr,
    rho_alt,
    rho_sea,
    cl_climb=None,
    cd_climb=None,
    cl_max=None,
    A=None,
    e_os=None,
    CD_0=None,
    cl_margin=0.2,
):
    """
    Roskam FAR 23 climb-gradient sizing using Eq. (3.29) and (3.30).

    Internal units:
    - W/S in lbf/ft^2
    - P/W in hp/lbf

    Final output:
    - P/W in W/N
    """
    if eta_p <= 0:
        raise ValueError("eta_p must be > 0")
    if rho_alt <= 0 or rho_sea <= 0:
        raise ValueError("rho_alt and rho_sea must be > 0")
    if cgr < 0:
        raise ValueError("cgr must be >= 0")

    W_S_array = np.asarray(W_S_array, dtype=float)

    if cl_climb is None or cd_climb is None:
        if cl_max is None or A is None or e_os is None or CD_0 is None:
            raise ValueError(
                "Provide (cl_climb, cd_climb) or provide (cl_max, A, e_os, CD_0)."
            )
        cl_climb = cl_max - cl_margin
        if cl_climb <= 0:
            raise ValueError("cl_climb must be > 0")
        cd_climb = CD_0 + cl_climb ** 2 / (math.pi * A * e_os)

    if cl_climb <= 0 or cd_climb <= 0:
        raise ValueError("cl_climb and cd_climb must be > 0")

    sigma = rho_alt / rho_sea
    W_S_lb_ft2 = W_S_array * N_M2_TO_LBF_FT2

    # Eq. (3.29): convert the climb-gradient requirement into Roskam's
    # intermediate climb-gradient parameter CGRP.
    cgrp = (cgr + cd_climb / cl_climb) / math.sqrt(cl_climb)

    # Eq. (3.30): solve for power loading in hp/lbf.
    p_w_hp_per_lbf = cgrp * np.sqrt(W_S_lb_ft2) / (18.97 * eta_p * math.sqrt(sigma))
    return p_w_hp_per_lbf * HP_PER_LBF_TO_W_PER_N


def _safe_inverse(values):
    values = np.asarray(values, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(values != 0.0, 1.0 / values, np.nan)


def constraints_raymer(input_dict):
    
    # Raymer-style and the added Roskam FAR 23 climb sizing.
    rho = input_dict["density"]
    v_stall = input_dict["stall_speed"]
    quarter_sweep = input_dict["Quarter chord sweep"]
    landing_dist = input_dict["landing_distance"]
    rho_ratio = input_dict["rho_ratio"]
    aircraft_type = input_dict["aircraft_type"]
    propulsion_type = input_dict["propulsion_type"]
    v_cruise = input_dict["cruise_speed"]
    AR = input_dict["AR"]
    C_D0 = input_dict["CD_0"]
    CL_max_to = input_dict["CL_max_to"]
    CL_max = input_dict["CL_max"]
    cgr = input_dict["climb_gradient"]
    roc = input_dict["rate_of_climb"]
    rho_ceiling = input_dict["rho_ceiling"]
    rho_cruise = input_dict["rho_cruise"]
    rho_climb = input_dict["rho_climb"]
    e_os = input_dict["oswald efficiency"]
    cl_max_foil = input_dict["cl_max_foil"]
    eta_p = input_dict["propeller_efficiency"]
    v_max = input_dict.get("max_speed", v_cruise)
    rho_max_speed = input_dict.get("rho_max_speed", rho)
    sigma_max_speed = input_dict.get("sigma_max_speed")
    rho_loiter_alt=input_dict.get("rho_loiter_alt")

    if aircraft_type in ["General aviation (single engine)", "General aviation (Twin engine)"]:
        S_a = 183
    elif aircraft_type in ["Civil jets", "Twin turboprop"]:
        S_a = 305
    else:
        raise ValueError("Data point not available for this aircraft type")

    lamda_025c = math.radians(quarter_sweep)

    if cl_max_foil is not None:
        CL_max_to = 0.9 * cl_max_foil * math.cos(lamda_025c)

    if propulsion_type == "jet":
        landing_factor = 0.85
        W_S_cruise_max_range = (0.5 * rho_cruise * v_cruise**2) * math.sqrt(math.pi * AR * C_D0 / 3)
    else:
        landing_factor = 1.0
        W_S_cruise_max_range = (0.5 * rho_cruise * v_cruise**2) * math.sqrt(math.pi * AR * C_D0)

    # Wing-loading limits 
    W_S_stall = 0.5 * rho * v_stall**2 * CL_max_to
    W_S_landing = ((landing_dist - S_a) * (rho_ratio * landing_factor * CL_max) / 5)*9.81 # converting to N/m2 - since apparaently eq 5.11 in Raymer is in kg/m2 for wingloading
    W_S_ceiling = 0.5 * rho_ceiling *v_cruise**2 * math.sqrt(math.pi*AR*e_os*C_D0)
    W_S_loiter= 0.5 * rho_loiter_alt *0.75*v_cruise**2 * math.sqrt(3*math.pi*AR*e_os*C_D0)

    K = 1.0 / (math.pi * AR * e_os)

    W_S_max = max(W_S_stall, W_S_landing, W_S_ceiling,W_S_loiter)
    W_S_array = np.arange(1, int(1.1 * W_S_max) + 10, 10, dtype=float)

    #  Raymer climb relation 
  
    v_climb = roc / cgr if cgr != 0 else 0.0
    D_W = ((0.5 * rho_climb * v_climb**2 * C_D0) / W_S_array) + (
        W_S_array / (e_os * 0.5 * np.pi * AR * rho_climb * v_climb**2)
    )
    T_W_climb = cgr + D_W

    P_W_climb = None
    W_P_climb = None
    W_P_max_speed = None
    P_W_max_speed = None
    P_W_climb_aeo_roc = None
    W_P_climb_aeo_roc = None
    P_W_climb_aeo_cgr = None
    W_P_climb_aeo_cgr = None
    P_W_climb_aeo = None
    W_P_climb_aeo = None
    P_W_climb_oei_one_engine_5000 = None
    W_P_climb_oei_one_engine_5000 = None
    P_W_climb_oei_5000 = None
    W_P_climb_oei_5000 = None
    P_W_climb_oei = None
    W_P_climb_oei = None

    if propulsion_type == "prop":
        # The Roskam FAR 23 implementation 
        #
        # AEO ROC 
        # Uses the base drag polar already passed into constraints_raymer.
        cd0_aeo_roc = C_D0

        # AEO CGR 
        # Use the takeoff CLmax already available and Roskam's suggested
        # 0.2 margin to define the climb CL.
        cd0_aeo_cgr = C_D0
        cl_max_for_aeo_cgr = CL_max_to
        cl_margin_from_stall = 0.2

        # OEI ROC case:
        # Use the climb density as the inoperative-engine altitude density,
        # the clean CLmax already supplied to the function, and Roskam's
        # FAR 23.67 relation RC > 0.027 * Vso^2.
        cd0_oei_roc = C_D0
        rho_oei = rho_climb
        cl_max_for_oei = CL_max
        oei_rc_factor = 0.027

        

        total_engines = 2

        # Convert the 5000 ft OEI result to an equivalent sea-level AEO
        
        density_power_ratio = rho_oei / rho

        P_W_climb_aeo_roc = FAR_23_climb_rate_roskam(
            eta_p=eta_p,
            W_S_array=W_S_array,
            roc=roc,
            rho_alt=rho_climb,
            rho_sea=rho,
            A=AR,
            e_os=e_os,
            CD_0=cd0_aeo_roc,
        )
        W_P_climb_aeo_roc = _safe_inverse(P_W_climb_aeo_roc)

        P_W_climb_aeo_cgr = FAR_23_climb_gradient_roskam(
            eta_p=eta_p,
            W_S_array=W_S_array,
            cgr=cgr,
            rho_alt=rho_climb,
            rho_sea=rho,
            cl_max=cl_max_for_aeo_cgr,
            A=AR,
            e_os=e_os,
            CD_0=cd0_aeo_cgr,
            cl_margin=cl_margin_from_stall,
        )
        W_P_climb_aeo_cgr = _safe_inverse(P_W_climb_aeo_cgr)

        # The AEO climb requirement is the more demanding of the AEO rate-of-
        # climb and AEO climb-gradient constraints at each wing loading.
        P_W_climb_aeo = np.maximum(P_W_climb_aeo_roc, P_W_climb_aeo_cgr)
        W_P_climb_aeo = _safe_inverse(P_W_climb_aeo)

        # For FAR 23.67, Roskam computes the OEI rate-of-climb requirement
        # from Vso at the OEI altitude, with Vso in knots.
        V_so_oei = np.sqrt(2.0 * W_S_array / (rho_oei * cl_max_for_oei))
        V_so_oei_kts = V_so_oei * KTS_PER_MPS
        roc_oei = (oei_rc_factor * V_so_oei_kts**2) / FPM_PER_MPS

        P_W_climb_oei_one_engine_5000 = FAR_23_climb_rate_roskam(
            eta_p=eta_p,
            W_S_array=W_S_array,
            roc=roc_oei,
            rho_alt=rho_oei,
            rho_sea=rho,
            A=AR,
            e_os=e_os,
            CD_0=cd0_oei_roc,
        )
        W_P_climb_oei_one_engine_5000 = _safe_inverse(P_W_climb_oei_one_engine_5000)

        # Convert one-engine-operating power loading to an equivalent all-engine
        # installed loading. For a twin, this multiplies P/W by 2.
        if total_engines > 1:
            P_W_climb_oei_5000 = P_W_climb_oei_one_engine_5000 * (total_engines / (total_engines - 1))
        else:
            P_W_climb_oei_5000 = P_W_climb_oei_one_engine_5000.copy()
        W_P_climb_oei_5000 = _safe_inverse(P_W_climb_oei_5000)

        if density_power_ratio <= 0:
            raise ValueError("density ratio rho_climb / density must be > 0")

        # Bring the OEI altitude result back to an equivalent sea-level loading
        # using the density ratio derived from the supplied densities.
        P_W_climb_oei = P_W_climb_oei_5000 / density_power_ratio
        W_P_climb_oei = _safe_inverse(P_W_climb_oei)

        # The prop climb curve used by the rest of the module is the more
        # restrictive of the AEO and OEI climb requirements.
        P_W_climb = np.maximum(P_W_climb_aeo, P_W_climb_oei)
        W_P_climb = _safe_inverse(P_W_climb)

        if sigma_max_speed is None:
            sigma_max_speed = rho_max_speed / rho if rho else 1.0

        with np.errstate(divide="ignore", invalid="ignore"):
            # Maximum-speed power loading from the standard drag-power balance.
            max_speed_denominator = (
                0.5 * rho_max_speed * v_max**3 * C_D0 * (1.0 / W_S_array)
                + (2.0 * K / (rho_max_speed * v_max)) * W_S_array
            )
            W_P_max_speed = (sigma_max_speed * eta_p) / max_speed_denominator
            P_W_max_speed = _safe_inverse(W_P_max_speed)

    return {
        "W_S_stall": W_S_stall,
        "W_S_landing": W_S_landing,
        "W_S_ceiling": W_S_ceiling,
        "W_S_cruise_max_range": W_S_cruise_max_range,
        "W_S_loiter": W_S_loiter,
        "W_S_array": W_S_array,
        "T_W_climb": T_W_climb,
        "P_W_climb": P_W_climb,
        "W_P_climb": W_P_climb,
        "P_W_climb_aeo_roc": P_W_climb_aeo_roc,
        "W_P_climb_aeo_roc": W_P_climb_aeo_roc,
        "P_W_climb_aeo_cgr": P_W_climb_aeo_cgr,
        "W_P_climb_aeo_cgr": W_P_climb_aeo_cgr,
        "P_W_climb_aeo": P_W_climb_aeo,
        "W_P_climb_aeo": W_P_climb_aeo,
        "P_W_climb_oei_one_engine_5000": P_W_climb_oei_one_engine_5000,
        "W_P_climb_oei_one_engine_5000": W_P_climb_oei_one_engine_5000,
        "P_W_climb_oei_5000": P_W_climb_oei_5000,
        "W_P_climb_oei_5000": W_P_climb_oei_5000,
        "P_W_climb_oei": P_W_climb_oei,
        "W_P_climb_oei": W_P_climb_oei,
        "W_P_max_speed": W_P_max_speed,
        "P_W_max_speed": P_W_max_speed,
    }


def plot_constraint_diagram(constraint_results, input_dict):
    """
    Plot constraint diagram directly from constraints_raymer() output.

    Parameters
    ----------
    constraint_results : dict
        Output dictionary from constraints_raymer()
    input_dict : dict
        Aircraft input dictionary, must contain 'propulsion_type'

    Returns
    -------
    dict
        Feasibility and selected design point information
    """
    import matplotlib.pyplot as plt

    W_S_stall = constraint_results["W_S_stall"]
    W_S_landing = constraint_results["W_S_landing"]
    W_S_ceiling = constraint_results["W_S_ceiling"]
    W_S_array = constraint_results["W_S_array"]
    T_W_climb = constraint_results["T_W_climb"]
    P_W_climb = constraint_results["P_W_climb"]
    P_W_max_speed = constraint_results.get("P_W_max_speed")
    P_W_climb_aeo_roc = constraint_results.get("P_W_climb_aeo_roc")
    P_W_climb_aeo_cgr = constraint_results.get("P_W_climb_aeo_cgr")
    P_W_climb_aeo = constraint_results.get("P_W_climb_aeo")
    P_W_climb_oei_one_engine_5000 = constraint_results.get("P_W_climb_oei_one_engine_5000")
    P_W_climb_oei_5000 = constraint_results.get("P_W_climb_oei_5000")
    P_W_climb_oei = constraint_results.get("P_W_climb_oei")
    W_S_loiter= constraint_results.get("W_S_loiter")
    propulsion_type = input_dict["propulsion_type"]

    WS_limit = min(W_S_stall, W_S_landing, W_S_ceiling,W_S_loiter)
    mask = W_S_array <= WS_limit

    results = {
        "feasible": False,
        "WS_star": None,
        "TW_star": None,
        "PW_star": None,
    }

    if propulsion_type == "jet":
        if T_W_climb is None:
            raise ValueError("T_W_climb is missing from constraint_results.")

        plt.figure(figsize=(8, 6))
        plt.plot(W_S_array, T_W_climb, linewidth=2, label="Climb")

        plt.axvline(W_S_stall, color="k", linewidth=3, linestyle="--", label="Stall")
        plt.axvline(W_S_landing, color="k", linewidth=3, linestyle="-.", label="Landing")
        plt.axvline(W_S_ceiling, color="k", linewidth=3, linestyle=":", label="Ceiling")

        if np.any(mask):
            y_top = 1.1 * np.max(T_W_climb)
            plt.fill_between(W_S_array[mask], T_W_climb[mask], y_top, alpha=0.15, label="Feasible")

            i = np.argmin(T_W_climb[mask])
            WS_star = W_S_array[mask][i]
            TW_star = T_W_climb[mask][i]

            plt.plot(WS_star, TW_star, "ko", markersize=7, label=f"Design Point ({WS_star:.0f}, {TW_star:.3f})")

            results["feasible"] = True
            results["WS_star"] = WS_star
            results["TW_star"] = TW_star

        plt.xlabel("Wing Loading W/S [N/m²]")
        plt.ylabel("Thrust Loading T/W [-]")
        plt.grid(True)
        plt.legend()
        plt.ylim(0, 1.1 * np.max(T_W_climb))
        plt.xlim(0, 1.05 * max(W_S_stall, W_S_landing, W_S_ceiling))
        plt.show()

    else:
        if P_W_climb is None:
            raise ValueError("P_W_climb is missing from constraint_results.")

        # Set this to True when you want the max-speed constraint back on the
        # diagram and included in the power-loading envelope.
        include_max_speed_constraint = True

        plt.figure(figsize=(8, 6))

        # Plot the individual prop-aircraft power-loading constraints 
        
        prop_curves = [
            ("AEO ROC", P_W_climb_aeo_roc, {"linestyle": "--", "linewidth": 1.8}),
            ("AEO CGR", P_W_climb_aeo_cgr, {"linestyle": "-.", "linewidth": 1.8}),
            ("AEO Climb Envelope", P_W_climb_aeo, {"linestyle": ":", "linewidth": 2.0}),
            ("OEI 5000 ft (One Engine)", P_W_climb_oei_one_engine_5000, {"linestyle": "--", "linewidth": 1.5}),
            ("OEI 5000 ft (Installed)", P_W_climb_oei_5000, {"linestyle": "-.", "linewidth": 1.8}),
            ("OEI Sea-Level Equivalent", P_W_climb_oei, {"linestyle": ":", "linewidth": 2.0}),
        ]
        if include_max_speed_constraint:
            prop_curves.append(("Max speed", P_W_max_speed, {"linestyle": "-", "linewidth": 2.0}))
        for label, curve, style in prop_curves:
            if curve is not None:
                plt.plot(W_S_array, curve, label=label, **style)

        # Plot the combined climb envelope 
        plt.plot(W_S_array, P_W_climb, linewidth=2.5, color="k", label="Climb Envelope")

        plt.axvline(W_S_stall, color="k", linewidth=3, linestyle="--", label="Stall")
        plt.axvline(W_S_landing, color="k", linewidth=3, linestyle="-.", label="Landing")
        plt.axvline(W_S_ceiling, color="k", linewidth=3, linestyle=":", label="Ceiling")
        plt.axvline(W_S_loiter, color="k", linewidth=3, linestyle="-.", label="Loiter")

       

    # Re-enable the
        # toggle above to bring max speed back into the sizing envelope.
        P_W_required = P_W_climb
        if include_max_speed_constraint and P_W_max_speed is not None:
            P_W_required = np.maximum(P_W_required, P_W_max_speed)
        visible_mask = mask & (W_S_array >= 0.5 * WS_limit)
        if np.any(visible_mask):
            y_top = 1.1 * np.max(P_W_required[visible_mask])
            x_min = 0.5 * WS_limit
        elif np.any(mask):
            y_top = 1.1 * np.max(P_W_required[mask])
            x_min = 0.0
        if np.any(mask):
            plt.fill_between(W_S_array[mask], P_W_required[mask], y_top, alpha=0.15, label="Feasible")

            #i = np.argmin(P_W_required[mask])  # these push the design point to the lowest possible ( unrealistic W/S values)
            #WS_star = W_S_array[mask][i]
            #PW_star = P_W_required[mask][i]

            WS_star = 0.95*WS_limit # Applying a small margin so the selected point isnt on the stall line
            i = np.argmin(np.abs(W_S_array - WS_star))
            PW_star = P_W_required[i]


            plt.plot(WS_star, PW_star, "ko", markersize=7, label=f"Design Point ({WS_star:.0f}, {PW_star:.3f})")

            results["feasible"] = True
            results["WS_star"] = WS_star
            results["PW_star"] = PW_star
        else:
            y_top = 1.1 * np.max(P_W_required)
            x_min = 0.0

        plt.xlabel("Wing Loading W/S [N/m²]")
        plt.ylabel("Power Loading P/W [W/N]")
        plt.grid(True)
        plt.legend(loc="center right", bbox_to_anchor=(1.02, 0.5))
        plt.tight_layout()

        plt.ylim(0, y_top)
        plt.xlim(x_min, 1.05 * max(W_S_stall, W_S_landing, W_S_ceiling))
        plt.show()

    return results


def plot_constraint_diagram_with_mtow_contours(
    constraint_results,
    input_dict,
    mtow_samples,
    contour_levels=8,
    cmap="viridis",
):
    """
    Plot the constraint diagram and overlay constant-MTOW contours from sampled points.
    """
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri

    W_S_stall = constraint_results["W_S_stall"]
    W_S_landing = constraint_results["W_S_landing"]
    W_S_ceiling = constraint_results["W_S_ceiling"]
    W_S_array = constraint_results["W_S_array"]
    T_W_climb = constraint_results["T_W_climb"]
    P_W_climb = constraint_results["P_W_climb"]
    P_W_max_speed = constraint_results.get("P_W_max_speed")

    propulsion_type = input_dict["propulsion_type"]
    WS_limit = min(W_S_stall, W_S_landing, W_S_ceiling)
    mask = W_S_array <= WS_limit

    fig, ax = plt.subplots(figsize=(9, 7))

    if propulsion_type == "jet":
        if T_W_climb is None:
            raise ValueError("T_W_climb is missing from constraint_results.")
        y_curve = T_W_climb
        y_key = "T_W"
        y_label = "Thrust Loading T/W [-]"
        ax.plot(W_S_array, y_curve, linewidth=2, label="Climb")
    else:
        if P_W_climb is None:
            raise ValueError("P_W_climb is missing from constraint_results.")
        ax.plot(W_S_array, P_W_climb, linewidth=2, label="Climb")
        if P_W_max_speed is not None:
            ax.plot(W_S_array, P_W_max_speed, linewidth=2, label="Max speed")
            y_curve = np.maximum(P_W_climb, P_W_max_speed)
        else:
            y_curve = P_W_climb
        y_key = "P_W"
        y_label = "Power Loading P/W [W/N]"

    ax.axvline(W_S_stall, color="k", linewidth=2, linestyle="--", label="Stall")
    ax.axvline(W_S_landing, color="k", linewidth=2, linestyle="-.", label="Landing")
    ax.axvline(W_S_ceiling, color="k", linewidth=2, linestyle=":", label="Ceiling")

    if np.any(mask):
        y_top = 1.1 * np.max(y_curve)
        ax.fill_between(W_S_array[mask], y_curve[mask], y_top, alpha=0.12, label="Feasible region")
    else:
        y_top = 1.1 * np.max(y_curve)

    filtered_samples = []
    for sample in mtow_samples:
        if not sample.get("success", True):
            continue
        ws_value = sample.get("W_S")
        y_value = sample.get(y_key)
        mtow_value = sample.get("MTOW")
        if ws_value is None or y_value is None or mtow_value is None:
            continue
        if not np.isfinite(ws_value) or not np.isfinite(y_value) or not np.isfinite(mtow_value):
            continue
        filtered_samples.append({"W_S": float(ws_value), y_key: float(y_value), "MTOW": float(mtow_value)})

    contour = None
    if filtered_samples:
        x = np.array([sample["W_S"] for sample in filtered_samples], dtype=float)
        y = np.array([sample[y_key] for sample in filtered_samples], dtype=float)
        z = np.array([sample["MTOW"] for sample in filtered_samples], dtype=float)

        if len(filtered_samples) >= 3 and np.unique(x).size >= 2 and np.unique(y).size >= 2:
            triangulation = mtri.Triangulation(x, y)
            contour = ax.tricontour(triangulation, z, levels=contour_levels, colors="black", linewidths=1.0)
            ax.clabel(contour, fmt=lambda value: f"{value:.0f} kg", fontsize=8)

        scatter = ax.scatter(
            x,
            y,
            c=z,
            cmap=cmap,
            s=48,
            edgecolors="white",
            linewidths=0.6,
            zorder=4,
            label="Class 2 samples",
        )
        colorbar = fig.colorbar(scatter, ax=ax)
        colorbar.set_label("Converged MTOW [kg]")

    ax.set_xlabel("Wing Loading W/S")
    ax.set_ylabel(y_label)
    ax.set_xlim(0, 1.05 * max(W_S_stall, W_S_landing, W_S_ceiling))
    ax.set_ylim(0, y_top)
    ax.grid(True)
    ax.legend()
    plt.show()

    return {
        "feasible": bool(np.any(mask)),
        "sample_count": len(filtered_samples),
        "contour_created": contour is not None,
        "samples": filtered_samples,
    }


def generate_mtow_overlay_for_constraint_diagram(
    constraint_analysis_inputs,
    class_2_sizing_inputs,
    aspect_ratio,
    lam,
    c_root,
    ws_target_count=5,
    pw_multipliers=(1.00, 1.05, 1.10, 1.15),
    outer_max_iter=5,
    outer_tol_kg=5.0,
    contour_levels=7,
    cmap="viridis",
):
    """
    Re-run the constraint analysis, sample feasible design points, run the
    Class 2 hybrid sizing loop at each point, and overlay MTOW contours on the
    constraint diagram.
    """
    import copy
    import class_2_airframe_structure

    constraint_results_mtow = constraints_raymer(constraint_analysis_inputs)

    taper_ratio = 1.0 / lam if lam > 1.0 else lam
    base_tail_area = class_2_sizing_inputs["tail"]["S_tail_m2"]
    base_wing_area = class_2_sizing_inputs["wing"]["S_m2"]
    base_t_root_ratio = class_2_sizing_inputs["wing"]["t_root_m"] / c_root
    class2_tol = class_2_sizing_inputs.get("tol", 1.0)
    class2_max_iter = class_2_sizing_inputs.get("max_iter", 100)

    def solve_class2_design_point(ws_target, pw_target, mtom_seed):
        working_mtom = float(mtom_seed)
        last_result = None

        for _ in range(outer_max_iter):
            point_inputs = copy.deepcopy(class_2_sizing_inputs)
            s_wing = working_mtom / ws_target
            b_wing = math.sqrt(aspect_ratio * s_wing)
            c_root_point = (2.0 * s_wing) / (b_wing * (1.0 + taper_ratio))
            c_tip_point = taper_ratio * c_root_point

            point_inputs["mtom_guess"] = working_mtom
            point_inputs["p_w_sel"] = float(pw_target)
            point_inputs["w_p_sel"] = 1.0 / float(pw_target)
            point_inputs["w_s_sel"] = float(ws_target)

            point_inputs["wing"]["W_G_kg"] = working_mtom
            point_inputs["wing"]["S_m2"] = s_wing
            point_inputs["wing"]["b_m"] = b_wing
            point_inputs["wing"]["t_root_m"] = base_t_root_ratio * c_root_point
            point_inputs["landing_gear"]["W_to_kg"] = working_mtom

            tail_scale = s_wing / base_wing_area
            point_inputs["tail"]["S_tail_m2"] = base_tail_area * tail_scale

            result = class_2_airframe_structure.converge_mtom_hybrid_struct(point_inputs)
            result["W_S_input"] = float(ws_target)
            result["P_W_input"] = float(pw_target)
            result["S_wing_m2"] = float(s_wing)
            result["b_wing_m"] = float(b_wing)
            result["c_root_m"] = float(c_root_point)
            result["c_tip_m"] = float(c_tip_point)

            last_result = result
            if abs(float(result["MTOM"]) - working_mtom) <= outer_tol_kg:
                break
            working_mtom = float(result["MTOM"])

        return last_result

    ws_limit = min(
        constraint_results_mtow["W_S_stall"],
        constraint_results_mtow["W_S_landing"],
        constraint_results_mtow["W_S_ceiling"],
    )
    feasible_mask = constraint_results_mtow["W_S_array"] <= ws_limit
    ws_feasible = constraint_results_mtow["W_S_array"][feasible_mask]
    pw_floor = constraint_results_mtow["P_W_climb"][feasible_mask]
    pw_max_speed = constraint_results_mtow.get("P_W_max_speed")
    if pw_max_speed is not None:
        pw_floor = np.maximum(pw_floor, pw_max_speed[feasible_mask])

    ws_targets = np.linspace(float(ws_feasible.min()), float(ws_feasible.max()), ws_target_count)
    pw_floor_targets = np.interp(ws_targets, ws_feasible, pw_floor)

    mtow_samples = []
    for ws_target, pw_min in zip(ws_targets, pw_floor_targets):
        for multiplier in pw_multipliers:
            pw_target = float(pw_min * multiplier)
            try:
                result = solve_class2_design_point(
                    ws_target=ws_target,
                    pw_target=pw_target,
                    mtom_seed=class_2_sizing_inputs["mtom_guess"],
                )
                converged = (
                    np.isfinite(result["MTOM"])
                    and np.isfinite(result.get("error", np.nan))
                    and float(result.get("error", np.inf)) <= class2_tol
                    and int(result.get("iterations", class2_max_iter)) < class2_max_iter
                )
                mtow_samples.append(
                    {
                        "W_S": float(ws_target),
                        "P_W": float(pw_target),
                        "MTOW": float(result["MTOM"]),
                        "iterations": int(result.get("iterations", class2_max_iter)),
                        "error": float(result.get("error", np.nan)),
                        "success": converged,
                    }
                )
            except Exception as exc:
                mtow_samples.append(
                    {
                        "W_S": float(ws_target),
                        "P_W": float(pw_target),
                        "MTOW": np.nan,
                        "iterations": np.nan,
                        "error": np.nan,
                        "success": False,
                        "error_message": str(exc),
                    }
                )

    successful_samples = [sample for sample in mtow_samples if sample["success"]]
    print(f"Successful Class 2 design points: {len(successful_samples)} / {len(mtow_samples)}")
    for sample in successful_samples:
        print(
            f"W/S={sample['W_S']:.1f}, P/W={sample['P_W']:.3f}, "
            f"MTOW={sample['MTOW']:.1f} kg, iterations={sample['iterations']}, "
            f"error={sample['error']:.3f}"
        )

    plot_metadata = plot_constraint_diagram_with_mtow_contours(
        constraint_results_mtow,
        constraint_analysis_inputs,
        mtow_samples,
        contour_levels=contour_levels,
        cmap=cmap,
    )

    return {
        "constraint_results": constraint_results_mtow,
        "samples": mtow_samples,
        "successful_samples": successful_samples,
        "plot": plot_metadata,
    }
