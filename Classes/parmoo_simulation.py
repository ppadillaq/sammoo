from parmoo import MOOP
from parmoo.optimizers import GlobalSurrogate_PS
from parmoo.searches import LatinHypercube
from parmoo.surrogates import GaussRBF
from parmoo.acquisitions import RandomConstraint
from parmoo.viz import scatter

class ParMOOSim:
    def __init__(self, config, desVarDict, search_budget=10, switch_after=5, batch_size=5, auto_switch=False, epsilon=1e-3):
        """
        Initializes a ParMOOSim optimization object.

        Parameters:
            config: object
                ConfigSelection object.
            desVarDict: dict
                Dictionary of design variables.
            objective_names: list
                List of objective functions names.
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
        """
        # Fix the random seed for reproducibility using the np_random_gen hyperparams
        self.my_moop = MOOP(GlobalSurrogate_PS, hyperparams={'np_random_gen': 0})

        # Save configuration
        self.desVarDict = desVarDict
        self.objective_names = config.selected_outputs
        self.sim_func = config.sim_func
        self.search_budget = search_budget

        # Add design variables
        for key,value in desVarDict.items():
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

        self.num_steps = 0
        self.switch_after = switch_after
        self.batch_size = batch_size
        self.switched_to_batch = False
        self.auto_switch = auto_switch
        self.prev_objectives = []  # guardará las medias de los objetivos previos

        self.epsilon = epsilon

        #def c1(x, s): return 0.1 - x["x1"]
        #my_moop.addConstraint({'name': "c1", 'constraint': c1})

        # By default, add 3 acquisitions initially
        self.initial_acquisitions(3)

    def _add_objectives(self):
        for idx, name in enumerate(self.objective_names):
            def make_obj_func(index):
                def obj_func(x, s):
                    return s["SAMOptim"][index]
                return obj_func
            #def obj_func(x, s, index=idx):
            #    return s["SAMOptim"][index]
            self.my_moop.addObjective({'name': name, 'obj_func': make_obj_func(idx)})

    def _obj_func_wrapper(self, x, s, index):
        return s["SAMOptim"][index]
    
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
        """Execute a single optimization step (one acquisition)."""
        if self.switched_to_batch:
            print("[WARN] Already in batch mode. Use solve_all() instead of optimize_step().")
            return

        self.num_steps += 1
        print(f"Optimizing step {self.num_steps} (sequential)...")
        self.my_moop.optimize()
        print("Executed one optimization step.")

        # Obtener resultados actuales
        results = self.my_moop.getPF(format="pandas")
        mean_obj = results.mean().values  # vector de medias por objetivo
        mean_obj_scalar = mean_obj.mean()  # valor medio general

        # Guardar historial
        self.prev_objectives.append(mean_obj_scalar)

        # Comparar mejora si hay al menos dos pasos
        if len(self.prev_objectives) >= 2:
            delta = abs(self.prev_objectives[-1] - self.prev_objectives[-2])
            print(f"Delta mean objective: {delta}")

            # Si mejora es menor que threshold → activar batch
            if self.auto_switch and not self.switched_to_batch and delta < self.epsilon:
                self.switched_to_batch = True
                print(f"\n[INFO] Auto-switching to batch mode: improvement delta {delta:.4f} < {self.epsilon}")
                for _ in range(self.batch_size):
                    self.add_acquisition()
                self.solve_all(plot_output=plot_output)

    def solve_all(self, sim_max, plot_output=None):
        """
        Executes all pending acquisitions (batch optimization).
        Automatically called if auto_switch is enabled.
        """
        print(f"Executing {self.batch_size if self.switched_to_batch else 'all pending'} acquisitions in batch...")
        self.my_moop.solve(sim_max=sim_max)
        print("Executed all pending acquisitions.")

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
        for key, value in self.desVarDict.items():
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

        # Reset internal state
        self.num_steps = 0
        self.prev_objectives = []
        self.switched_to_batch = False

        # Optionally: re-add initial acquisitions (if needed)
        self.initial_acquisitions(3)

        print("[INFO] Reset complete.")