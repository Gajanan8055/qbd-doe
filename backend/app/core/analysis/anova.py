"""
ANOVA decomposition for RSM models.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import Dict, List

class ANOVAAnalyzer:
    """ANOVA with Type I (sequential) and Type III (partial) SS."""
    
    def __init__(self, df: pd.DataFrame, factor_names: List[str], 
                 response_name: str):
        self.df = df
        self.factors = factor_names
        self.response = response_name
        
    def run_anova(self, model_type: str = 'quadratic') -> Dict:
        """Run full ANOVA analysis."""
        # Build model matrix
        y = self.df[self.response]
        X = pd.DataFrame({'Intercept': np.ones(len(self.df))})
        
        # Main effects
        for f in self.factors:
            X[f] = self.df[f]
        
        # Interactions
        for i, fi in enumerate(self.factors):
            for fj in self.factors[i+1:]:
                X[f'{fi}:{fj}'] = self.df[fi] * self.df[fj]
        
        # Quadratic
        if model_type == 'quadratic':
            for f in self.factors:
                X[f'{f}^2'] = self.df[f] ** 2
        
        # Fit full model
        model = sm.OLS(y, X)
        results = model.fit()
        
        # ANOVA table (Type I - sequential)
        anova_type1 = sm.stats.anova_lm(results, typ=1)
        
        # ANOVA table (Type III - partial)
        anova_type3 = sm.stats.anova_lm(results, typ=3)
        
        # Lack-of-fit test (requires replicates)
        lof_result = self._lack_of_fit_test(y, X, results)
        
        return {
            'type1_ss': anova_type1.reset_index().to_dict('records'),
            'type3_ss': anova_type3.reset_index().to_dict('records'),
            'lack_of_fit': lof_result,
            'total_ss': ((y - y.mean()) ** 2).sum(),
            'model_ss': ((results.fittedvalues - y.mean()) ** 2).sum(),
            'residual_ss': (results.resid ** 2).sum(),
        }
    
    def _lack_of_fit_test(self, y, X, results) -> Dict:
        """Lack-of-fit F-test."""
        # Check for replicates
        unique_runs = X.drop_duplicates()
        n_unique = len(unique_runs)
        n_total = len(X)
        
        if n_unique == n_total:
            return {
                'testable': False,
                'reason': 'No replicate runs available for lack-of-fit test'
            }
        
        # Pure error SS
        pure_error_ss = 0
        pure_error_df = 0
        
        for _, run in unique_runs.iterrows():
            mask = (X == run.values).all(axis=1)
            y_at_run = y[mask]
            if len(y_at_run) > 1:
                mean_at_run = y_at_run.mean()
                pure_error_ss += ((y_at_run - mean_at_run) ** 2).sum()
                pure_error_df += len(y_at_run) - 1
        
        if pure_error_df == 0:
            return {
                'testable': False,
                'reason': 'No pure error degrees of freedom'
            }
        
        # Lack-of-fit SS
        lof_ss = (results.resid ** 2).sum() - pure_error_ss
        lof_df = n_total - n_unique - (len(X.columns) - 1)
        
        if lof_df <= 0:
            return {
                'testable': False,
                'reason': 'Insufficient degrees of freedom for lack-of-fit test'
            }
        
        # F-test
        pure_error_ms = pure_error_ss / pure_error_df
        lof_ms = lof_ss / lof_df
        f_value = lof_ms / pure_error_ms
        
        from scipy.stats import f
        p_value = 1 - f.cdf(f_value, lof_df, pure_error_df)
        
        return {
            'testable': True,
            'lof_ss': lof_ss,
            'lof_df': lof_df,
            'lof_ms': lof_ms,
            'pure_error_ss': pure_error_ss,
            'pure_error_df': pure_error_df,
            'pure_error_ms': pure_error_ms,
            'f_value': f_value,
            'p_value': p_value,
            'verdict': 'PASS' if p_value > 0.05 else 'FAIL'
        }
