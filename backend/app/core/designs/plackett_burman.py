"""Stub for Plackett-Burman screening designs. TODO: implement PB for n-1 factors."""

from .base import DesignGenerator

class PlackettBurmanGenerator(DesignGenerator):
    """Plackett-Burman design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'plackett_burman')
    
    def generate(self, **kwargs):
        raise NotImplementedError("Plackett-Burman not yet implemented.")
