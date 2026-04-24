"""Stub for Box-Behnken designs. TODO: implement BBD for 3-7 factors."""

from .base import DesignGenerator

class BBDGenerator(DesignGenerator):
    """Box-Behnken Design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'bbd')
    
    def generate(self, **kwargs):
        raise NotImplementedError("BBD not yet implemented.")
