import numpy as np


def plot_constraint_diagram_with_fixed_design_point(
    constraint_results,
    input_dict,
    *,
    design_ws,
    design_wp,
    design_point_label="E-19 Design Point",
    include_max_speed_constraint=True,
    include_ceiling_constraint=True,
    include_loiter_constraint=True,
    margin_factor=0.95,
):
    """
    Plot the existing W/P constraint diagram with a fixed external design point.

    This wrapper is intentionally separate from SMP_W_P.plot_constraint_diagram so
    the original notebook and plotting function remain untouched.
    """
    import matplotlib.pyplot as plt

    if input_dict["propulsion_type"] != "prop":
        raise NotImplementedError(
            "SMP_W_P plotting currently supports propeller aircraft only."
        )

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
    W_P_climb_oei_one_engine_5000 = constraint_results.get(
        "W_P_climb_oei_one_engine_5000"
    )
    W_P_climb_oei_5000 = constraint_results.get("W_P_climb_oei_5000")
    W_P_climb_oei = constraint_results.get("W_P_climb_oei")

    ws_limits = [W_S_stall, W_S_landing]
    if include_ceiling_constraint:
        ws_limits.append(W_S_ceiling)
    if include_loiter_constraint and W_S_loiter is not None:
        ws_limits.append(W_S_loiter)
    WS_limit = min(ws_limits)
    mask = W_S_array <= WS_limit

    wp_curves = [
        ("AEO ROC", W_P_climb_aeo_roc, {"linestyle": "--", "linewidth": 1.8}),
        ("AEO CGR", W_P_climb_aeo_cgr, {"linestyle": "-.", "linewidth": 1.8}),
        ("AEO Climb Envelope", W_P_climb_aeo, {"linestyle": ":", "linewidth": 2.0}),
        (
            "OEI 5000 ft (One Engine)",
            W_P_climb_oei_one_engine_5000,
            {"linestyle": "--", "linewidth": 1.5},
        ),
        (
            "OEI 5000 ft (Installed)",
            W_P_climb_oei_5000,
            {"linestyle": "-.", "linewidth": 1.8},
        ),
        ("OEI Sea-Level Equivalent", W_P_climb_oei, {"linestyle": ":", "linewidth": 2.0}),
    ]
    if include_max_speed_constraint:
        wp_curves.append(("Max speed", W_P_max_speed, {"linestyle": "-", "linewidth": 2.0}))

    plt.figure(figsize=(8, 6))

    for label, curve, style in wp_curves:
        if curve is not None:
            plt.plot(W_S_array, curve, label=label, **style)

    plt.plot(W_S_array, W_P_climb, linewidth=2.5, color="k", label="Climb Envelope")

    plt.axvline(W_S_stall, color="g", linewidth=3, linestyle="-.", label="Stall")
    plt.axvline(W_S_landing, color="k", linewidth=3, linestyle="--", label="Landing")
    if include_ceiling_constraint:
        plt.axvline(W_S_ceiling, color="k", linewidth=3, linestyle=":", label="Ceiling")
    if include_loiter_constraint and W_S_loiter is not None:
        plt.axvline(
            W_S_loiter,
            color="k",
            linewidth=3,
            linestyle=(0, (6, 2)),
            label="Loiter",
        )

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

    auto_ws_star = None
    auto_wp_star = None
    if np.any(mask):
        auto_ws_star = margin_factor * WS_limit
        i = np.argmin(np.abs(W_S_array - auto_ws_star))
        auto_wp_star = W_P_required[i]

    design_wp_limit = np.nan
    design_point_within_ws_limits = bool(design_ws <= WS_limit)
    if design_ws >= np.min(W_S_array) and design_ws <= np.max(W_S_array):
        design_wp_limit = float(np.interp(design_ws, W_S_array, W_P_required))
    design_point_within_power_limits = bool(
        np.isfinite(design_wp_limit) and design_wp <= design_wp_limit
    )

    plt.plot(
        design_ws,
        design_wp,
        marker="o",
        color="k",
        markersize=7,
        linestyle="None",
        label=f"{design_point_label} ({design_ws:.0f}, {design_wp:.4f})",
    )

    plt.xlabel("Wing Loading W/S [N/m^2]")
    plt.ylabel("Power Loading W/P [N/W]")
    plt.grid(True)
    plt.legend(loc="center right", bbox_to_anchor=(1.02, 0.5))
    plt.tight_layout()
    plt.ylim(0.0, y_top)
    plt.xlim(x_min, 1.05 * max(ws_limits))
    plt.show()

    return {
        "feasible_region_exists": bool(np.any(mask)),
        "envelope_WS_star": auto_ws_star,
        "envelope_WP_star": auto_wp_star,
        "design_WS": float(design_ws),
        "design_WP": float(design_wp),
        "design_WP_limit": design_wp_limit,
        "design_point_within_ws_limits": design_point_within_ws_limits,
        "design_point_within_power_limits": design_point_within_power_limits,
        "design_point_feasible": design_point_within_ws_limits and design_point_within_power_limits,
    }
