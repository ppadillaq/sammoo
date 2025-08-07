# examples/parabolicIPHcommercial_owner.py


"""
Performs a multi-objective thermo-economic optimization of an industrial
parabolic trough CSP system using the 'Commercial owner' configuration
from the PySAM module.

This example uses the sammoo framework to demonstrate how to optimize
three economic metrics simultaneously:
    - Levelized Cost of Energy (LCOE)
    - Simple Payback Period
    - Life Cycle Savings (LCS)

Design variables explored:
    - Thermal energy storage capacity (tshours)
    - Solar multiple (specified_solar_multiple)
    - HTF outlet temperature from solar loop (T_loop_out)

The system uses the default industrial collector: 'Power Trough 250'.
"""

from sammoo import ConfigSelection, ParMOOSim
from sammoo.components import ThermalLoadProfileLPG

# -----------------------------
# Monthly LPG consumption data (kg)
# -----------------------------
monthly_data = {
    1: 11343,  2: 15133,  3: 4983,
    4: 13221,  5: 7250,   6: 12137,
    7: 8055,   8: 7542,   9: 7605,
    10: 12899, 11: 6090,  12: 12343
}

# -----------------------------
# Generate thermal load profile
# -----------------------------
profile = ThermalLoadProfileLPG(monthly_kg=monthly_data)

# -----------------------------
# Define design space
# -----------------------------
design_variables = {"tshours": ([0,20],"integer"),                          # Thermal storage hours
                   "specified_solar_multiple": ([0.7,4.0],"continuous"),   # Solar multiple (SM)
                   "T_loop_out":([200,250],"integer")}                     # Loop outlet temperature [°C]

# -----------------------------
# Define objective functions
# -----------------------------
obj_functions = ["LCOE", "Payback","-LCS"] # Minimize LCOE, Payback; Maximize Life Cycle Savings


# -----------------------------
# Create configuration and apply thermal demand
# -----------------------------
config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=obj_functions,
    design_variables=design_variables,
    collector_name="Power Trough 250",  # Default collector
    htf_name="Therminol VP-1",
    verbose=0
)

# Apply demand profile → sets timestep_load_abs, q_pb_design and system_capacity
profile.apply_to_config(config)

# -----------------------------
# Initialize and solve optimization problem
# -----------------------------
my_moop = ParMOOSim(config, search_budget=50)
my_moop.solve_all(sim_max=50) # sim_max=1 for faster evaluation; increase for better convergence

# -----------------------------
# Output results
# -----------------------------
results = my_moop.get_results()
print(results)