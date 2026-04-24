"""
OLS regression with full quadratic model for RSM.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm
from typing import Dict, List, Tuple, Any

class RegressionAnalyzer:
    """Fit and analyze quadratic response surface models."""
    
    def __init__(self, df: pd.DataFrame, factor_names: List[str], 
                 response_name: str, coded: bool = True):
        """
        Args:
            df: DataFrame with design + results
            factor_names: List of factor column names
            response_name: CQA column name
            coded: Whether factors are in coded (-1/+1) units
        """
        self.df = df.copy()
        self.factors = factor_names
        self.response = response_name
        self.coded = coded
        self.model = None
        self.results = None
        self.reduced_model = None
        self.reduced_results = None
        
    def build_model_matrix(self, df: pd.DataFrame, quadratic: bool = True, 
                           interactions: bool = True) -> pd.DataFrame:
        """Build full quadratic model matrix: X = [1, x_i, x_i*x_j, x_i^2]."""
        X = pd.DataFrame(index=df.index)
        X['Intercept'] = 1.0
        
        # Main effects
        for f in self.factors:
            X[f] = df[f]
        
        # Two-factor interactions
        if interactions:
            for i, fi in enumerate(self.factors):
                for fj in self.factors[i+1:]:
                    X[f'{fi}:{fj}'] = df[fi] * df[fj]
        
        # Quadratic terms
        if quadratic:
            for f in self.factors:
                X[f'{f}^2'] = df[f] ** 2
        
        return X
    
    def fit(self, quadratic: bool = True, interactions: bool = True) -> Dict[str, Any]:
        """Fit OLS model. Returns full statistics dictionary."""
        y = self.df[self.response]
        X = self.build_model_matrix(self.df, quadratic, interactions)
        
        self.model = sm.OLS(y, X)
        self.results = self.model.fit()
        
        return self._compile_results(self.results, X)
    
    def stepwise_reduce(self, alpha: float = 0.05) -> Dict[str, Any]:
        """Backward elimination preserving model hierarchy."""
        if self.results is None:
            self.fit()
        
        X = self.build_model_matrix(self.df)
        y = self.df[self.response]
        
        # Get current terms
        terms = list(X.columns)
        terms.remove('Intercept')
        
        # Iteratively remove highest p-value terms
        # But preserve hierarchy: don't drop main if interaction present
        changed = True
        while changed and len(terms) > 0:
            changed = False
            pvals = self.results.pvalues.drop('Intercept')
            
            # Find highest p-value
            max_p = pvals.max()
            if max_p > alpha:
                term_to_drop = pvals.idxmax()
                
                # Hierarchy check: don't drop main effect if its interaction/quadratic is present
                if '^2' not in term_to_drop and ':' not in term_to_drop:
                    # It's a main effect - check if interaction or quadratic exists
                    has_child = any(
                        term_to_drop in t and (':' in t or '^2' in t)
                        for t in terms
                    )
                    if has_child:
                        # Find next highest p-value
                        sorted_p = pvals.sort_values(ascending=False)
                        for candidate in sorted_p.index:
                            if ':' in candidate or '^2' in candidate:
                                term_to_drop = candidate
                                break
                        else:
                            continue
                
                # Drop term
                if term_to_drop in terms:
                    terms.remove(term_to_drop)
                    X_reduced = X[['Intercept'] + terms]
                    self.reduced_model = sm.OLS(y, X_reduced)
                    self.reduced_results = self.reduced_model.fit()
                    self.results = self.reduced_results
                    changed = True
        
        return self._compile_results(self.results, X[['Intercept'] + terms])
    
    def _compile_results(self, results, X) -> Dict[str, Any]:
        """Compile comprehensive regression results."""
        # Coefficient table
        coef_table = pd.DataFrame({
            'Term': results.params.index,
            'Estimate': results.params.values,
            'SE': results.bse.values,
            't_value': results.tvalues.values,
            'p_value': results.pvalues.values,
            'CI_lower': results.conf_int()[0].values,
            'CI_upper': results.conf_int()[1].values,
        })
        
        # VIF calculation
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        vif_data = []
        for i, col in enumerate(X.columns):
            if col != 'Intercept':
                try:
                    vif = variance_inflation_factor(X.values, i)
                except:
                    vif = np.inf
                vif_data.append({'Term': col, 'VIF': vif})
        vif_df = pd.DataFrame(vif_data)
        
        # Model metrics
        r2 = results.rsquared
        adj_r2 = results.rsquared_adj
        
        # Predicted R² (Q² via PRESS)
        press = self._calculate_press(results, X)
        q2 = 1 - press / ((self.df[self.response] - self.df[self.response].mean()) ** 2).sum()
        
        # CV%
        cv = results.resid.std() / self.df[self.response].mean() * 100
        
        return {
            'coefficients': coef_table.to_dict('records'),
            'vif': vif_df.to_dict('records'),
            'r2': r2,
            'adjusted_r2': adj_r2,
            'predicted_r2': q2,
            'cv_percent': cv,
            'mse': results.mse_resid,
            'rmse': np.sqrt(results.mse_resid),
            'f_statistic': results.fvalue,
            'f_pvalue': results.f_pvalue,
            'aic': results.aic,
            'bic': results.bic,
            'model_equation_coded': self._format_equation(results.params),
        }
    
    def _calculate_press(self, results, X) -> float:
        """Calculate PRESS statistic for Q²."""
        n = len(X)
        press = 0.0
        for i in range(n):
            X_loo = X.drop(index=X.index[i])
            y_loo = self.df[self.response].drop(index=self.df.index[i])
            model_loo = sm.OLS(y_loo, X_loo).fit()
            y_pred = model_loo.predict(X.iloc[i:i+1])
            press += (self.df[self.response].iloc[i] - y_pred.iloc[0]) ** 2
        return press
    
    def _format_equation(self, params: pd.Series) -> str:
        """Format model equation as string in coded units."""
        terms = []
        for term, coef in params.items():
            if abs(coef) > 1e-10:
                if term == 'Intercept':
                    terms.append(f"{coef:.4f}")
                else:
                    terms.append(f"{'+' if coef >= 0 else ''}{coef:.4f}*{term}")
        return 'y = ' + ' '.join(terms)
    
    def predict(self, X_new: pd.DataFrame, quadratic: bool = True, 
                interactions: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with 95% prediction interval."""
        if self.results is None:
            self.fit(quadratic, interactions)
        
        X_mat = self.build_model_matrix(X_new, quadratic, interactions)
        pred = self.results.get_prediction(X_mat)
        
        return pred.predicted_mean, pred.conf_int()
