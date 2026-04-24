"""
Test Derringer-Suich desirability against published example.
"""

import numpy as np
import pytest
from app.core.optimization.desirability import DesirabilityOptimizer

class TestDesirability:
    """Desirability function tests."""
    
    def test_maximize_desirability(self):
        """d=0 below L, d=1 above T, linear in between."""
        opt = DesirabilityOptimizer({}, [])
        
        spec = {'goal': 'maximize', 'lower': 10, 'target': 20, 'upper': 30}
        
        assert opt.individual_desirability(5, spec) == pytest.approx(0.0, abs=1e-6)
        assert opt.individual_desirability(10, spec) == pytest.approx(0.0, abs=1e-6)
        assert opt.individual_desirability(15, spec) == pytest.approx(0.5, abs=1e-6)
        assert opt.individual_desirability(20, spec) == pytest.approx(1.0, abs=1e-6)
        assert opt.individual_desirability(25, spec) == pytest.approx(1.0, abs=1e-6)
    
    def test_minimize_desirability(self):
        """d=0 above U, d=1 below T, linear in between."""
        opt = DesirabilityOptimizer({}, [])
        
        spec = {'goal': 'minimize', 'lower': 0, 'target': 10, 'upper': 20}
        
        assert opt.individual_desirability(5, spec) == pytest.approx(1.0, abs=1e-6)
        assert opt.individual_desirability(10, spec) == pytest.approx(1.0, abs=1e-6)
        assert opt.individual_desirability(15, spec) == pytest.approx(0.5, abs=1e-6)
        assert opt.individual_desirability(20, spec) == pytest.approx(0.0, abs=1e-6)
        assert opt.individual_desirability(25, spec) == pytest.approx(0.0, abs=1e-6)
    
    def test_target_desirability(self):
        """Piecewise: maximize to target, minimize from target."""
        opt = DesirabilityOptimizer({}, [])
        
        spec = {'goal': 'target', 'lower': 0, 'target': 10, 'upper': 20}
        
        assert opt.individual_desirability(0, spec) == pytest.approx(0.0, abs=1e-6)
        assert opt.individual_desirability(5, spec) == pytest.approx(0.5, abs=1e-6)
        assert opt.individual_desirability(10, spec) == pytest.approx(1.0, abs=1e-6)
        assert opt.individual_desirability(15, spec) == pytest.approx(0.5, abs=1e-6)
        assert opt.individual_desirability(20, spec) == pytest.approx(0.0, abs=1e-6)
    
    def test_overall_desirability(self):
        """Geometric mean of individual desirabilities."""
        opt = DesirabilityOptimizer({}, [])
        
        # Two CQAs, both with d=1, weights=1
        D = opt.overall_desirability([1.0, 1.0], [1.0, 1.0])
        assert D == pytest.approx(1.0, abs=1e-6)
        
        # One d=0 → overall D=0
        D = opt.overall_desirability([1.0, 0.0], [1.0, 1.0])
        assert D == pytest.approx(0.0, abs=1e-6)
        
        # d=0.5, d=1.0, equal weights → D = sqrt(0.5 * 1.0) = sqrt(0.5)
        D = opt.overall_desirability([0.5, 1.0], [1.0, 1.0])
        assert D == pytest.approx(np.sqrt(0.5), abs=1e-6)
