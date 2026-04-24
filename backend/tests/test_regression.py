"""
Test regression and ANOVA against known examples.
"""

import numpy as np
import pandas as pd
import pytest
from app.core.analysis.regression import RegressionAnalyzer
from app.core.analysis.anova import ANOVAAnalyzer

class TestRegression:
    """Regression known-answer tests."""
    
    def test_simple_linear_regression(self):
        """Test basic linear regression with known slope/intercept."""
        # y = 2 + 3x + noise
        np.random.seed(42)
        x = np.array([1, 2, 3, 4, 5])
        y = 2 + 3 * x + np.random.normal(0, 0.1, 5)
        
        df = pd.DataFrame({'x': x, 'y': y})
        reg = RegressionAnalyzer(df, ['x'], 'y')
        results = reg.fit(quadratic=False, interactions=False)
        
        # Check R² is high
        assert results['r2'] > 0.99, f"R² should be near 1 for perfect linear data, got {results['r2']}"
    
    def test_quadratic_regression(self):
        """Test quadratic term detection."""
        np.random.seed(42)
        x = np.linspace(-1, 1, 20)
        y = 5 + 2*x + 3*x**2 + np.random.normal(0, 0.1, 20)
        
        df = pd.DataFrame({'x': x, 'y': y})
        reg = RegressionAnalyzer(df, ['x'], 'y')
        results = reg.fit(quadratic=True, interactions=False)
        
        # Should have x^2 term
        terms = [c['Term'] for c in results['coefficients']]
        assert 'x^2' in terms, "Quadratic term should be present"
        
        # R² should be high
        assert results['r2'] > 0.95


class TestANOVA:
    """ANOVA tests."""
    
    def test_anova_ss_decomposition(self):
        """SS components should sum to total SS."""
        # Simple 2x2 factorial
        np.random.seed(42)
        data = []
        for a in [-1, 1]:
            for b in [-1, 1]:
                for _ in range(3):  # 3 replicates
                    y = 10 + 2*a + 3*b + 1.5*a*b + np.random.normal(0, 0.5)
                    data.append({'A': a, 'B': b, 'y': y})
        
        df = pd.DataFrame(data)
        anova = ANOVAAnalyzer(df, ['A', 'B'], 'y')
        results = anova.run_anova(model_type='interaction')
        
        # Total SS should equal model SS + residual SS
        total = results['total_ss']
        model_plus_resid = results['model_ss'] + results['residual_ss']
        assert abs(total - model_plus_resid) < 1e-6, "SS should decompose exactly"
