"""Stub for Fractional Factorial designs. TODO: implement 2^(k-p) with resolution."""

from .base import DesignGenerator

class FractionalFactorialGenerator(DesignGenerator):
    """Fractional factorial design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'frac_factorial')
    
    def generate(self, resolution: int = 5, **kwargs):
        raise NotImplementedError("Fractional factorial not yet implemented.")
