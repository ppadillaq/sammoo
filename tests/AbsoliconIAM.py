#!/usr/bin/env python3
"""
Quintic IAM polynomial fit for Absolicon T160 from datasheet points.
- Fits K(theta) with theta in RADIANS (SAM convention).
- Saves figure (PDF) and coefficients (CSV/JSON).
"""
import os, json
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# --- Datasheet points ---
theta_deg = np.array([0,10,20,30,40,50,60,70,80,90], dtype=float)
Kb = np.array([1.00,0.99,0.99,0.98,0.96,0.91,0.77,0.53,0.18,0.00], dtype=float)

# Convert to radians (SAM's polynomial uses radians)
theta_rad = np.deg2rad(theta_deg)

# --- Fit polynomial K(theta) = c0 + c1*theta + ... + c5*theta^5 ---
deg = 5
coef_desc = np.polyfit(theta_rad, Kb, deg)   # descending order
coef_asc  = coef_desc[::-1]                  # ascending: [c0..c5]

# Predictions on the original points & RMSE
Kb_pred = np.polyval(coef_desc, theta_rad)
rmse = float(np.sqrt(np.mean((Kb - Kb_pred)**2)))

# Dense curve for plotting
theta_plot_deg = np.linspace(0, 90, 361)
theta_plot_rad = np.deg2rad(theta_plot_deg)
Kb_fit = np.polyval(coef_desc, theta_plot_rad)

# --- Outputs ---
out_dir = os.path.dirname(os.path.abspath(__file__))
fig_dir = os.path.join(out_dir, "figs")
os.makedirs(fig_dir, exist_ok=True)

# Figure
plt.figure(figsize=(7,5))
plt.scatter(theta_deg, Kb, label="Datasheet points")
plt.plot(theta_plot_deg, Kb_fit, label=f"Quintic fit (RMSE = {rmse:.3f})")
plt.xlabel("Incidence angle θ (degrees)")
plt.ylabel("IAM K(θ)")
plt.title("Absolicon T160 IAM: datasheet vs. quintic polynomial fit")
plt.legend()
plt.grid(True)
fig_path_pdf = os.path.join(fig_dir, "IAM_fit_T160.pdf")
plt.savefig(fig_path_pdf, bbox_inches="tight")
plt.close()

# Coefficients
coef_table = pd.DataFrame({"order": list(range(len(coef_asc))), "coefficient": coef_asc})
coef_csv_path  = os.path.join(out_dir, "IAM_coefficients_T160_order5.csv")
coef_json_path = os.path.join(out_dir, "IAM_coefficients_T160_order5.json")
coef_table.to_csv(coef_csv_path, index=False)
with open(coef_json_path, "w") as f:
    json.dump({
        "polynomial_order": int(deg),
        "theta_units": "radians",
        "coefficients_c0_to_c5": coef_asc.tolist(),
        "rmse": rmse
    }, f, indent=2)

# Console summary
print("IAM coefficients (c0..c5) [theta in radians]:")
print([float(x) for x in coef_asc])
print(f"RMSE: {rmse:.6f}")
print("Saved:")
print(" - Figure:", fig_path_pdf)
print(" - CSV:   ", coef_csv_path)
print(" - JSON:  ", coef_json_path)
