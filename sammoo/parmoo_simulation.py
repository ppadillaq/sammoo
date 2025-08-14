# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2025, Pedro Padilla Quesada
# All rights reserved.
#
# This file is part of the sammoo project: a Python-based framework
# for multi-objective optimization of renewable energy systems using
# NREL's System Advisor Model (SAM).
#
# Distributed under the terms of the BSD 3-Clause License.
# For full license text, see the LICENSE file in the project root.


from parmoo import MOOP
from parmoo.optimizers import GlobalSurrogate_PS
from parmoo.searches import LatinHypercube
from parmoo.surrogates import GaussRBF
from parmoo.acquisitions import RandomConstraint
from parmoo.viz import scatter

class ParMOOSim:
    def __init__(self, config, search_budget=10, switch_after=5, batch_size=5, auto_switch=False, epsilon=1e-3, initial_acq=3):
        """
        Initializes a ParMOOSim optimization object.

        This class supports both sequential and batch optimization modes, with the option
        to automatically switch between them based on convergence criteria. This provides
        flexibility for different optimization workflows, from exploratory single-step runs
        to efficient batch acquisitions once the solution space stabilizes.

        Parameters:
            config: ConfigSelection
                ConfigSelection object.
            search_budget: int
                Initial sampling budget.
            switch_after: int
                Number of sequential steps before switching to batch (if auto_switch is True).
            batch_size: int
                Number of acquisitions to add when switching to batch.
            auto_switch: bool
                Whether to switch automatically from sequential to batch.
            epsilon: float
                Threshold to detect convergence (used to trigger auto-switch to batch if improvement < epsilon).
            initial_acq: int
                Number of initial acquisitions added before the first optimization step (default: 3).
        """
        self.config = config

        # 🔒 Check early if weather file is missing
        weather_file = config.get_input("file_name")
        if not weather_file or weather_file.strip() == "":
            raise ValueError(
                "[ERROR] Weather file not defined in configuration. Please assign a valid path to 'file_name'."
            )
        
        # Set a fixed seed (0) to ensure reproducibility of all random operations (e.g., sampling, perturbations)
        self.my_moop = MOOP(GlobalSurrogate_PS, hyperparams={'np_random_gen': 0})

        # Save configuration
        self.design_var_dict = config.design_variables # dictionary of design variables
        self.objective_names = config.selected_outputs
        self.sim_func = config.sim_func
        self.search_budget = search_budget

        # Add design variables
        for key,value in self.design_var_dict.items():
            self.my_moop.addDesign({
                'name': key,
                'des_type': value[1],
                'lb': value[0][0],
                'ub': value[0][1]
            })

        # Note: the 'levels' key can contain a list of strings, but jax can only jit
        # numeric types, so integer level IDs are strongly recommended
        
        # Add simulation
        self.my_moop.addSimulation({
            'name': "SAMOptim",
            'm': len(self.objective_names),
            'sim_func': config.sim_func,
            'search': LatinHypercube,
            'surrogate': GaussRBF,
            'hyperparams': {'search_budget': search_budget}
        })

        # Add objectives
        self._add_objectives()

        # --- Add constraints from ConfigSelection (if any) ---
        if hasattr(self.config, "get_constraints"):
            for c in self.config.get_constraints():
                self.my_moop.addConstraint(c)
                if getattr(config, "verbose", 1) >= 1:
                    print(f"[INFO] Constraint '{c['name']}' added to MOOP.")

        self.num_steps = 0
        self.switch_after = switch_after
        self.batch_size = batch_size
        self.switched_to_batch = False
        self.auto_switch = auto_switch
        self.prev_objectives = []  # list of scalar mean values from previous Pareto front evaluations (for convergence tracking)
        self.epsilon = epsilon

        # Add initial acquisitions before starting the optimization loop
        self.initial_acquisitions(initial_acq)

    def _add_objectives(self):
        """
        Adds objective functions to the MOOP based on the user's selection.

        Objective names are expected to come from `config.selected_outputs`, where
        a leading minus sign ('-') indicates that the objective should be maximized.

        For example:
            - "LCOE"         → minimize LCOE
            - "-net_energy"  → maximize net_energy

        Internally, each objective is registered with ParMOO by wrapping the 
        appropriate index from the SAM simulation result and applying a sign (+1 or -1).
        """
        for idx, name in enumerate(self.objective_names):
            # Detect if it is a maximization problem
            is_max = name.startswith("-")
            sign = -1 if is_max else 1

            # Define objective function based on index and sign
            def make_obj_func(index, sign=1):
                def obj_func(x, s):
                    return sign * s["SAMOptim"][index]
                return obj_func
            
            self.my_moop.addObjective({'name': name, 'obj_func': make_obj_func(idx, sign)})
    
    def initial_acquisitions(self, n=3):
        """Add an initial number of acquisitions."""
        for _ in range(n):
            self.my_moop.addAcquisition({'acquisition': RandomConstraint, 'hyperparams': {}})

    def add_acquisition(self, acquisition_method=RandomConstraint, hyperparams=None):
        """Add a single acquisition dynamically."""
        if hyperparams is None:
            hyperparams = {}
        self.my_moop.addAcquisition({'acquisition': acquisition_method, 'hyperparams': hyperparams})
        print(f"Added acquisition with {acquisition_method.__name__}")

    def optimize_step(self, plot_output=None):
        """
        Executes a single sequential optimization step using one acquisition.

        This method performs one iteration of optimization, evaluates the updated 
        Pareto front, and tracks progress based on the mean objective value. If 
        auto-switching is enabled, it monitors convergence by comparing the change 
        in average objective values and switches to batch mode if improvement falls 
        below a predefined threshold (`epsilon`).

        Parameters:
            plot_output: str or None (default: None)
                If provided, the Pareto front will be plotted or saved using the
                specified format (e.g., "png", "svg", etc.).
        """
        if self.switched_to_batch:
            print("[WARN] Already in batch mode. Use solve_all() instead of optimize_step().")
            return

        self.num_steps += 1
        print(f"Optimizing step {self.num_steps} (sequential)...")
        self.my_moop.optimize()
        print("Executed one optimization step.")

        # Get current Pareto front results
        results = self.my_moop.getPF(format="pandas")
        mean_obj = results.mean().values  # vector of mean values for each objective
        mean_obj_scalar = mean_obj.mean() # scalar average of all objectives

        # Store in history
        self.prev_objectives.append(mean_obj_scalar)

        # Compare improvement if at least two steps have been executed
        if len(self.prev_objectives) >= 2:
            delta = abs(self.prev_objectives[-1] - self.prev_objectives[-2])
            print(f"Delta mean objective: {delta}")

            # If improvement is below threshold → switch to batch mode
            if self.auto_switch and not self.switched_to_batch and delta < self.epsilon:
                self.switched_to_batch = True
                print(f"\n[INFO] Auto-switching to batch mode: improvement delta {delta:.4f} < {self.epsilon}")
                for _ in range(self.batch_size):
                    self.add_acquisition()
                self.solve_all(plot_output=plot_output)

    def solve_all(self, sim_max, plot=True, plot_output=None):
        """
        Executes all pending acquisitions (batch optimization).
        Automatically called if auto_switch is enabled.

        Parameters:
            sim_max: int
                Maximum number of simulations to perform.
            plot: bool (default: True)
                Whether to plot the Pareto front after optimization.
            plot_output: str or None (default: None)
                If provided, saves the plot to the given format ("png", "svg", etc.).
                Ignored if plot=False.
        """
        print(f"Executing {self.batch_size if self.switched_to_batch else 'all pending'} acquisitions in batch...")
        self.my_moop.solve(sim_max=sim_max)
        print("Executed all pending acquisitions.")

        if plot:
            self.plot_results(output=plot_output)

    def get_results(self, format="pandas"):
        """Retrieve Pareto front results."""
        return self.my_moop.getPF(format=format)

    def export_results(self, filename="results.csv"):
        """Export Pareto front results to CSV."""
        df = self.get_results(format="pandas")
        df.to_csv(filename, index=False)
        print(f"Results exported to {filename}")

    def plot_results(self, output=None):
        """
        Plots the Pareto front obtained by the optimization (optional output file).

        Parameters:
            output: str or None (default: None)
                - If None: Displays an interactive plot (e.g., using matplotlib window).
                - If str: Saves the plot to a file, with filename auto-generated, using the extension provided.
                        Valid options: "jpeg", "png", "svg".
                        The output file will be named automatically (e.g., 'pareto_front.jpeg').
    
        Example usage:
            plot_results()              # shows interactive plot
            plot_results(output="jpeg") # saves plot as 'pareto_front.jpeg'
        """
        if output is None:
            scatter(self.my_moop)
            print("Pareto front plotted interactively")
        else:
            scatter(self.my_moop, output=output)
            print(f"Pareto front plotted to {output}")

    def interactive_loop(self, steps=5):
        """
        Run an interactive optimization loop.

        Parameters:
            steps: int
                Number of acquisitions to perform interactively.
        """
        available_acquisitions = {
            "random": RandomConstraint,
            # aquí puedes añadir más métodos si tienes otros, por ejemplo:
            # "expected_improvement": ExpectedImprovementConstraint,
        }

        for step in range(steps):
            print(f"\nStep {step + 1}/{steps}: Available acquisition functions:")
            for i, name in enumerate(available_acquisitions.keys(), 1):
                print(f"  {i}. {name}")

            # Choose acquisition function
            valid = False
            while not valid:
                try:
                    choice = int(input(f"Select acquisition function (1-{len(available_acquisitions)}): "))
                    if 1 <= choice <= len(available_acquisitions):
                        acquisition_name = list(available_acquisitions.keys())[choice - 1]
                        acquisition_func = available_acquisitions[acquisition_name]
                        valid = True
                    else:
                        print("Invalid choice. Try again.")
                except ValueError:
                    print("Invalid input. Please enter a number.")

            print(f"Selected acquisition: {acquisition_name}")
            self.add_acquisition(acquisition_method=acquisition_func)

            # Optimize
            self.optimize_step()
            self.plot_results()

            # Show results
            results = self.get_results()
            print(f"Current Pareto front ({len(results)} points):")
            print(results)



    def reset(self):
        """
        Resets the MOOP instance to its initial state (designs, objectives, simulation),
        clearing acquisitions, Pareto front, and counters, but keeping the problem definition.
        """
        print("[INFO] Resetting MOOP to initial state...")

        # Recreate the MOOP instance
        self.my_moop = MOOP(GlobalSurrogate_PS, hyperparams={'np_random_gen': 0})

        # Re-add design variables
        for key, value in self.design_var_dict.items():
            self.my_moop.addDesign({
                'name': key,
                'des_type': value[1],
                'lb': value[0][0],
                'ub': value[0][1]
            })

        # Re-add simulation
        self.my_moop.addSimulation({
            'name': "SAMOptim",
            'm': len(self.objective_names),
            'sim_func': self.sim_func,
            'search': LatinHypercube,
            'surrogate': GaussRBF,
            'hyperparams': {'search_budget': self.search_budget}
        })

        # Re-add objectives
        self._add_objectives()

        # Re-add constraints registered in ConfigSelection
        if hasattr(self, "config") and hasattr(self.config, "get_constraints"):
            for c in self.config.get_constraints():
                self.my_moop.addConstraint(c)

        # Reset internal state
        self.num_steps = 0
        self.prev_objectives = []
        self.switched_to_batch = False

        # Optionally: re-add initial acquisitions (if needed)
        self.initial_acquisitions(3)

        print("[INFO] Reset complete.")