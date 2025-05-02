from parmoo import MOOP
from parmoo.optimizers import GlobalSurrogate_PS
from parmoo.searches import LatinHypercube
from parmoo.surrogates import GaussRBF
from parmoo.acquisitions import RandomConstraint
from parmoo.viz import scatter

class ParMOOSim:
    def __init__(self, sim_func, desVarDict, objDict, search_budget=100, switch_after=5, batch_size=5, auto_switch=False):
        """
        Initializes a ParMOOSim optimization object.

        Parameters:
            sim_func: function
                Simulation function.
            desVarDict: dict
                Dictionary of design variables.
            objDict: dict
                Dictionary of objective functions.
            search_budget: int
                Initial sampling budget.
            switch_after: int
                Number of sequential steps before switching to batch (if auto_switch is True).
            batch_size: int
                Number of acquisitions to add when switching to batch.
            auto_switch: bool
                Whether to switch automatically from sequential to batch.
        """
        # Fix the random seed for reproducibility using the np_random_gen hyperparams
        self.my_moop = MOOP(GlobalSurrogate_PS, hyperparams={'np_random_gen': 0})

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
            'm': len(objDict),
            'sim_func': sim_func,
            'search': LatinHypercube,
            'surrogate': GaussRBF,
            'hyperparams': {'search_budget': search_budget}
        })

        # Add objectives
        for key,value in objDict.items():
            self.my_moop.addObjective({'name': key, 'obj_func': value})

        self.num_steps = 0
        self.switch_after = switch_after
        self.batch_size = batch_size
        self.switched_to_batch = False
        self.auto_switch = auto_switch
        self.prev_objectives = []  # guardará las medias de los objetivos previos

        #def c1(x, s): return 0.1 - x["x1"]
        #my_moop.addConstraint({'name': "c1", 'constraint': c1})

        # By default, add 3 acquisitions initially
        self.initial_acquisitions(3)

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

    def solve_all(self):
        """
        Executes all pending acquisitions (batch optimization).
        Automatically called if auto_switch is enabled.
        """
        print(f"Executing {self.batch_size if self.switched_to_batch else 'all pending'} acquisitions in batch...")
        self.my_moop.solve()
        print("Executed all pending acquisitions.")

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
        scatter(self.my_moop, output=output)
        print(f"Pareto front plotted {'to ' + output if output else 'interactively'}")

    def interactive_loop(self, steps=5):
        """
        Run an interactive optimization loop.

        Parameters:
            steps: int
                Number of acquisitions to perform interactively.
        """
        for step in range(steps):
            input(f"\nStep {step + 1}/{steps}: Press Enter to execute next acquisition...")
            self.add_acquisition()  # Optionally allow user to choose method interactively
            self.optimize_step()
            self.plot_results()
            results = self.get_results()
            print(f"Current Pareto front ({len(results)} points):")
            print(results)