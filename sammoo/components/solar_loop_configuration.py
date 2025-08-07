class SolarLoopConfiguration:
    def __init__(self, n_sca_per_loop: int = 8):
        self.n_sca_per_loop = n_sca_per_loop

    def generate_trough_loop_control(self) -> list[int]:
        control = [self.n_sca_per_loop]
        for df_order in reversed(range(1, self.n_sca_per_loop + 1)):
            control.extend([1, 1, df_order])  # SCA type = 1, HCE type = 1
        return control

    def apply_to_config(self, config):
        """
        Applies the generated trough_loop_control to a PySAM configuration.
        Assumes config is a ConfigSelection instance or has access to the relevant module.
        """
        control_array = self.generate_trough_loop_control()
        config.set_input("trough_loop_control", control_array)
