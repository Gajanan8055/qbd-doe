"""Stub for Definitive Screening Designs. TODO: implement DSD for k >= 4."""

from .base import DesignGenerator

class DSDGenerator(DesignGenerator):
    """Definitive Screening Design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'dsd')
    
    def generate(self, **kwargs):
        raise NotImplementedError("DSD not yet implemented.")
