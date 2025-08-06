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
# Create configuration and optimizer
# -----------------------------
config = ConfigSelection(
    config="Commercial owner",
    selected_outputs=obj_functions,
    design_variables=design_variables,
    collector_name="Power Trough 250",  # Default collector
    verbose=0
)

# -----------------------------
# Initialize and solve optimization problem
# -----------------------------
my_moop = ParMOOSim(config, search_budget=10)
my_moop.solve_all(sim_max=10) # sim_max=1 for faster evaluation; increase for better convergence

# -----------------------------
# Output results
# -----------------------------
results = my_moop.get_results()
print(results)