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


class SolarLoopConfiguration:
    """
    Defines and applies a standard trough loop configuration for parabolic trough collectors.

    This class generates the `trough_loop_control` array used by SAM to configure
    the arrangement of Solar Collector Assemblies (SCAs) in each loop.

    Assumptions:
        - All SCAs in the plant are of the same type (SCA type = 1).
        - All Heat Collection Elements (HCEs) are of the same type (HCE type = 1).
        - Defocus order follows the standard descending sequence: n, n-1, ..., 2, 1.
        - The number of SCAs per loop can be adjusted via `n_sca_per_loop`.

    Parameters
    ----------
    n_sca_per_loop : int, optional
        Number of Solar Collector Assemblies per loop. Default is 8.

    Example
    -------
    >>> loop_config = SolarLoopConfiguration(n_sca_per_loop=6)
    >>> loop_config.generate_trough_loop_control()
    [6, 1, 1, 6, 1, 1, 5, 1, 1, 4, 1, 1, 3, 1, 1, 2, 1, 1, 1]
    """
    def __init__(self, n_sca_per_loop: int = 8):
        self.n_sca_per_loop = n_sca_per_loop

    def generate_trough_loop_control(self) -> list[int]:
        """
        Generates the `trough_loop_control` list according to SAM's expected format.

        Structure:
            [n_sca_per_loop, SCA_type, HCE_type, defocus_order, ...]

        Returns
        -------
        list[int]
            The complete `trough_loop_control` array for the given loop configuration.
        """
        control = [self.n_sca_per_loop]
        for df_order in reversed(range(1, self.n_sca_per_loop + 1)):
            # Append [SCA_type, HCE_type, defocus_order] for each SCA in the loop
            control.extend([1, 1, df_order])  # SCA type = 1, HCE type = 1
        return control

    def apply_to_config(self, config):
        """
        Applies the generated trough_loop_control to a PySAM configuration.
        Assumes config is a ConfigSelection instance or has access to the relevant module.

        Parameters
        ----------
        config : ConfigSelection or compatible object
            Instance that has a `set_input(key, value)` method to assign
            the `trough_loop_control` array.

        Notes
        -----
        - This method assumes that the key `"trough_loop_control"` is valid
          for the given `config` object.
        """
        control_array = self.generate_trough_loop_control()
        config.set_input("trough_loop_control", control_array)
