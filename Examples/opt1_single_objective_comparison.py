# examples/opt1_single_objective_comparison.py


"""
single_objective_comparison.py

Performs three independent single-objective thermo-economic optimizations
using different cost functions for a CSP system design problem.

Each optimization uses a different objective function:
    - Minimize LCOE (Levelized Cost of Energy)
    - Minimize Payback Period
    - Maximize Life Cycle Savings (via -LCS)
    - Maximize Net Present Value (via -NPV)

The same design space is used in all cases:
    - Thermal storage hours (tshours)
    - Solar multiple (SM)
    - Loop outlet temperature (T_loop_out)
    - Number of SCA per loop (n_sca_per_loop)

Results show how different objective choices lead to different
optimal design points, demonstrating the trade-offs involved in
techno-economic decision-making.

Note: All optimizations use NREL PySAM via a custom simulation wrapper.
"""

import pandas as pd
from sammoo import ConfigSelection, ParMOOSim
from sammoo.components import ThermalLoadProfileLPG


# Monthly LPG consumption data (kg)
monthly_data = {
    1: 11343,  2: 15133,  3: 4983,
    4: 13221,  5: 7250,   6: 12137,
    7: 8055,   8: 7542,   9: 7605,
    10: 12899, 11: 6090,  12: 12343
}

# Generate hourly thermal load profile from monthly LPG consumption
profile = ThermalLoadProfileLPG(monthly_kg=monthly_data)

# System design variables and bounds
designVariables = {
    "tshours": ([0, 24], "integer"),
    "specified_solar_multiple": ([0.7, 5.0], "continuous"),
    "T_loop_out": ([200, 250], "integer"),
    "n_sca_per_loop": ([7, 20], "integer"),
}

# List of single-objective optimizations to run
objectives = [
    ("-LCS", "Maximize Life Cycle Savings"),
    ("LCOE", "Minimize Levelized Cost of Energy"),
    ("Payback", "Minimize Simple Payback Period"),
    ("-NPV", "Maximize Net Present Value"),
]

# Store best results from each optimization case
summary_rows = []

# Run optimization for each objective
for obj_name, description in objectives:
    print(f"\n========== Optimizing objective: {description} ==========")

    # Create SAM configuration
    config = ConfigSelection(
        config="Commercial owner",
        selected_outputs=[obj_name],
        design_variables=designVariables,
        collector_name="Absolicon T160",
        htf_name="Therminol VP-1",
        verbose=0
        )
    
    # Apply demand profile → sets timestep_load_abs and q_pb_design
    profile.apply_to_config(config)

    # Create optimizer
    moop = ParMOOSim(config, search_budget=50)

    # Run optimization (adjust sim_max depending on model runtime cost)
    moop.solve_all(sim_max=100, plot=False)

    # Retrieve results (select best design)
    results = moop.get_results()
    best = results.sort_values(by=obj_name).iloc[0] if not obj_name.startswith("-") else results.sort_values(by=obj_name, ascending=False).iloc[0]

    # Run simulation at best point to retrieve extended outputs
    config.set_debug_outputs(["-LCS", "LCOE", "Payback", "-NPV"])
    x_input = {var: best[var] for var in designVariables.keys()}
    config.set_inputs(x_input)
    extended_outputs = config.sim_func(x_input)

    output_map = {name: val for name, val in zip(config.selected_outputs, extended_outputs)}

    # Store summary row
    summary_rows.append({
        "Objective": description,
        "tshours": x_input["tshours"],
        "SM": x_input["specified_solar_multiple"],
        "T_loop_out": x_input["T_loop_out"],
        "SCA/loop": x_input["n_sca_per_loop"],
        "LCS [€]": output_map.get("-LCS", "-"),
        "LCOE [€/kWh]": output_map.get("LCOE", "-"),
        "Payback [yrs]": output_map.get("Payback", "-"),
        "NPV [€]": output_map.get("-NPV", "-"),
    })

# Display summary table
summary_df = pd.DataFrame(summary_rows)
print("\n========== Comparison of Optimal Designs ==========")
print(summary_df.to_string(index=False))