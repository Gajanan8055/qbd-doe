"""Stub for D-optimal designs. TODO: implement Fedorov exchange algorithm."""

from .base import DesignGenerator

class DOptimalGenerator(DesignGenerator):
    """D-optimal design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'd_optimal')
    
    def generate(self, n_runs: int = None, **kwargs):
        raise NotImplementedError("D-optimal not yet implemented.")
