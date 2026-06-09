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

    a_term = rcp + np.sqrt(W_S_lb_ft2)
    b_term = 19.0 * cl32_cd * np.sqrt(sigma)
    c_term = a_term / b_term
    w_p = eta_p / c_term

    p_w_hp_per_lbf = 1.0 / w_p
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
    cgrp = (cgr + cd_climb / cl_climb) / math.sqrt(cl_climb)
    p_w_hp_per_lbf = cgrp * np.sqrt(W_S_lb_ft2) / (18.97 * eta_p * math.sqrt(sigma))
    return p_w_hp_per_lbf * HP_PER_LBF_TO_W_PER_N


def _safe_inverse(values):
    values = np.asarray(values, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(values != 0.0, 1.0 / values, np.nan)


def constraints_raymer(input_dict):
    """
    Propeller-aircraft constraint sizing in W/P form.

    Returns wing-loading limits in N/m^2 and power-loading curves in N/W.
    The climb helpers are evaluated in P/W first, then inverted here so the
    plotting function can work directly in W/P.
    """
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
    CL_max_L= input_dict["CL_max_L"]
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
    rho_loiter_alt = input_dict.get("rho_loiter_alt")
    loiter_speed_factor = input_dict.get("loiter_speed_factor", 0.75)

    if propulsion_type != "prop":
        raise NotImplementedError("SMP_W_P currently supports propeller aircraft only.")

    if aircraft_type in ["General aviation (single engine)", "General aviation (Twin engine)"]:
        S_a = 183
    elif aircraft_type in ["Civil jets", "Twin turboprop"]:
        S_a = 305
    else:
        raise ValueError("Data point not available for this aircraft type")

    lambda_025c = math.radians(quarter_sweep)
    if cl_max_foil is not None:
        CL_max_to = 0.9 * cl_max_foil * math.cos(lambda_025c)

    landing_factor = 1.0
    W_S_cruise_max_range = (0.5 * rho_cruise * v_cruise**2) * math.sqrt(math.pi * AR * C_D0)

    W_S_stall =CL_max_L * 0.5 * rho * v_stall**2 # 0.5 * rho * v_stall**2 * CL_max_to - originally used Cl_max_to
    W_S_landing = ((landing_dist - S_a) * (rho_ratio * landing_factor * CL_max_L) / 5.0) * 9.81
    W_S_ceiling = 0.5 * rho_ceiling * v_cruise**2 * math.sqrt(math.pi * AR * e_os * C_D0)
    W_S_loiter = None
    if rho_loiter_alt is not None:
        W_S_loiter = (
            0.5
            * rho_loiter_alt
            * (loiter_speed_factor * v_cruise) ** 2
            * math.sqrt(3.0 * math.pi * AR * e_os * C_D0)
        )

    K = 1.0 / (math.pi * AR * e_os)
    ws_candidates = [W_S_stall, W_S_landing, W_S_ceiling]
    if W_S_loiter is not None:
        ws_candidates.append(W_S_loiter)
    W_S_max = max(ws_candidates)
    W_S_array = np.arange(1.0, int(1.1 * W_S_max) + 10, 10, dtype=float)

    P_W_climb = None
    W_P_climb = None
    P_W_max_speed = None
    W_P_max_speed = None
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

    cd0_aeo_roc = C_D0
    cd0_aeo_cgr = C_D0
    cl_max_for_aeo_cgr = CL_max_to
    cl_margin_from_stall = 0.2
    cd0_oei_roc = C_D0
    rho_oei = rho_climb
    cl_max_for_oei = CL_max
    oei_rc_factor = 0.027
    total_engines = 2
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

    P_W_climb_aeo = np.maximum(P_W_climb_aeo_roc, P_W_climb_aeo_cgr)
    W_P_climb_aeo = _safe_inverse(P_W_climb_aeo)

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

    if total_engines > 1:
        P_W_climb_oei_5000 = P_W_climb_oei_one_engine_5000 * (total_engines / (total_engines - 1))
    else:
        P_W_climb_oei_5000 = P_W_climb_oei_one_engine_5000.copy()
    W_P_climb_oei_5000 = _safe_inverse(P_W_climb_oei_5000)

    if density_power_ratio <= 0:
        raise ValueError("density ratio rho_climb / density must be > 0")

    P_W_climb_oei = P_W_climb_oei_5000 / density_power_ratio
    W_P_climb_oei = _safe_inverse(P_W_climb_oei)

    P_W_climb = np.maximum(P_W_climb_aeo, P_W_climb_oei)
    W_P_climb = _safe_inverse(P_W_climb)

    if sigma_max_speed is None:
        sigma_max_speed = rho_max_speed / rho if rho else 1.0

    with np.errstate(divide="ignore", invalid="ignore"):
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
        "P_W_max_speed": P_W_max_speed,
        "W_P_max_speed": W_P_max_speed,
    }


