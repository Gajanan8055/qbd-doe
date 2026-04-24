"""
Test CCD generator against Montgomery Example 11-2.
"""

import numpy as np
import pytest
from app.core.designs.ccd import CCDGenerator

# Montgomery Example 11-2: Chemical process with 3 factors
# Expected design matrix characteristics
MONTGOMERY_K3_N = 20  # 2^3 + 2*3 + 6 center = 8 + 6 + 6 = 20

class TestCCD:
    """CCD known-answer tests."""
    
    def test_k3_design_size(self):
        """CCD with k=3 should produce 20 runs (8 factorial + 6 axial + 6 center)."""
        factors = [
            {'name': 'Time', 'unit': 'min', 'low': 80, 'center': 90, 'high': 100},
            {'name': 'Temp', 'unit': '°C', 'low': 170, 'center': 175, 'high': 180},
            {'name': 'Catalyst', 'unit': '%', 'low': 2, 'center': 3, 'high': 4},
        ]
        gen = CCDGenerator(factors)
        design = gen.generate(n_center=6)
        
        assert len(design) == 20, f"Expected 20 runs, got {len(design)}"
        assert len(design.columns) >= 8, "Should have Run, StdOrder, RunOrder, Block + 3 factors + Notes"
    
    def test_k3_alpha_rotatable(self):
        """Rotatable alpha for k=3 should be (2^3)^(1/4) = 1.682."""
        factors = [
            {'name': 'A', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
            {'name': 'B', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
            {'name': 'C', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
        ]
        gen = CCDGenerator(factors)
        info = gen.get_design_info()
        
        expected_alpha = (2 ** 3) ** 0.25
        assert abs(info['alpha'] - expected_alpha) < 0.01
    
    def test_engineering_unit_conversion(self):
        """Coded -1/+1 should map to correct engineering units."""
        factors = [
            {'name': 'Temp', 'unit': '°C', 'low': 70, 'center': 80, 'high': 90},
        ]
        gen = CCDGenerator(factors)
        design = gen.generate()
        
        # Check that low and high appear in the design
        temps = design['Temp'].values
        assert any(abs(t - 70) < 0.1 for t in temps), "Low level should appear"
        assert any(abs(t - 90) < 0.1 for t in temps), "High level should appear"
        assert any(abs(t - 80) < 0.1 for t in temps), "Center level should appear"
    
    def test_randomization(self):
        """RunOrder should be a permutation of 1..n."""
        factors = [
            {'name': 'A', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
            {'name': 'B', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
        ]
        gen = CCDGenerator(factors)
        design = gen.generate(seed=42)
        
        n = len(design)
        run_orders = sorted(design['RunOrder'].values)
        expected = list(range(1, n + 1))
        assert run_orders == expected, "RunOrder should be a permutation"
    
    def test_reproducibility(self):
        """Same seed should produce same design."""
        factors = [
            {'name': 'A', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
            {'name': 'B', 'unit': '', 'low': -1, 'center': 0, 'high': 1},
        ]
        gen1 = CCDGenerator(factors)
        d1 = gen1.generate(seed=123)
        
        gen2 = CCDGenerator(factors)
        d2 = gen2.generate(seed=123)
        
        pd.testing.assert_frame_equal(d1.sort_values('Run'), d2.sort_values('Run'))


import pandas as pd
