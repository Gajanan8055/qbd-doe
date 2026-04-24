"""
Derringer-Suich desirability optimization.
"""

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize
from typing import Dict, List, Tuple, Callable

class DesirabilityOptimizer:
    """Multi-response desirability optimization."""
    
    def __init__(self, models: Dict[str, Callable], cqa_specs: List[Dict]):
        """
        Args:
            models: Dict mapping CQA name -> prediction function
            cqa_specs: List of dicts with keys: name, goal, target, lower, upper, weight
        """
        self.models = models
        self.cqa_specs = cqa_specs
        
    def individual_desirability(self, y: float, spec: Dict) -> float:
        """
        Compute individual desirability for one CQA.
        
        Goals:
        - maximize: d = ((y-L)/(T-L))^s if L <= y <= T, 1 if y >= T, 0 if y < L
        - minimize: d = ((U-y)/(U-T))^t if T <= y <= U, 1 if y <= T, 0 if y > U
        - target: piecewise maximize-to-target then minimize-from-target
        """
        goal = spec['goal']
        L = spec.get('lower', -np.inf)
        T = spec['target']
        U = spec.get('upper', np.inf)
        
        # Exponent (default 1 for linear)
        s = spec.get('shape', 1.0)
        
        if goal == 'maximize':
            if y < L:
                return 0.0
            elif y >= T:
                return 1.0
            else:
                return ((y - L) / (T - L)) ** s
                
        elif goal == 'minimize':
            if y > U:
                return 0.0
            elif y <= T:
                return 1.0
            else:
                return ((U - y) / (U - T)) ** s
                
        elif goal == 'target':
            # Piecewise: maximize to target, then minimize from target
            if y < L or y > U:
                return 0.0
            elif y <= T:
                return ((y - L) / (T - L)) ** s
            else:
                return ((U - y) / (U - T)) ** s
        
        else:
            raise ValueError(f"Unknown goal: {goal}")
    
    def overall_desirability(self, d_values: List[float], weights: List[float]) -> float:
        """
        Compute overall desirability: D = (prod(d_i^w_i))^(1/sum(w_i))
        """
        if any(d <= 0 for d in d_values):
            return 0.0
        
        weighted_product = np.prod([d ** w for d, w in zip(d_values, weights)])
        sum_weights = sum(weights)
        
        if sum_weights == 0:
            return 0.0
        
        return weighted_product ** (1.0 / sum_weights)
    
    def optimize(self, bounds: List[Tuple[float, float]], 
                 maxiter: int = 1000, seed: int = 42) -> Dict:
        """
        Find optimal factor settings maximizing overall desirability.
        
        Args:
            bounds: List of (low, high) for each factor in coded units
            
        Returns:
            Dict with optimal point, D, predicted CQAs, and PI
        """
        weights = [spec.get('weight', 1.0) for spec in self.cqa_specs]
        
        def objective(x):
            # x is coded factor settings
            # Predict all CQAs
            d_values = []
            for cqa_name, spec in zip(self.models.keys(), self.cqa_specs):
                y_pred = self.models[cqa_name](x)
                d = self.individual_desirability(y_pred, spec)
                d_values.append(d)
            
            D = self.overall_desirability(d_values, weights)
            return -D  # Negative because we minimize
        
        # Global optimization with differential evolution
        result_de = differential_evolution(
            objective,
            bounds,
            maxiter=maxiter,
            seed=seed,
            polish=True,
            tol=1e-6
        )
        
        # Local polish with L-BFGS-B
        result_local = minimize(
            objective,
            result_de.x,
            method='L-BFGS-B',
            bounds=bounds,
            options={'maxiter': 1000}
        )
        
        # Use best result
        if result_local.fun < result_de.fun:
            optimal_x = result_local.x
            optimal_D = -result_local.fun
        else:
            optimal_x = result_de.x
            optimal_D = -result_de.fun
        
        # Predict all CQAs at optimum
        predictions = {}
        for cqa_name in self.models:
            y_pred = self.models[cqa_name](optimal_x)
            predictions[cqa_name] = {
                'predicted': y_pred,
                # PI would need more info - placeholder
                'pi_lower': y_pred * 0.95,
                'pi_upper': y_pred * 1.05,
            }
        
        return {
            'optimal_factors': optimal_x.tolist(),
            'overall_desirability': optimal_D,
            'individual_desirabilities': [
                self.individual_desirability(predictions[cqa]['predicted'], spec)
                for cqa, spec in zip(predictions.keys(), self.cqa_specs)
            ],
            'predictions': predictions,
            'convergence': result_de.success,
            'n_iterations': result_de.nit,
        }
    
    def evaluate_grid(self, factor_grids: Dict[str, np.ndarray]) -> pd.DataFrame:
        """
        Evaluate desirability over a grid for contour plotting.
        
        Args:
            factor_grids: Dict mapping factor name -> 1D array of values
            
        Returns:
            DataFrame with factor columns + D + individual d_i
        """
        from itertools import product
        
        factor_names = list(factor_grids.keys())
        grid_values = list(factor_grids.values())
        
        results = []
        for point in product(*grid_values):
            x = np.array(point)
            
            d_values = []
            for cqa_name, spec in zip(self.models.keys(), self.cqa_specs):
                y_pred = self.models[cqa_name](x)
                d = self.individual_desirability(y_pred, spec)
                d_values.append(d)
            
            weights = [spec.get('weight', 1.0) for spec in self.cqa_specs]
            D = self.overall_desirability(d_values, weights)
            
            row = dict(zip(factor_names, point))
            row['D'] = D
            for i, cqa in enumerate(self.models.keys()):
                row[f'd_{cqa}'] = d_values[i]
            
            results.append(row)
        
        return pd.DataFrame(results)
