from parmoo import MOOP
from parmoo.optimizers import GlobalSurrogate_PS
from parmoo.searches import LatinHypercube
from parmoo.surrogates import GaussRBF
from parmoo.acquisitions import RandomConstraint

class ParMOOSim:
    def __init__(self, sim_func, desVarDict, objDict):
        # Fix the random seed for reproducibility using the np_random_gen hyperparams
        self.my_moop = MOOP(GlobalSurrogate_PS, hyperparams={'np_random_gen': 0})

        for key,value in desVarDict.items():
            self.my_moop.addDesign({'name': key,
                                    'des_type': "integer",
                                    'lb': value[0], 'ub': value[1]})
        # Note: the 'levels' key can contain a list of strings, but jax can only jit
        # numeric types, so integer level IDs are strongly recommended
        
        self.my_moop.addSimulation({'name': "SAMOptim",
                       'm': 2,
                       'sim_func': sim_func,
                       'search': LatinHypercube,
                       'surrogate': GaussRBF,
                       'hyperparams': {'search_budget': 10}})

        for key,value in objDict.items():
            self.my_moop.addObjective({'name': key, 'obj_func': value})

        #self.my_moop.addObjective({'name': "-CF", 'obj_func': f1})
        #self.my_moop.addObjective({'name': "LCOE", 'obj_func': f2})

        #def c1(x, s): return 0.1 - x["x1"]
        #my_moop.addConstraint({'name': "c1", 'constraint': c1})

        for i in range(3):
            self.my_moop.addAcquisition({'acquisition': RandomConstraint,
                           'hyperparams': {}})
            

    def solve(self):
        self.my_moop.solve(5)
        results = self.my_moop.getPF(format="pandas")

        # Display solution
        print(results)

        # Plot results -- must have extra viz dependencies installed
        from parmoo.viz import scatter
        # The optional arg `output` exports directly to jpeg instead of interactive mode
        scatter(self.my_moop, output="jpeg")