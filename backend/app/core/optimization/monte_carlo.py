"""
Monte Carlo simulation for design space and robustness.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Callable, Tuple

class MonteCarloSimulator:
    """Monte Carlo process variation simulation."""
    
    def __init__(self, models: Dict[str, Callable], cqa_specs: List[Dict]):
        """
        Args:
            models: Dict mapping CQA name -> prediction function
            cqa_specs: List of CQA specification dicts
        """
        self.models = models
        self.cqa_specs = cqa_specs
    
    def simulate(self, setpoint: np.ndarray, sigmas: np.ndarray, 
                 n_samples: int = 10000, seed: int = 42) -> Dict:
        """
        Simulate process variation at a setpoint.
        
        Args:
            setpoint: Factor settings in coded units
            sigmas: Standard deviation for each factor (in coded units)
            n_samples: Number of Monte Carlo samples
            seed: Random seed
            
        Returns:
            Dict with simulation results
        """
        np.random.seed(seed)
        
        # Sample factor variations
        n_factors = len(setpoint)
        factor_samples = np.zeros((n_samples, n_factors))
        for i in range(n_factors):
            factor_samples[:, i] = np.random.normal(setpoint[i], sigmas[i], n_samples)
        
        # Propagate through models
        cqa_distributions = {}
        all_in_spec = np.ones(n_samples, dtype=bool)
        
        for cqa_name, spec in zip(self.models.keys(), self.cqa_specs):
            # Predict for all samples
            y_samples = np.array([self.models[cqa_name](factor_samples[j, :]) 
                                  for j in range(n_samples)])
            
            # Check specification
            L = spec.get('lower', -np.inf)
            U = spec.get('upper', np.inf)
            in_spec = (y_samples >= L) & (y_samples <= U)
            all_in_spec &= in_spec
            
            cqa_distributions[cqa_name] = {
                'samples': y_samples.tolist(),
                'mean': float(np.mean(y_samples)),
                'std': float(np.std(y_samples)),
                'min': float(np.min(y_samples)),
                'max': float(np.max(y_samples)),
                'median': float(np.median(y_samples)),
                'p5': float(np.percentile(y_samples, 5)),
                'p95': float(np.percentile(y_samples, 95)),
                'in_spec_fraction': float(np.mean(in_spec)),
                'lower_spec': L if L > -np.inf else None,
                'upper_spec': U if U < np.inf else None,
            }
        
        # Overall probability
        p_all_specs = float(np.mean(all_in_spec))
        
        return {
            'setpoint': setpoint.tolist(),
            'n_samples': n_samples,
            'cqa_distributions': cqa_distributions,
            'probability_all_specs': p_all_specs,
            'overall_risk': 'LOW' if p_all_specs > 0.99 else ('MEDIUM' if p_all_specs > 0.95 else 'HIGH'),
        }
    
    def map_design_space(self, factor1_range: np.ndarray, factor2_range: np.ndarray,
                         fixed_factors: Dict[int, float], sigmas: np.ndarray,
                         threshold: float = 0.95, n_samples: int = 1000,
                         seed: int = 42) -> pd.DataFrame:
        """
        Map 2D design space by running MC at each grid point.
        
        Args:
            factor1_range: Array of values for factor 1
            factor2_range: Array of values for factor 2
            fixed_factors: Dict mapping factor index -> fixed value for other factors
            sigmas: Std dev for each factor
            threshold: Probability threshold for design space boundary
            
        Returns:
            DataFrame with grid columns + P(all specs)
        """
        results = []
        
        for f1 in factor1_range:
            for f2 in factor2_range:
                # Build setpoint
                n_factors = len(sigmas)
                setpoint = np.zeros(n_factors)
                setpoint[0] = f1
                setpoint[1] = f2
                for idx, val in fixed_factors.items():
                    setpoint[idx] = val
                
                # Run MC
                mc_result = self.simulate(setpoint, sigmas, n_samples, seed)
                p = mc_result['probability_all_specs']
                
                results.append({
                    'factor1': f1,
                    'factor2': f2,
                    'probability': p,
                    'in_design_space': p >= threshold,
                })
        
        return pd.DataFrame(results)
