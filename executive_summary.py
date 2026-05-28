import copy
import math
import shutil
import subprocess
from pathlib import Path

import pandas as pd

import class_1_sizing
import class_2_airframe_structure as c2s
import special_functions as sf


def build_e19_appendix_summary(
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

    def _propulsion_breakdown(out):
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
    systems = sf.installed_system_weights_from_class2_inputs(class_2_sizing_inputs)
    propulsion = _propulsion_breakdown(class_2_out)
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

    derived = {
        "airframe": airframe,
        "systems": systems,
        "propulsion": propulsion,
        "class_1_out": class_1_out,
        "class_2_out": class_2_out,
        "tail_out": tail_out,
        "class2_structure_plus_systems_kg": class2_structure_plus_systems,
        "class2_fuel_mass_in_loop_kg": class2_fuel_mass_in_loop,
        "selected_wing_loading_n_per_m2": selected_wing_loading_n_per_m2,
        "selected_power_loading_w_per_n": selected_power_loading_w_per_n,
    }
    paper_comparison = build_e19_paper_comparison_table(
        class_2_sizing_inputs,
        class_2_out,
        derived=derived,
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
        "Step 10: E19 Paper Comparison": paper_comparison,
    }

    table_order = list(tables.keys())

    return {
        "executive_summary_md": executive_summary_md,
        "tables": tables,
        "table_order": table_order,
        "derived": derived,
    }


def _phase_lookup(mission, phase_name):
    return next(
        (ph for ph in mission if str(ph.get("phase", "")).lower() == str(phase_name).lower()),
        {},
    )


def _percent_difference(current_value, reference_value):
    if reference_value in (None, 0):
        return None
    if current_value is None:
        return None
    try:
        return 100.0 * (float(current_value) - float(reference_value)) / float(reference_value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def build_e19_paper_comparison_table(
    class_2_sizing_inputs,
    class_2_out,
    *,
    derived,
):
    """
    Build a comparison table between the current worked-example results and
    the E19 reference aircraft from the eCommuter study.

    Parameters
    ----------
    class_2_sizing_inputs : dict
        Active Class II sizing inputs used for the worked example.
    class_2_out : dict
        Converged Class II output dict.
    derived : dict
        Typically appendix_summary["derived"] from build_e19_appendix_summary().
    """
    if derived is None:
        raise ValueError("derived must be provided, typically appendix_summary['derived']")

    mission = class_2_sizing_inputs["mission"]
    constraint_inputs = class_2_sizing_inputs["constraint_analysis_inputs"]
    climb_phase = _phase_lookup(mission, "climb")
    cruise_phase = _phase_lookup(mission, "cruise")
    ifr_phase = _phase_lookup(mission, "ifr")
    takeoff_phase = _phase_lookup(mission, "takeoff")

    airframe = derived["airframe"]
    systems = derived["systems"]
    propulsion = derived["propulsion"]
    fuel_mass = float(derived["class2_fuel_mass_in_loop_kg"])

    system_breakdown = systems["weight_breakdown_kg"]
    furnishings_mass = float(system_breakdown.get("furnishings_weight_kg", 0.0) or 0.0) + float(
        system_breakdown.get("galley_entertainment_furnishing_weight_mohan_kg", 0.0) or 0.0
    )
    base_systems_mass = float(system_breakdown.get("base_systems_weight_kg", 0.0) or 0.0)

    prop_rows = propulsion["table"].to_dict("records")
    prop_map = {row["Component"]: float(row["Mass [kg]"]) for row in prop_rows}

    thermal_propulsion_mass = (
        prop_map.get("Turboprops (installed)", 0.0)
        + prop_map.get("Propellers", 0.0)
        + prop_map.get("Fuel system", 0.0)
    )
    electric_power_train_budget = (
        float(class_2_out["M_batt"])
        + prop_map.get("Electric motors", 0.0)
        + prop_map.get("Motor controllers", 0.0)
    )

    mtom = float(class_2_out["MTOM"])
    payload = float(class_2_sizing_inputs["payload"])
    mzfm = mtom - fuel_mass
    oem = mtom - payload - fuel_mass

    wing_geometry = airframe["geometry"]
    lam = float(class_2_sizing_inputs["wing"]["lam"])
    c_root = float(wing_geometry["c_root_m"])
    wing_mac = (2.0 / 3.0) * c_root * ((1.0 + lam + lam**2) / (1.0 + lam))

    current_psfc = float(
        class_2_sizing_inputs.get(
            "psfc_gt_cruise_kg_per_kwh",
            class_2_sizing_inputs.get("psfc_kg_per_kwh", 0.34),
        )
    )

    electric_range_km = float(cruise_phase.get("range", 0.0) or 0.0) / 1000.0
    hybrid_range_proxy_km = electric_range_km + float(ifr_phase.get("range", 0.0) or 0.0) / 1000.0
    cruise_altitude_m = float(
        cruise_phase.get("cruise_alt", climb_phase.get("target_altitude", 0.0)) or 0.0
    )

    rows = []

    def add_row(category, parameter, unit, current_value, reference_value, reference_note):
        rows.append(
            {
                "Category": category,
                "Parameter": parameter,
                "Unit": unit,
                "This model": None if current_value is None else round(float(current_value), 3),
                "E19 paper": None if reference_value is None else round(float(reference_value), 3),
                "Diff [%]": None
                if _percent_difference(current_value, reference_value) is None
                else round(_percent_difference(current_value, reference_value), 2),
                "Reference / Notes": reference_note,
            }
        )

    add_row("Mission / TLAR", "Payload", "kg", payload, 1805.0, "Chart 8 / Chart 9")
    add_row("Mission / TLAR", "Cruise altitude", "m", cruise_altitude_m, 3048.0, "Chart 8: 10000 ft")
    add_row("Mission / TLAR", "Ceiling altitude", "m", float(climb_phase.get("ceiling_alt", 0.0) or 0.0), 7620.0, "Chart 8: 25000 ft")
    add_row("Mission / TLAR", "Diversion mission", "km", float(ifr_phase.get("range", 0.0) or 0.0) / 1000.0, 185.2, "Chart 8: 100 nm")
    add_row("Mission / TLAR", "Takeoff field length", "m", float(takeoff_phase.get("tofl", 0.0) or 0.0), 1440.0, "Chart 8")
    add_row("Mission / TLAR", "Electric mission range", "km", electric_range_km, 190.0, "Chart 12")

    add_row("Mass / Power", "MTOM", "kg", mtom, 8618.0, "Chart 9 / Chart 13")
    add_row("Mass / Power", "Design fuel (IFR reserves only)", "kg", fuel_mass, 192.0, "Chart 9")
    add_row("Mass / Power", "Maximum zero-fuel mass", "kg", mzfm, 8426.0, "Chart 9")
    add_row("Mass / Power", "Operating empty mass", "kg", oem, 6621.0, "Chart 9")
    add_row("Mass / Power", "Furnishings", "kg", furnishings_mass, 270.0, "Chart 9")
    add_row("Mass / Power", "Systems (excluding furnishings)", "kg", base_systems_mass, 650.0, "Chart 9")
    add_row("Mass / Power", "Propellers + range extender", "kg", thermal_propulsion_mass, 388.0, "Chart 9")
    add_row("Mass / Power", "Airframe structure", "kg", float(airframe["total_mass_kg"]), 2446.0, "Chart 9")
    add_row("Mass / Power", "Electric power-train budget", "kg", electric_power_train_budget, 2329.0, "Chart 9; current model excludes cooling/power distribution")
    add_row("Mass / Power", "Electric motors", "kg", prop_map.get("Electric motors", 0.0), 253.0, "Chart 9")
    add_row("Mass / Power", "Installed EM power", "kW", float(class_2_out["p_rated_em"]) / 1000.0, 1251.0, "Chart 9")
    add_row("Mass / Power", "Motor controllers", "kg", prop_map.get("Motor controllers", 0.0), 12.0, "Chart 9")
    add_row("Mass / Power", "Battery mass", "kg", float(class_2_out["M_batt"]), 2018.0, "Chart 9")

    add_row("Geometry / Aero", "Wing area", "m^2", float(wing_geometry["wing_area_m2"]), 33.2, "Chart 10")
    add_row("Geometry / Aero", "Wing span", "m", float(wing_geometry["wing_span_m"]), 20.0, "Chart 13")
    add_row("Geometry / Aero", "Wing aspect ratio", "-", float(class_2_sizing_inputs["wing"]["A"]), 12.0, "Chart 10")
    add_row("Geometry / Aero", "Wing MAC", "m", wing_mac, 1.77, "Chart 10")
    add_row("Geometry / Aero", "Horizontal tail area", "m^2", float(wing_geometry["tail_area_horizontal_m2"]), 8.2, "Chart 10")
    add_row("Geometry / Aero", "Vertical tail area", "m^2", float(wing_geometry["tail_area_vertical_m2"]), 6.1, "Chart 10")
    add_row("Geometry / Aero", "Cruise L/D", "-", float(cruise_phase.get("l_d", 0.0) or 0.0), 19.4, "Chart 13")
    add_row("Geometry / Aero", "Gas-turbine PSFC", "kg/kWh", current_psfc, 0.35, "Chart 13; defaults to 0.34 if not stored")

    return pd.DataFrame(rows)


def _latex_escape(value):
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _latex_cell(value):
    if value is None or (isinstance(value, float) and not math.isfinite(value)):
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        text = f"{value:.3f}".rstrip("0").rstrip(".")
    else:
        text = str(value)
    text = text.replace("Â²", "2").replace("²", "2").replace("^2", "2")
    return _latex_escape(text)


def _dataframe_to_longtable_latex(
    df,
    caption,
    label,
    *,
    column_format=None,
    font_size=None,
):
    column_count = len(df.columns)
    column_format = column_format or ("l" * column_count)
    header = " & ".join(_latex_cell(col) for col in df.columns) + r" \\"
    body = "\n".join(
        " & ".join(_latex_cell(value) for value in row) + r" \\"
        for row in df.itertuples(index=False, name=None)
    )
    table = (
        f"\\begin{{longtable}}{{{column_format}}}\n"
        f"\\caption{{{_latex_escape(caption)}}}\\label{{{label}}}\\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endfirsthead\n"
        f"\\multicolumn{{{column_count}}}{{l}}{{\\tablename\\ \\thetable{{}} -- continued from previous page}}\\\\\n"
        "\\toprule\n"
        f"{header}\n"
        "\\midrule\n"
        "\\endhead\n"
        "\\midrule\n"
        f"\\multicolumn{{{column_count}}}{{r}}{{Continued on next page}}\\\\\n"
        "\\endfoot\n"
        "\\bottomrule\n"
        "\\endlastfoot\n"
        f"{body}\n"
        "\\end{longtable}\n"
    )
    if font_size:
        return f"{{{font_size}\n{table}}}\n"
    return table


def _table_latex_options(table_name, df):
    columns = list(df.columns)

    if columns == ["Parameter", "Value", "Units", "Notes"]:
        return {
            "column_format": "@{}p{3.0cm}p{1.8cm}p{1.3cm}p{8.0cm}@{}",
            "font_size": "\\footnotesize",
        }

    if columns == [
        "Phase",
        "Mode",
        "Range [km]",
        "L/D",
        "Phi",
        "Battery energy [MJ]",
        "Fuel energy [MJ]",
        "Total energy [MJ]",
        "Fuel mass [kg]",
    ]:
        return {
            "column_format": (
                "@{}p{1.5cm}p{1.8cm}p{1.3cm}p{0.9cm}p{0.8cm}"
                "p{1.8cm}p{1.8cm}p{1.8cm}p{1.4cm}@{}"
            ),
            "font_size": "\\scriptsize",
        }

    if columns == ["Group", "Component", "Mass [kg]", "Included in MTOM loop"]:
        return {
            "column_format": "@{}p{2.1cm}p{7.0cm}p{1.9cm}p{3.5cm}@{}",
            "font_size": "\\footnotesize",
        }

    if columns == [
        "Category",
        "Parameter",
        "Unit",
        "This model",
        "E19 paper",
        "Diff [%]",
        "Reference / Notes",
    ]:
        return {
            "column_format": "@{}p{2.4cm}p{3.1cm}p{1.1cm}p{1.8cm}p{1.8cm}p{1.6cm}p{8.0cm}@{}",
            "font_size": "\\footnotesize",
        }

    return {"column_format": None, "font_size": "\\footnotesize"}


def _find_latex_engine():
    for candidate in ("pdflatex", "xelatex", "tectonic"):
        found = shutil.which(candidate)
        if found:
            return candidate, found
    return None, None


def _render_e19_worked_example_latex(appendix_summary):
    derived = appendix_summary["derived"]
    class_2_out = derived["class_2_out"]
    airframe = derived["airframe"]
    systems = derived["systems"]
    propulsion = derived["propulsion"]
    fuel_mass = float(derived["class2_fuel_mass_in_loop_kg"])

    intro = (
        "\\section{EADG Worked Example}\n"
        "This section is generated directly from the current worked-example summary data. "
        f"The present Class II solution converges to an MTOM of {class_2_out['MTOM']:.1f} kg with "
        f"{class_2_out['M_batt']:.1f} kg of batteries, {fuel_mass:.1f} kg of fuel, "
        f"{airframe['total_mass_kg']:.1f} kg of airframe structure, "
        f"{systems['total_weight_kg']:.1f} kg of systems, and "
        f"{propulsion['included_total_kg']:.1f} kg of propulsion mass in the current MTOM loop.\n\n"
        f"The converged wing area is {airframe['geometry']['wing_area_m2']:.2f} m2 and the span is "
        f"{airframe['geometry']['wing_span_m']:.2f} m. The installed electric and thermal powers are "
        f"{class_2_out['p_rated_em']/1000.0:.1f} kW and {class_2_out['p_rated_te']/1000.0:.1f} kW, respectively.\n"
    )

    latex_parts = [
        "\\documentclass[11pt]{article}",
        "\\usepackage[a4paper,margin=1in]{geometry}",
        "\\usepackage{booktabs}",
        "\\usepackage{longtable}",
        "\\usepackage{pdflscape}",
        "\\usepackage[T1]{fontenc}",
        "\\usepackage[utf8]{inputenc}",
        "\\usepackage{hyperref}",
        "\\setlength{\\LTleft}{0pt}",
        "\\setlength{\\LTright}{0pt}",
        "\\setlength{\\tabcolsep}{3pt}",
        "\\renewcommand{\\arraystretch}{1.08}",
        "\\begin{document}",
        intro,
        "\\subsection{Executive Summary Tables}",
    ]

    comparison_name = "Step 10: E19 Paper Comparison"
    for table_name in appendix_summary["table_order"]:
        if table_name == comparison_name:
            continue
        table_options = _table_latex_options(
            table_name, appendix_summary["tables"][table_name]
        )
        latex_parts.append(f"\\subsubsection{{{_latex_escape(table_name)}}}")
        latex_parts.append(
            _dataframe_to_longtable_latex(
                appendix_summary["tables"][table_name],
                caption=table_name,
                label="tab:" + table_name.lower().replace(" ", "-").replace(":", ""),
                column_format=table_options["column_format"],
                font_size=table_options["font_size"],
            )
        )

    if comparison_name in appendix_summary["tables"]:
        comparison_options = _table_latex_options(
            comparison_name, appendix_summary["tables"][comparison_name]
        )
        latex_parts.append("\\subsection{Comparison with the E19 Reference Aircraft}")
        latex_parts.append("\\begin{landscape}")
        latex_parts.append(
            _dataframe_to_longtable_latex(
                appendix_summary["tables"][comparison_name],
                caption="Comparison with the E19 reference aircraft from the eCommuter study",
                label="tab:e19_paper_comparison",
                column_format=comparison_options["column_format"],
                font_size=comparison_options["font_size"],
            )
        )
        latex_parts.append("\\end{landscape}")

    latex_parts.append("\\end{document}")
    return "\n".join(latex_parts)


def export_e19_worked_example_latex_report(
    appendix_summary,
    *,
    output_dir=None,
    base_name="E19_worked_example_report",
    compile_pdf=True,
):
    """
    Create a LaTeX report and, when a local LaTeX engine is available, compile a PDF.

    Parameters
    ----------
    appendix_summary : dict
        Output of build_e19_appendix_summary().
    output_dir : str or Path, optional
        Directory where the .tex and .pdf files should be written.
    base_name : str, optional
        Base filename without extension.
    compile_pdf : bool, optional
        If True, attempt PDF compilation with pdflatex/xelatex/tectonic.
    """
    output_dir = Path(output_dir or (Path.cwd() / "generated_reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_source = _render_e19_worked_example_latex(appendix_summary)
    tex_path = output_dir / f"{base_name}.tex"
    pdf_path = output_dir / f"{base_name}.pdf"
    tex_path.write_text(tex_source, encoding="utf-8")

    engine_name, engine_path = _find_latex_engine()
    compile_result = {
        "status": "not_requested" if not compile_pdf else "not_run",
        "engine": engine_name,
        "engine_path": engine_path,
    }

    if compile_pdf:
        if engine_name is None:
            compile_result = {
                "status": "skipped_no_latex_engine",
                "engine": None,
                "engine_path": None,
                "message": "No pdflatex, xelatex, or tectonic executable was found.",
            }
        else:
            if engine_name == "tectonic":
                command = [engine_path, "--keep-logs", "--outdir", str(output_dir), str(tex_path)]
                cwd = output_dir
            else:
                command = [engine_path, "-interaction=nonstopmode", "-halt-on-error", tex_path.name]
                cwd = output_dir

            completed = subprocess.run(
                command,
                cwd=str(cwd),
                capture_output=True,
                text=True,
            )
            compile_result = {
                "status": "success" if completed.returncode == 0 and pdf_path.exists() else "failed",
                "engine": engine_name,
                "engine_path": engine_path,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }

    return {
        "tex_path": tex_path,
        "pdf_path": pdf_path if pdf_path.exists() else None,
        "latex_source": tex_source,
        "compile_result": compile_result,
    }


def export_e19_worked_example_latex_report_from_inputs(
    *,
    inputs_class_1,
    class_2_sizing_inputs,
    class_2_out,
    class_1_out=None,
    tail_out=None,
    output_dir=None,
    base_name="E19_worked_example_report",
    compile_pdf=True,
):
    """
    Build the appendix summary from the current worked-example inputs/outputs and export the
    LaTeX report in one call. This avoids exporting a stale ``appendix_summary`` snapshot in
    notebook workflows.
    """
    appendix_summary = build_e19_appendix_summary(
        inputs_class_1=inputs_class_1,
        class_2_sizing_inputs=class_2_sizing_inputs,
        class_2_out=class_2_out,
        class_1_out=class_1_out,
        tail_out=tail_out,
    )
    report_out = export_e19_worked_example_latex_report(
        appendix_summary,
        output_dir=output_dir,
        base_name=base_name,
        compile_pdf=compile_pdf,
    )
    report_out["appendix_summary"] = appendix_summary
    return report_out
