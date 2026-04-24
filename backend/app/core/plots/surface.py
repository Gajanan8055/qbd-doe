"""
Plotly figure generators for all QbD-DOE plots.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Callable

class PlotGenerator:
    """Generate Plotly figures for all analysis plots."""
    
    @staticmethod
    def response_surface(model: Callable, factor_names: List[str], 
                        fixed_factors: Dict[str, float], 
                        x_range: tuple = (-1.5, 1.5),
                        n_grid: int = 50,
                        title: str = "Response Surface") -> Dict:
        """Generate 3D response surface plot."""
        # Create grid for first two factors
        x1 = np.linspace(x_range[0], x_range[1], n_grid)
        x2 = np.linspace(x_range[0], x_range[1], n_grid)
        X1, X2 = np.meshgrid(x1, x2)
        
        # Build full factor vector
        n_factors = len(factor_names)
        Z = np.zeros_like(X1)
        
        for i in range(n_grid):
            for j in range(n_grid):
                x = np.zeros(n_factors)
                x[0] = X1[i, j]
                x[1] = X2[i, j]
                # Fill in fixed factors
                for idx, (name, val) in enumerate(fixed_factors.items()):
                    if name in factor_names:
                        x[factor_names.index(name)] = val
                Z[i, j] = model(x)
        
        fig = go.Figure(data=[go.Surface(x=X1, y=X2, z=Z, colorscale='RdYlBu')])
        fig.update_layout(
            title=title,
            scene=dict(
                xaxis_title=factor_names[0],
                yaxis_title=factor_names[1],
                zaxis_title='Response',
            ),
            width=800,
            height=600,
        )
        return fig.to_dict()
    
    @staticmethod
    def contour_plot(model: Callable, factor_names: List[str],
                     fixed_factors: Dict[str, float],
                     x_range: tuple = (-1.5, 1.5),
                     n_grid: int = 50,
                     title: str = "Contour Plot") -> Dict:
        """Generate 2D contour plot."""
        x1 = np.linspace(x_range[0], x_range[1], n_grid)
        x2 = np.linspace(x_range[0], x_range[1], n_grid)
        X1, X2 = np.meshgrid(x1, x2)
        
        n_factors = len(factor_names)
        Z = np.zeros_like(X1)
        
        for i in range(n_grid):
            for j in range(n_grid):
                x = np.zeros(n_factors)
                x[0] = X1[i, j]
                x[1] = X2[i, j]
                for name, val in fixed_factors.items():
                    if name in factor_names:
                        x[factor_names.index(name)] = val
                Z[i, j] = model(x)
        
        fig = go.Figure(data=[
            go.Contour(
                x=x1, y=x2, z=Z,
                colorscale='RdYlBu',
                contours=dict(showlabels=True),
                colorbar=dict(title='Response'),
            )
        ])
        fig.update_layout(
            title=title,
            xaxis_title=factor_names[0],
            yaxis_title=factor_names[1],
            width=700,
            height=600,
        )
        return fig.to_dict()
    
    @staticmethod
    def predicted_vs_actual(y_actual: np.ndarray, y_pred: np.ndarray, 
                           r2: float, title: str = "Predicted vs Actual") -> Dict:
        """Predicted vs Actual plot."""
        fig = go.Figure()
        
        # Scatter points
        fig.add_trace(go.Scatter(
            x=y_actual, y=y_pred,
            mode='markers',
            marker=dict(size=10, color='blue', opacity=0.6),
            name='Data points',
        ))
        
        # 45-degree line
        min_val = min(y_actual.min(), y_pred.min())
        max_val = max(y_actual.max(), y_pred.max())
        fig.add_trace(go.Scatter(
            x=[min_val, max_val], y=[min_val, max_val],
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='Perfect fit (y=x)',
        ))
        
        fig.update_layout(
            title=f"{title}<br><sup>R² = {r2:.4f}</sup>",
            xaxis_title='Actual',
            yaxis_title='Predicted',
            width=600,
            height=500,
        )
        return fig.to_dict()
    
    @staticmethod
    def residuals_vs_predicted(y_pred: np.ndarray, residuals: np.ndarray,
                               title: str = "Residuals vs Predicted") -> Dict:
        """Residuals vs Predicted plot."""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=y_pred, y=residuals,
            mode='markers',
            marker=dict(size=10, color='blue', opacity=0.6),
        ))
        
        # Zero line
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        
        # ±2 sigma bands
        sigma = np.std(residuals)
        fig.add_hline(y=2*sigma, line_dash="dot", line_color="gray")
        fig.add_hline(y=-2*sigma, line_dash="dot", line_color="gray")
        
        fig.update_layout(
            title=title,
            xaxis_title='Predicted',
            yaxis_title='Residuals',
            width=600,
            height=500,
        )
        return fig.to_dict()
    
    @staticmethod
    def normal_qq(residuals: np.ndarray, title: str = "Normal Q-Q Plot") -> Dict:
        """Normal Q-Q plot."""
        from scipy import stats
        
        sorted_resid = np.sort(residuals)
        n = len(residuals)
        theoretical = stats.norm.ppf((np.arange(1, n+1) - 0.5) / n)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=theoretical, y=sorted_resid,
            mode='markers',
            marker=dict(size=10, color='blue', opacity=0.6),
            name='Residuals',
        ))
        
        # Reference line
        z = np.polyfit(theoretical, sorted_resid, 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=theoretical, y=p(theoretical),
            mode='lines',
            line=dict(color='red', dash='dash'),
            name='Reference line',
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title='Theoretical Quantiles',
            yaxis_title='Sample Quantiles',
            width=600,
            height=500,
        )
        return fig.to_dict()
    
    @staticmethod
    def pareto_chart(coefficients: pd.DataFrame, title: str = "Pareto Chart") -> Dict:
        """Pareto chart of |t-statistic|."""
        # Sort by |t|
        coef_sorted = coefficients.copy()
        coef_sorted['abs_t'] = coef_sorted['t_value'].abs()
        coef_sorted = coef_sorted.sort_values('abs_t', ascending=True)
        
        fig = go.Figure()
        
        # Bars
        colors = ['green' if p < 0.05 else 'gray' 
                  for p in coef_sorted['p_value']]
        
        fig.add_trace(go.Bar(
            x=coef_sorted['abs_t'],
            y=coef_sorted['Term'],
            orientation='h',
            marker_color=colors,
        ))
        
        # Reference line at t = 2 (approx 95% CI)
        fig.add_vline(x=2, line_dash="dash", line_color="red",
                      annotation_text="t = 2 (approx α=0.05)")
        
        fig.update_layout(
            title=title,
            xaxis_title='|t-statistic|',
            yaxis_title='Term',
            width=700,
            height=500,
        )
        return fig.to_dict()
    
    @staticmethod
    def desirability_contour(eval_df: pd.DataFrame, factor_names: List[str],
                             title: str = "Desirability Contour") -> Dict:
        """Desirability contour plot."""
        fig = go.Figure(data=[
            go.Contour(
                x=eval_df[factor_names[0]],
                y=eval_df[factor_names[1]],
                z=eval_df['D'],
                colorscale='RdYlGn',
                contours=dict(showlabels=True),
                colorbar=dict(title='Desirability D'),
            )
        ])
        
        fig.update_layout(
            title=title,
            xaxis_title=factor_names[0],
            yaxis_title=factor_names[1],
            width=700,
            height=600,
        )
        return fig.to_dict()
    
    @staticmethod
    def monte_carlo_histogram(samples: np.ndarray, spec_lower: float,
                                spec_upper: float, cqa_name: str) -> Dict:
        """Histogram of Monte Carlo samples with spec lines."""
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=samples,
            nbinsx=50,
            opacity=0.7,
            name=f'{cqa_name} distribution',
        ))
        
        # Spec lines
        if spec_lower is not None:
            fig.add_vline(x=spec_lower, line_color="red", line_dash="dash",
                          annotation_text="LSL")
        if spec_upper is not None:
            fig.add_vline(x=spec_upper, line_color="red", line_dash="dash",
                          annotation_text="USL")
        
        fig.update_layout(
            title=f"Monte Carlo: {cqa_name}",
            xaxis_title=cqa_name,
            yaxis_title='Frequency',
            width=600,
            height=400,
        )
        return fig.to_dict()
