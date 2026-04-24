"""
Residual diagnostics for model validation.
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any

class DiagnosticsAnalyzer:
    """Comprehensive residual diagnostics."""
    
    def __init__(self, y_actual: np.ndarray, y_pred: np.ndarray, 
                 residuals: np.ndarray, X_matrix: pd.DataFrame):
        self.y = y_actual
        self.y_pred = y_pred
        self.residuals = residuals
        self.X = X_matrix
        self.n = len(y_actual)
        self.p = X_matrix.shape[1]
        
    def run_all(self) -> Dict[str, Any]:
        """Run complete diagnostic suite."""
        return {
            'normality': self._normality_tests(),
            'heteroscedasticity': self._heteroscedasticity_test(),
            'autocorrelation': self._durbin_watson(),
            'influential_points': self._influential_points(),
            'residual_stats': self._residual_stats(),
            'box_cox': self._box_cox_recommendation(),
        }
    
    def _normality_tests(self) -> Dict:
        """Shapiro-Wilk and Anderson-Darling tests."""
        # Shapiro-Wilk
        if self.n <= 5000:
            shapiro_stat, shapiro_p = stats.shapiro(self.residuals)
        else:
            shapiro_stat, shapiro_p = None, None
        
        # Anderson-Darling
        ad_stat, ad_critical, ad_sig = stats.anderson(self.residuals, dist='norm')
        ad_5pct = ad_critical[2]  # 5% significance level
        
        return {
            'shapiro_wilk': {
                'statistic': shapiro_stat,
                'p_value': shapiro_p,
                'pass': shapiro_p > 0.05 if shapiro_p else None,
            },
            'anderson_darling': {
                'statistic': ad_stat,
                'critical_5pct': ad_5pct,
                'pass': ad_stat < ad_5pct,
            },
            'overall_normal': (shapiro_p > 0.05 if shapiro_p else True) and (ad_stat < ad_5pct)
        }
    
    def _heteroscedasticity_test(self) -> Dict:
        """Breusch-Pagan test for constant variance."""
        from statsmodels.stats.diagnostic import het_breuschpagan
        
        try:
            bp_stat, bp_pval, f_stat, f_pval = het_breuschpagan(
                self.residuals, self.X.drop('Intercept', axis=1)
            )
            return {
                'breusch_pagan_stat': bp_stat,
                'breusch_pagan_pvalue': bp_pval,
                'pass': bp_pval > 0.05,
            }
        except:
            return {
                'breusch_pagan_stat': None,
                'breusch_pagan_pvalue': None,
                'pass': None,
                'error': 'Could not compute Breusch-Pagan test'
            }
    
    def _durbin_watson(self) -> Dict:
        """Durbin-Watson test for autocorrelation."""
        from statsmodels.stats.stattools import durbin_watson
        
        dw = durbin_watson(self.residuals)
        
        # Interpretation
        if dw < 1.5:
            interpretation = 'Positive autocorrelation suspected'
        elif dw > 2.5:
            interpretation = 'Negative autocorrelation suspected'
        else:
            interpretation = 'No autocorrelation detected'
        
        return {
            'statistic': dw,
            'interpretation': interpretation,
            'pass': 1.5 <= dw <= 2.5,
        }
    
    def _influential_points(self) -> Dict:
        """Cook's distance, leverage, DFFITS."""
        # Hat matrix diagonal (leverage)
        H = self.X.values @ np.linalg.pinv(self.X.values.T @ self.X.values) @ self.X.values.T
        h_diag = np.diag(H)
        
        # Cook's distance
        mse = np.mean(self.residuals ** 2)
        cooks_d = (self.residuals ** 2 / (self.p * mse)) * (h_diag / (1 - h_diag))
        
        # DFFITS
        dffits = self.residuals / np.sqrt(mse) * np.sqrt(h_diag / (1 - h_diag))
        
        # Thresholds
        cook_threshold = 4 / self.n
        leverage_threshold = 2 * self.p / self.n
        dffits_threshold = 2 * np.sqrt(self.p / self.n)
        
        influential = []
        for i in range(self.n):
            if cooks_d[i] > cook_threshold or h_diag[i] > leverage_threshold or abs(dffits[i]) > dffits_threshold:
                influential.append({
                    'index': i,
                    'cooks_d': cooks_d[i],
                    'leverage': h_diag[i],
                    'dffits': dffits[i],
                    'reason': []
                })
                if cooks_d[i] > cook_threshold:
                    influential[-1]['reason'].append('high Cook\'s distance')
                if h_diag[i] > leverage_threshold:
                    influential[-1]['reason'].append('high leverage')
                if abs(dffits[i]) > dffits_threshold:
                    influential[-1]['reason'].append('high DFFITS')
        
        return {
            'cooks_d_threshold': cook_threshold,
            'leverage_threshold': leverage_threshold,
            'dffits_threshold': dffits_threshold,
            'n_influential': len(influential),
            'influential_points': influential,
        }
    
    def _residual_stats(self) -> Dict:
        """Basic residual statistics."""
        return {
            'mean': np.mean(self.residuals),
            'std': np.std(self.residuals, ddof=1),
            'min': np.min(self.residuals),
            'max': np.max(self.residuals),
            'median': np.median(self.residuals),
            'range': np.max(self.residuals) - np.min(self.residuals),
        }
    
    def _box_cox_recommendation(self) -> Dict:
        """Recommend Box-Cox transformation if residuals non-normal."""
        from scipy.stats import boxcox
        
        # Only if all positive
        if np.all(self.y > 0):
            try:
                _, lmbda = boxcox(self.y)
                
                if abs(lmbda - 1.0) < 0.1:
                    recommendation = 'No transformation needed (lambda ≈ 1.0)'
                elif abs(lmbda) < 0.1:
                    recommendation = 'Try log transformation (lambda ≈ 0)'
                elif lmbda < 0:
                    recommendation = f'Try reciprocal transformation (lambda = {lmbda:.3f})'
                else:
                    recommendation = f'Try power transformation y^{lmbda:.3f}'
                
                return {
                    'applicable': True,
                    'lambda': lmbda,
                    'recommendation': recommendation,
                }
            except:
                return {'applicable': False, 'error': 'Box-Cox failed'}
        else:
            return {
                'applicable': False,
                'reason': 'Response contains non-positive values; Box-Cox not applicable'
            }
