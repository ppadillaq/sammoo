"""
single_objective_comparison.py

Performs three independent single-objective thermo-economic optimizations
using different cost functions for a CSP system design problem.

Each optimization uses a different objective function:
    - Minimize LCOE (Levelized Cost of Energy)
    - Minimize Payback Period
    - Maximize Year 1 Savings (via -Savings)

The same design space is used in all three cases:
    - Thermal storage hours (tshours)
    - Solar multiple (SM)
    - Loop outlet temperature (T_loop_out)

Results show how different objective choices lead to different
optimal design points, demonstrating the trade-offs involved in
techno-economic decision-making.

Note: All optimizations use NREL PySAM via a custom simulation wrapper.
"""

import sys
sys.path.append(".")

from sammoo import ConfigSelection, ParMOOSim

import pandas as pd

# Diseño del sistema
designVariables = {
    "tshours": ([0, 20], "integer"),
    "specified_solar_multiple": ([0.7, 4.0], "continuous"),
    "T_loop_out": ([200, 400], "integer")
}

# Lista de funciones objetivo a estudiar por separado
objectives = [
    ("-LCS", "Maximize Life Cycle Savings"),
    ("LCOE", "Minimize Levelized Cost of Energy"),
    ("Payback", "Minimize Simple Payback Period"),
    ("-NPV", "Maximize Net Present Value"),
]

# Almacena los mejores resultados de cada caso
summary_rows = []

# Ejecutar la optimización para cada función objetivo
for obj_name, description in objectives:
    print(f"\n========== Optimizing objective: {description} ==========")

    # Crear configuración y optimizador
    config = ConfigSelection("Commercial owner", [obj_name], designVariables)
    moop = ParMOOSim(config)

    # Ejecutar optimización (ajusta sim_max según coste del modelo)
    moop.solve_all(sim_max=1)

    # Obtener resultados (el mejor diseño)
    results = moop.get_results()
    best = results.sort_values(by=obj_name).iloc[0] if not obj_name.startswith("-") else results.sort_values(by=obj_name, ascending=False).iloc[0]

    # Añadir métricas adicionales ejecutando el mejor punto
    config.set_debug_outputs(["-LCS", "LCOE", "Payback", "-NPV"])
    x_input = {var: best[var] for var in designVariables.keys()}
    config.set_inputs(x_input)
    extended_outputs = config.sim_func(x_input)

    output_map = {name: val for name, val in zip(config.selected_outputs, extended_outputs)}

    # Guardar resumen
    summary_rows.append({
        "Objective": description,
        "tshours": x_input["tshours"],
        "SM": x_input["specified_solar_multiple"],
        "T_loop_out": x_input["T_loop_out"],
        "LCS [€]": output_map.get("-LCS", "-"),
        "LCOE [€/kWh]": output_map.get("LCOE", "-"),
        "Payback [yrs]": output_map.get("Payback", "-"),
        #"LCS [€]": best["-LCS"] if "-LCS" in results.columns else "-",
        #"LCOE [€/kWh]": best["LCOE"] if "LCOE" in results.columns else "-",
        #"Payback [yrs]": best["Payback"] if "Payback" in results.columns else "-"
    })

# Mostrar tabla resumen
summary_df = pd.DataFrame(summary_rows)
print("\n========== Comparison of Optimal Designs ==========")
print(summary_df.to_string(index=False))