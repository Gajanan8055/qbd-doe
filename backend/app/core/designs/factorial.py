"""Stub for Full Factorial designs. TODO: implement 2^k and general m^k designs."""

import numpy as np
import pandas as pd
from .base import DesignGenerator

class FactorialGenerator(DesignGenerator):
    """Full factorial design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'factorial')
    
    def generate(self, levels: int = 2, n_center: int = 3, **kwargs) -> pd.DataFrame:
        """TODO: Implement full factorial generation."""
        raise NotImplementedError("Full factorial not yet implemented. Use CCD for optimization or stub with pyDOE3 ff2n.")
