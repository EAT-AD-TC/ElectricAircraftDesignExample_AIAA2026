import pandas as pd
import matplotlib.pyplot as plt

ALLOWED = ["warmup","taxi","takeoff","climb","cruise","loiter","descend","land"]

def validate_mission(mission_list):
    req = {"cruise": ["range","cruise_speed","cruise_alt"]}
    for i, e in enumerate(mission_list):
        p = str(e.get("phase","")).strip().lower()
        if p not in ALLOWED:
            raise ValueError(f"Item {i}: invalid phase '{e.get('phase')}'")
        e["phase"] = p
        for k in req.get(p, []):
            if e.get(k, None) is None:
                raise ValueError(f"Item {i} ('{p}'): missing '{k}'")
    return mission_list


def plot_mission_altitude(mission_list):
    phases = [m["phase"] for m in mission_list]
    x = list(range(len(phases)))

    alt = []
    current_alt = 0.0
    for m in mission_list:
        for k in ("cruise_alt", "loiter_alt", "target_altitude"):
            if m.get(k) is not None:
                current_alt = float(m[k])
        alt.append(current_alt)

    plt.figure(figsize=(10,3))
    plt.step(x, alt, where="post")
    plt.ylabel("Altitude [m]")
    plt.xticks(x, [p.capitalize() for p in phases], rotation=30)
    plt.grid(True, axis="y", alpha=0.3)
    plt.show()


def plot_mission_speed(mission_list):
    phases = [m["phase"] for m in mission_list]
    x = list(range(len(phases)))

    speed = []
    current_speed = None
    for m in mission_list:
        for k in ("max_speed", "cruise_speed", "loiter_speed", "climb_speed"):
            if m.get(k) is not None:
                current_speed = float(m[k])
        speed.append(current_speed)

    plt.figure(figsize=(10,3))
    plt.step(x, speed, where="post")
    plt.ylabel("Speed [Mach]")
    plt.xticks(x, [p.capitalize() for p in phases], rotation=30)
    plt.grid(True, axis="y", alpha=0.3)
    plt.show()
