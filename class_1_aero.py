### Option 1 : Low fidelity - maximum lift-to-drag-ratio

import math
import numpy as np

def ld_max_lofi(aircraft_type, AR, swet_sref):
   
    KLD_table = {
        "civil_jet": 15.5,
        "military_jet": 14.0,
        "prop_retractable": 11.0,
        "prop_fixed": 9.0,
        "high_aspect_ratio": 13.0,
        "sailplane": 15.0
    }

    if aircraft_type not in KLD_table:
        raise ValueError(
            f"Unknown aircraft type '{aircraft_type}'. "
            f"Choose from: {list(KLD_table.keys())}"
        )

    KLD = KLD_table[aircraft_type]

    return KLD * math.sqrt(AR / swet_sref)

### Option - 2 Low fidelity - two term drag polar 



def drag_polar_lofi(
    aircraft_type,
    CL,
    AR,
    delta_cd0_flaps, #These can be changed or passed in for drag estimation in non-cruise phases
    delta_cd0_lg,
    delta_e_flaps,
    use_mid_range=False
):

    # Table 4 values: (CD0_min, CD0_max, e_min, e_max)
    table = {
        "high_subsonic_jet": (0.014, 0.020, 0.75, 0.85),
        "large_turboprop": (0.018, 0.024, 0.80, 0.85),
        "twin_piston": (0.022, 0.028, 0.75, 0.80),
        "single_piston_retractable": (0.020, 0.030, 0.75, 0.80),
        "single_piston_fixed": (0.025, 0.040, 0.65, 0.75),
        "agricultural_clean": (0.060, 0.060, 0.65, 0.75),
        "agricultural_spray": (0.070, 0.080, 0.65, 0.75)
    }

    if aircraft_type not in table:
        raise ValueError(
            f"Unknown aircraft type '{aircraft_type}'. "
            f"Choose from: {list(table.keys())}"
        )

    cd0_min, cd0_max, e_min, e_max = table[aircraft_type]

    if use_mid_range:
        cd0_clean = 0.5 * (cd0_min + cd0_max)
        e_clean = 0.5 * (e_min + e_max)
    else:
        cd0_clean = cd0_min
        e_clean = e_max

    # Apply configuration increments
    CD0 = cd0_clean + delta_cd0_flaps + delta_cd0_lg 
    e = e_clean + delta_e_flaps # this should not be adding the deltavalue if the delta is a whole oswald efficiency for a specific configuration 

    # Two-term drag polar
    CD = CD0 + CL**2 / (math.pi * AR * e)

    return CD




CLMAX_TABLE = {
    "small_single_engine_props": {"clean": (1.3, 1.9), "TO": (1.3, 1.9), "L": (1.6, 2.3)},
    "small_twin_engine_props":   {"clean": (1.2, 1.8), "TO": (1.4, 2.0), "L": (1.6, 2.5)},
    "regional_turboprops":       {"clean": (1.5, 1.9), "TO": (1.7, 2.1), "L": (1.9, 3.3)},
    "transport_jets":            {"clean": (1.2, 1.8), "TO": (1.6, 2.2), "L": (1.8, 2.8)},
    "military_transports":       {"clean": (1.2, 1.8), "TO": (1.6, 2.2), "L": (1.8, 3.4)},
}

def _pick(rng, level):
    if level == "lo":
        return rng[0]
    if level == "hi":
        return rng[1]
    if level == "mid":
        return 0.5 * (rng[0] + rng[1])
    raise ValueError("range must be 'lo', 'mid', or 'hi'")

def CL_max(
    aircraft_type,
    clmax_airfoil=None,
    sweep_quarter_chord_deg=None,
    fid_range=None,
):
    """
    Behavior:
    ----------
    If clmax_airfoil AND sweep_quarter_chord_deg are provided:
        → return CL_max_clean (single float, Raymer)
    Else:
        → return (CL_max_clean, CL_max_TO, CL_max_landing) from table

    fid_range = 'lo' | 'mid' | 'hi'
    """

    if aircraft_type not in CLMAX_TABLE:
        raise KeyError(f"Unknown aircraft_type '{aircraft_type}'")

    tbl = CLMAX_TABLE[aircraft_type]

    # Case 1: Raymer-based clean CLmax
    if clmax_airfoil is not None and sweep_quarter_chord_deg is not None:
        lam = np.deg2rad(sweep_quarter_chord_deg)
        return 0.9 * clmax_airfoil * np.cos(lam)

    # Case 2: Table-based values
    CL_max_clean    = _pick(tbl["clean"], fid_range)
    CL_max_TO       = _pick(tbl["TO"],    fid_range)
    CL_max_landing  = _pick(tbl["L"],     fid_range)

    return CL_max_clean, CL_max_TO, CL_max_landing

## Lo-fi Aero Propulsive Interactions 

def apply_aero_prop_interactions(
    CL_cruise, CD_cruise, eta_p_cruise,
    arrangement,
    level="mid",
    CL_takeoff=None, CD_takeoff=None, eta_p_takeoff=None,
):
    """
    Additive updates:
      CL_new   = CL + ΔCL
      CD_new   = CD + ΔCD
      eta_p_new= eta_p + Δη_p

    If takeoff vars are provided (all three not None) -> update both cruise & takeoff and return both.
    Else -> update cruise only and return cruise only.
    """

    def pick(r):
        if level == "min": return r[0]
        if level == "max": return r[1]
        return 0.5 * (r[0] + r[1])  # mid

    # --- cruise update ---
    c = AERO_PROP_TABLE[arrangement]["cruise"]
    dCL_c  = pick(c["dCL"])
    dCD_c  = pick(c["dCD"])
    deta_c = pick(c["deta_p"])

    CL_cruise_new   = CL_cruise + dCL_c
    CD_cruise_new   = CD_cruise + dCD_c
    eta_p_cruise_new = eta_p_cruise + deta_c

    # --- takeoff update (only if available) ---
    takeoff_available = (CL_takeoff is not None) and (CD_takeoff is not None) and (eta_p_takeoff is not None)
    if not takeoff_available:
        return CL_cruise_new, CD_cruise_new, eta_p_cruise_new

    t = AERO_PROP_TABLE[arrangement]["takeoff"]
    dCL_t  = pick(t["dCL"])
    dCD_t  = pick(t["dCD"])
    deta_t = pick(t["deta_p"])

    CL_takeoff_new   = CL_takeoff + dCL_t
    CD_takeoff_new   = CD_takeoff + dCD_t
    eta_p_takeoff_new = eta_p_takeoff + deta_t

    return (CL_cruise_new, CD_cruise_new, eta_p_cruise_new,
            CL_takeoff_new, CD_takeoff_new, eta_p_takeoff_new)