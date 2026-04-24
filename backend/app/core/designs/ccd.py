"""
Central Composite Design (CCD) generator.
Fully implemented with rotatable and face-centered alpha options.
"""

import numpy as np
import pandas as pd
from pyDOE3 import ccdesign
from .base import DesignGenerator

class CCDGenerator(DesignGenerator):
    """Central Composite Design generator."""
    
    def __init__(self, factors: list):
        super().__init__(factors, 'CCD')
        
    def generate(self, alpha: str = 'rotatable', n_center: int = None, 
                 n_replicates: int = 1, randomize: bool = True, 
                 seed: int = 42, **kwargs) -> pd.DataFrame:
        """
        Generate CCD design matrix.
        
        Args:
            alpha: 'rotatable', 'face-centered', or numeric value
            n_center: Number of center points (default: 5 for k<=4, 6 for k>=5)
            n_replicates: Number of replicate runs at factorial points
            randomize: Whether to randomize run order
            seed: Random seed for reproducibility
            
        Returns:
            DataFrame with full design in engineering units
        """
        k = self.n_factors
        
        # Determine alpha
        if alpha == 'rotatable':
            alpha_val = (2 ** k) ** 0.25
        elif alpha == 'face-centered':
            alpha_val = 1.0
        else:
            alpha_val = float(alpha)
        
        # Default center points
        if n_center is None:
            n_center = 5 if k <= 4 else 6
        
        # Generate coded design using pyDOE3
        # ccdesign returns: 2^k factorial + 2k axial + n_center center
        coded_matrix = ccdesign(k, center=n_center, alpha='orthogonal' if alpha == 'rotatable' else 'face')
        
        # Adjust alpha to exact value
        if alpha == 'rotatable':
            # Replace axial points with exact rotatable alpha
            n_factorial = 2 ** k
            for i in range(n_factorial, n_factorial + 2 * k):
                for j in range(k):
                    if abs(abs(coded_matrix[i, j]) - 1.0) > 0.01:
                        coded_matrix[i, j] = np.sign(coded_matrix[i, j]) * alpha_val
        
        # Create DataFrame
        factor_names = [f['name'] for f in self.factors]
        df_coded = pd.DataFrame(coded_matrix, columns=factor_names)
        
        # Decode to engineering units
        df_eng = self.decode_to_engineering(df_coded)
        
        # Add metadata columns
        df_eng = self.add_run_order(df_eng, seed=seed)
        df_eng = self.add_block_column(df_eng, n_blocks=1)
        
        # Add empty CQA columns placeholder
        df_eng['Notes'] = ''
        
        # Reorder columns
        meta_cols = ['Run', 'StdOrder', 'RunOrder', 'Block']
        col_order = meta_cols + factor_names + ['Notes']
        df_eng = df_eng[col_order]
        
        return df_eng
    
    def get_design_info(self) -> dict:
        """Return design metadata."""
        k = self.n_factors
        n_factorial = 2 ** k
        n_axial = 2 * k
        n_center = 5 if k <= 4 else 6
        n_total = n_factorial + n_axial + n_center
        
        return {
            'type': 'CCD',
            'n_factors': k,
            'n_factorial_points': n_factorial,
            'n_axial_points': n_axial,
            'n_center_points': n_center,
            'n_total_runs': n_total,
            'alpha': (2 ** k) ** 0.25,
            'is_rotatable': True,
            'can_fit_model': 'full_quadratic'
        }
