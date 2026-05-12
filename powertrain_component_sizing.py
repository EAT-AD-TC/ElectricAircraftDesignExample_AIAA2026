import math 

"""
The following methods compute the propulsive power loading for each propulsion architecture listed in Table 8.

"""




def WP_therm_eng_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen):
    """
    Series hybrid: thermal engine power loading
    """
    term = ((Phi / (1.0 - Phi)) * (eta_em / eta_te)) + eta_gen
    return W_over_Pp / (eta_p * eta_gb * term)


def WP_em_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen):
    """
    Series hybrid: electric motor power loading
    """
    term = 1.0 + ((1.0 - Phi) / Phi) * (eta_te * eta_gen / eta_em)
    return W_over_Pp / (eta_p * eta_gb * term)


def WP_batt_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen):
    """
    Series hybrid: battery power loading
    """
    term = eta_em + ((1.0 - Phi) / Phi) * eta_te * eta_gen
    return W_over_Pp / (eta_p * eta_gb * term)


def WP_therm_eng_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em):
    """
    Parallel hybrid: thermal engine power loading
    """
    term = (Phi / (1.0 - Phi)) * (eta_em / eta_te) + 1.0
    return W_over_Pp / (eta_p * eta_gb * term)

def WP_therm_eng_parallel_alt(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em):
    """
    Parallel hybrid: thermal engine power loading
    """
    if Phi == 1: 
        term=1
    else:
        term = (Phi / (1.0 - Phi)) * (eta_em / eta_te) + 1.0
    return W_over_Pp / (eta_p * eta_gb * term)


def WP_em_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em):
    """
    Parallel hybrid: electric motor power loading
    """
    
    
    term = 1.0 + ((1.0 - Phi) / Phi) * (eta_te / eta_em)
    return W_over_Pp / (eta_p * eta_gb * term)


def WP_batt_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em):
    """
    Parallel hybrid: battery power loading
    """
    term = eta_em + ((1.0 - Phi) / Phi) * eta_te
    return W_over_Pp / (eta_p * eta_gb * term)


def power_loading_components(
    W_over_Pp,
    Phi,
    eta_p,
    eta_gb,
    eta_te,
    eta_em,
    powertrain_type,
    eta_gen=None,
):
    """
    Compute component power loadings W/P for the selected hybrid architecture.

    Parameters
    ----------
    W_over_Pp : float
        Aircraft propulsive power loading, W/P_p
    Phi : float
        Supplied power ratio / hybridization ratio
    eta_p : float
        Propulsor efficiency
    eta_gb : float
        Gearbox efficiency
    eta_te : float
        Thermal engine efficiency
    eta_em : float
        Electric motor efficiency
    powertrain_type : str
        'series' or 'parallel'
    eta_gen : float or None
        Generator efficiency. Required for series architecture.

    Returns
    -------
    dict
        Dictionary containing component W/P values.
    """

    if W_over_Pp <= 0:
        raise ValueError("W_over_Pp must be > 0")
    if not (0.0 < Phi < 1.0):
        raise ValueError("Phi must be between 0 and 1 (exclusive)")
    if eta_p <= 0 or eta_gb <= 0 or eta_te <= 0 or eta_em <= 0:
        raise ValueError("All efficiencies must be > 0")

    pt = powertrain_type.strip().lower()

    if pt == "series":
        if eta_gen is None:
            raise ValueError("eta_gen is required for series powertrain")
        if eta_gen <= 0:
            raise ValueError("eta_gen must be > 0")

        W_over_Pte = WP_therm_eng_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen)
        W_over_Pem = WP_em_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen)
        W_over_Pb = WP_batt_series(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em, eta_gen)

        return {
            "powertrain_type": "series",
            "W_over_Pp": W_over_Pp,
            "W_over_Pte": W_over_Pte,
            "W_over_Pem": W_over_Pem,
            "W_over_Pb": W_over_Pb,
        }

    elif pt == "parallel":
        W_over_Pte = WP_therm_eng_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em)
        W_over_Pem = WP_em_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em)
        W_over_Pb = WP_batt_parallel(W_over_Pp, Phi, eta_p, eta_gb, eta_te, eta_em)

        return {
            "powertrain_type": "parallel",
            "W_over_Pp": W_over_Pp,
            "W_over_Pte": W_over_Pte,
            "W_over_Pem": W_over_Pem,
            "W_over_Pb": W_over_Pb,
        }

    else:
        raise ValueError("powertrain_type must be 'series' or 'parallel'")
