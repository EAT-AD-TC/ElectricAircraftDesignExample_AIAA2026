#note - this has not been tested - a very quick implementation

import numpy as np

def solve_powertrain(
    eta_te, eta_gb, eta_p1, eta_em, eta_pm, eta_gen, eta_p2,
    Phi, phi, Pp
):
    A = np.array([
        [-eta_te,   1,      0,      0,      0,      0,      0,      0,      0,   0],
        [0,     -eta_gb,    1,      1,      0,      0,      0,      0,      0,   0],
        [0,         0,      0,  -eta_p1,    0,      0,      0,      0,      1,   0],
        [0,         0,  -eta_em,    0,      1,      0,      0,      0,      0,   0],
        [0,         0,      0,      0,  -eta_pm, -eta_pm,   1,      0,      0,   0],
        [0,         0,      0,      0,      0,      0,  -eta_gen,   1,      0,   0],
        [0,         0,      0,      0,      0,      0,      0,  -eta_p2,    0,   1],
        [Phi,       0,      0,      0,      0,  (Phi-1),     0,      0,      0,   0],
        [0,         0,      0,      0,     phi,     0,       0,      0,  (phi-1), 0],
        [0,         0,      0,      0,      0,      0,      0,      0,      1,   1],
    ], dtype=float)

    b = np.zeros(10)
    b[-1] = Pp

    x = np.linalg.solve(A, b)

    names = ["Pt","Pte","Pgb","Ps1","Pe1","Pbat","Pe2","Ps2","Pp1","Pp2"]
    return dict(zip(names, x))


# How to use this:
if __name__ == "__main__":
    sol = solve_powertrain(
        eta_te=0.98, eta_gb=0.99, eta_p1=0.90, eta_em=0.95, eta_pm=0.97, # provide efficiencies
        eta_gen=0.96, eta_p2=0.90, Phi=0.2, phi=0.3, Pp=100_000
    )
    print(sol)
