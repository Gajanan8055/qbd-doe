"""
Base class for all DOE design generators.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple
import pandas as pd
import numpy as np

class DesignGenerator(ABC):
    """Abstract base class for design of experiments generators."""
    
    def __init__(self, factors: List[Dict], design_type: str):
        """
        Args:
            factors: List of factor dicts with keys: name, unit, low, center, high, type
            design_type: String identifier for the design type
        """
        self.factors = factors
        self.design_type = design_type
        self.n_factors = len(factors)
        
    @abstractmethod
    def generate(self, **kwargs) -> pd.DataFrame:
        """
        Generate the design matrix.
        
        Returns:
            DataFrame with columns: Run, StdOrder, RunOrder, Block, [factor columns in eng units], [empty CQA columns]
        """
        pass
    
    def encode_to_coded(self, df_eng: pd.DataFrame) -> pd.DataFrame:
        """Convert engineering units to coded -1/+1 scale."""
        df_coded = df_eng.copy()
        for factor in self.factors:
            name = factor['name']
            low = factor['low']
            high = factor['high']
            center = factor.get('center', (low + high) / 2)
            # Map [low, high] to [-1, +1]
            df_coded[name] = (df_eng[name] - center) / ((high - low) / 2)
        return df_coded
    
    def decode_to_engineering(self, df_coded: pd.DataFrame) -> pd.DataFrame:
        """Convert coded -1/+1 scale to engineering units."""
        df_eng = df_coded.copy()
        for factor in self.factors:
            name = factor['name']
            low = factor['low']
            high = factor['high']
            center = factor.get('center', (low + high) / 2)
            # Map [-1, +1] to [low, high]
            df_eng[name] = center + df_coded[name] * ((high - low) / 2)
        return df_eng
    
    def add_run_order(self, df: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
        """Add randomized RunOrder column."""
        np.random.seed(seed)
        n = len(df)
        df['Run'] = range(1, n + 1)
        df['StdOrder'] = range(1, n + 1)
        df['RunOrder'] = np.random.permutation(n) + 1
        return df
    
    def add_block_column(self, df: pd.DataFrame, n_blocks: int = 1) -> pd.DataFrame:
        """Add Block column."""
        n = len(df)
        block_size = n // n_blocks
        df['Block'] = [min(i // block_size + 1, n_blocks) for i in range(n)]
        return df
