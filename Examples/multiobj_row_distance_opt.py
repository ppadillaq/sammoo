"""
Multi-objective thermo-economic optimization of a parabolic trough solar power plant
using ParMOO and NREL PySAM.

This script defines a fixed design point for the plant using three key parameters:
    - 'tshours': thermal energy storage duration (in hours)
    - 'T_loop_out': outlet temperature of the solar loop (°C)
    - 'specified_solar_multiple': design solar multiple

These parameters are set using the 'set_inputs' method of the 'ConfigSelection' class,
representing the nominal size and performance of the system at design conditions.

The optimization focuses on a single design variable:
    - 'Row_Distance': center-to-center spacing between solar collector rows [m]

This spacing affects the land area and optical performance:
    - Reducing it decreases land use and capital cost, but increases optical losses due to row-to-row shading.
    - Increasing it reduces shading losses but requires more land and thus higher costs.

Three objective functions are considered:
    - 'LCOE': Levelized Cost of Electricity [€/kWh] – to minimize
    - 'Payback': Simple Payback Period [years] – to minimize
    - '-Savings': First year savings [€] – to maximize (negated for minimization framework)

The goal is to identify the optimal row spacing that balances cost, performance, and return metrics.
"""

import sys
sys.path.append(".")

from Classes.config_selection import ConfigSelection
from Classes.parmoo_simulation import ParMOOSim

# Define the design variable to optimize
designVariables = {
    "Row_Distance": ([5.0, 15.0], "continuous")  # Row spacing in meters
}

# Define the objective functions
objectiveFunctions = ["LCOE", "Payback", "-Savings"]

# Create the simulation configuration
config = ConfigSelection("Commercial owner", objectiveFunctions, designVariables)

# Set plant design point (fixed thermal capacity scenario)
config.set_inputs({
    "tshours": 6,                    # Thermal energy storage duration [h]
    "T_loop_out": 390,              # Loop outlet temperature [°C]
    "specified_solar_multiple": 2.5 # Solar multiple (design capacity multiplier)
})

# Instantiate the optimizer
my_moop = ParMOOSim(config)

# Run the multi-objective optimization (can increase sim_max for broader exploration)
my_moop.solve_all(sim_max=1)

# Retrieve and print the optimization results
results = my_moop.get_results()
print("Multi-objective optimization results for varying Row_Distance:")
print(results)