def plot_constraint_diagram(
    constraint_results,
    input_dict,
    *,
    include_max_speed_constraint=True,
    include_ceiling_constraint=True,
    include_loiter_constraint=True,
    margin_factor=0.95,
):
    """
    Plot the propeller-aircraft constraint diagram in W/P [N/W] versus W/S [N/m^2].

    Feasible region:
    - W/S must stay to the left of the active vertical constraints.
    - W/P must stay below the active envelope.
    """
    import matplotlib.pyplot as plt

    if input_dict["propulsion_type"] != "prop":
        raise NotImplementedError("SMP_W_P plotting currently supports propeller aircraft only.")

    W_S_stall = constraint_results["W_S_stall"]
    W_S_landing = constraint_results["W_S_landing"]
    W_S_ceiling = constraint_results["W_S_ceiling"]
    W_S_loiter = constraint_results.get("W_S_loiter")
    W_S_array = constraint_results["W_S_array"]

    W_P_climb = constraint_results["W_P_climb"]
    W_P_max_speed = constraint_results.get("W_P_max_speed")
    W_P_climb_aeo_roc = constraint_results.get("W_P_climb_aeo_roc")
    W_P_climb_aeo_cgr = constraint_results.get("W_P_climb_aeo_cgr")
    W_P_climb_aeo = constraint_results.get("W_P_climb_aeo")
    W_P_climb_oei_one_engine_5000 = constraint_results.get("W_P_climb_oei_one_engine_5000")
    W_P_climb_oei_5000 = constraint_results.get("W_P_climb_oei_5000")
    W_P_climb_oei = constraint_results.get("W_P_climb_oei")

    ws_limits = [W_S_stall, W_S_landing]
    if include_ceiling_constraint:
        ws_limits.append(W_S_ceiling)
    if include_loiter_constraint and W_S_loiter is not None:
        ws_limits.append(W_S_loiter)
    WS_limit = min(ws_limits)
    mask = W_S_array <= WS_limit

    results = {
        "feasible": False,
        "WS_star": None,
        "WP_star": None,
    }

    plt.figure(figsize=(8, 6))

    wp_curves = [
        ("AEO ROC", W_P_climb_aeo_roc, {"linestyle": "--", "linewidth": 1.8}),
        ("AEO CGR", W_P_climb_aeo_cgr, {"linestyle": "-.", "linewidth": 1.8}),
        ("AEO Climb Envelope", W_P_climb_aeo, {"linestyle": ":", "linewidth": 2.0}),
        ("OEI 5000 ft (One Engine)", W_P_climb_oei_one_engine_5000, {"linestyle": "--", "linewidth": 1.5}),
        ("OEI 5000 ft (Installed)", W_P_climb_oei_5000, {"linestyle": "-.", "linewidth": 1.8}),
        ("OEI Sea-Level Equivalent", W_P_climb_oei, {"linestyle": ":", "linewidth": 2.0}),
    ]
    if include_max_speed_constraint:
        wp_curves.append(("Max speed", W_P_max_speed, {"linestyle": "-", "linewidth": 2.0}))

    for label, curve, style in wp_curves:
        if curve is not None:
            plt.plot(W_S_array, curve, label=label, **style)

    plt.plot(W_S_array, W_P_climb, linewidth=2.5, color="k", label="Climb Envelope")

    plt.axvline(W_S_stall, color="g", linewidth=3, linestyle="-.", label="Stall")
    plt.axvline(W_S_landing, color="k", linewidth=3, linestyle="--", label="Landing")
    if include_ceiling_constraint:
        plt.axvline(W_S_ceiling, color="k", linewidth=3, linestyle=":", label="Ceiling")
    if include_loiter_constraint and W_S_loiter is not None:
        plt.axvline(W_S_loiter, color="k", linewidth=3, linestyle=(0, (6, 2)), label="Loiter")

    W_P_required = W_P_climb.copy()
    if include_max_speed_constraint and W_P_max_speed is not None:
        W_P_required = np.minimum(W_P_required, W_P_max_speed)

    visible_mask = mask & (W_S_array >= 0.5 * WS_limit)
    plotted_curves = [curve for _, curve, _ in wp_curves if curve is not None]
    plotted_curves.append(W_P_climb)

    if np.any(visible_mask):
        y_top = 1.1 * max(np.nanmax(curve[visible_mask]) for curve in plotted_curves)
        x_min = 0.5 * WS_limit
    elif np.any(mask):
        y_top = 1.1 * max(np.nanmax(curve[mask]) for curve in plotted_curves)
        x_min = 0.0
    else:
        y_top = 1.1 * max(np.nanmax(curve) for curve in plotted_curves)
        x_min = 0.0

    if np.any(mask):
        plt.fill_between(W_S_array[mask], 0.0, W_P_required[mask], alpha=0.15, label="Feasible")

        WS_star = margin_factor * WS_limit
        i = np.argmin(np.abs(W_S_array - WS_star))
        WP_star = W_P_required[i]

        plt.plot(WS_star, WP_star, "ko", markersize=7, label=f"Design Point ({WS_star:.0f}, {WP_star:.3f})")

        results["feasible"] = True
        results["WS_star"] = WS_star
        results["WP_star"] = WP_star

    plt.xlabel("Wing Loading W/S [N/m^2]")
    plt.ylabel("Propulsive Power Loading W/P [N/W]")
    plt.grid(True)
    plt.legend(loc="center right", bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    plt.ylim(0.0, y_top)
    plt.xlim(x_min, 1.05 * max(ws_limits))
    plt.show()

    return results
