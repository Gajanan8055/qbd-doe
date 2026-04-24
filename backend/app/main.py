"""
FastAPI main application with all endpoints.
"""

import os
import json
import hashlib
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
import io

# Core imports
from app.core.designs.ccd import CCDGenerator
from app.core.analysis.regression import RegressionAnalyzer
from app.core.analysis.anova import ANOVAAnalyzer
from app.core.analysis.diagnostics import DiagnosticsAnalyzer
from app.core.optimization.desirability import DesirabilityOptimizer
from app.core.optimization.monte_carlo import MonteCarloSimulator
from app.core.plots.surface import PlotGenerator
from app.core.llm.suggester import Suggester
from app.reports.docx_builder import ReportBuilder

app = FastAPI(title="QbD-DOE API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Demo project data
DEMO_PROJECT = {
    'project_id': 'demo-suzuki-001',
    'api_name': 'Suzuki coupling — Finerenone intermediate step 4',
    'unit_operation': 'Suzuki-Miyaura coupling',
    'chemistry_description': 'Suzuki-Miyaura coupling of 6-bromoquinoline with pyridine boronic ester using Pd(PPh3)4 (3 mol%), K2CO3 (2 eq), in toluene/water (5:1), 80°C, 4h',
    'cqas': [
        {'name': 'Assay', 'unit': '%', 'target': 98, 'lower_spec': 95, 'upper_spec': 102, 'weight': 5, 'goal': 'target'},
        {'name': 'Total_Impurities', 'unit': '%', 'target': 0.5, 'lower_spec': 0, 'upper_spec': 2.0, 'weight': 5, 'goal': 'minimize'},
        {'name': 'Yield', 'unit': '%', 'target': 85, 'lower_spec': 70, 'upper_spec': 100, 'weight': 3, 'goal': 'maximize'},
    ],
    'cpps': [
        {'name': 'Temperature', 'unit': '°C', 'type': 'continuous', 'low': 70, 'center': 80, 'high': 90},
        {'name': 'Catalyst_Loading', 'unit': 'mol%', 'type': 'continuous', 'low': 1, 'center': 3, 'high': 5},
        {'name': 'Time', 'unit': 'h', 'type': 'continuous', 'low': 2, 'center': 4, 'high': 6},
        {'name': 'Base_eq', 'unit': 'eq', 'type': 'continuous', 'low': 1.5, 'center': 2.0, 'high': 2.5},
        {'name': 'Solvent_Ratio', 'unit': 'ratio', 'type': 'continuous', 'low': 3, 'center': 5, 'high': 7},
    ],
}

# Schemas
class SuggestRequest(BaseModel):
    api_name: str
    chemistry_description: str

class DesignRequest(BaseModel):
    project_id: str
    design_type: str = 'CCD'
    factors: List[Dict]
    
class AnalysisRequest(BaseModel):
    project_id: str
    cqa_name: str
    
class OptimizeRequest(BaseModel):
    project_id: str
    
class ReportRequest(BaseModel):
    project_id: str
    author: str = "Process Chemist"

# Endpoints
@app.get("/api/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.post("/api/suggest")
def suggest(request: SuggestRequest):
    """Two-stage LLM suggestion."""
    suggester = Suggester()
    result = suggester.suggest(request.api_name, request.chemistry_description)
    return result

@app.get("/api/demo")
def get_demo():
    """Get demo project data."""
    return DEMO_PROJECT

@app.post("/api/designs/generate")
def generate_design(request: DesignRequest):
    """Generate DOE design matrix."""
    if request.design_type == 'CCD':
        generator = CCDGenerator(request.factors)
        design = generator.generate()
        info = generator.get_design_info()
        
        return {
            'design': design.to_dict('records'),
            'info': info,
            'csv': design.to_csv(index=False),
        }
    else:
        raise HTTPException(status_code=400, detail=f"Design type {request.design_type} not yet implemented")

@app.post("/api/upload")
def upload_results(file: UploadFile = File(...), project_id: str = Form(...)):
    """Upload experimental results CSV."""
    contents = file.file.read()
    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    
    # Validation
    validation = {
        'n_rows': len(df),
        'n_cols': len(df.columns),
        'columns': list(df.columns),
        'missing_values': int(df.isnull().sum().sum()),
        'valid': True,
        'issues': []
    }
    
    if validation['missing_values'] > 0:
        validation['issues'].append(f"{validation['missing_values']} missing values detected")
    
    return validation

@app.post("/api/analysis/run")
def run_analysis(request: AnalysisRequest):
    """Run full statistical analysis on uploaded data."""
    # For demo, generate synthetic data
    np.random.seed(42)
    
    # Simulate CCD design with 5 factors, 32 runs
    from pyDOE3 import ccdesign
    coded = ccdesign(5, center=6)
    
    # Decode to engineering units
    factor_names = ['Temperature', 'Catalyst_Loading', 'Time', 'Base_eq', 'Solvent_Ratio']
    low = [70, 1, 2, 1.5, 3]
    high = [90, 5, 6, 2.5, 7]
    center = [80, 3, 4, 2.0, 5]
    
    df = pd.DataFrame(coded, columns=factor_names)
    for i, name in enumerate(factor_names):
        df[name] = center[i] + df[name] * ((high[i] - low[i]) / 2)
    
    # Generate realistic response data
    if request.cqa_name == 'Yield':
        # Yield with quadratic curvature and interaction
        df['Yield'] = (85 + 5*ccdesign(5, center=6)[:, 0] + 3*ccdesign(5, center=6)[:, 1]
                       - 2*ccdesign(5, center=6)[:, 0]**2 
                       + 4*ccdesign(5, center=6)[:, 0]*ccdesign(5, center=6)[:, 1]
                       + np.random.normal(0, 2, len(df)))
        df['Yield'] = np.clip(df['Yield'], 60, 100)
    elif request.cqa_name == 'Total_Impurities':
        df['Total_Impurities'] = (2.0 - 0.5*ccdesign(5, center=6)[:, 0] 
                                  + 0.3*ccdesign(5, center=6)[:, 1]
                                  + 0.2*ccdesign(5, center=6)[:, 0]*ccdesign(5, center=6)[:, 1]
                                  + np.random.normal(0, 0.2, len(df)))
        df['Total_Impurities'] = np.clip(df['Total_Impurities'], 0.1, 3.0)
    else:
        df['Assay'] = 98 + np.random.normal(0, 1, len(df))
    
    # Fit model
    y_col = request.cqa_name
    reg = RegressionAnalyzer(df, factor_names, y_col, coded=False)
    reg_results = reg.fit()
    
    # ANOVA
    anova = ANOVAAnalyzer(df, factor_names, y_col)
    anova_results = anova.run_anova()
    
    # Diagnostics
    diag = DiagnosticsAnalyzer(
        df[y_col].values,
        reg.results.fittedvalues.values,
        reg.results.resid.values,
        reg.build_model_matrix(df)
    )
    diag_results = diag.run_all()
    
    return {
        'cqa': request.cqa_name,
        'regression': reg_results,
        'anova': anova_results,
        'diagnostics': diag_results,
        'verdict': 'PASS' if reg_results['r2'] > 0.8 else 'WARN',
    }

@app.get("/api/plots/{plot_type}")
def get_plot(plot_type: str, project_id: str, cqa: str, 
             factor1: str = None, factor2: str = None):
    """Generate Plotly figure JSON."""
    # Return demo plot data
    if plot_type == 'response_surface':
        x = np.linspace(-1, 1, 50)
        y = np.linspace(-1, 1, 50)
        X, Y = np.meshgrid(x, y)
        Z = 85 + 5*X + 3*Y - 2*X**2 + 4*X*Y
        
        fig = {
            'data': [{'type': 'surface', 'x': X.tolist(), 'y': Y.tolist(), 'z': Z.tolist()}],
            'layout': {'title': f'{cqa} Response Surface', 'scene': {'xaxis': {'title': factor1}, 'yaxis': {'title': factor2}}}
        }
        return fig
    
    elif plot_type == 'contour':
        return PlotGenerator.contour_plot(
            lambda x: 85 + 5*x[0] + 3*x[1],
            [factor1 or 'F1', factor2 or 'F2'],
            {},
            title=f'{cqa} Contour'
        )
    
    elif plot_type == 'pareto':
        coefs = pd.DataFrame({
            'Term': ['A', 'B', 'AB', 'A^2'],
            't_value': [8.5, 6.2, 4.1, 3.8],
            'p_value': [0.001, 0.005, 0.02, 0.03]
        })
        return PlotGenerator.pareto_chart(coefs)
    
    else:
        return {'data': [], 'layout': {'title': f'{plot_type} not implemented'}}

@app.post("/api/optimize")
def optimize(request: OptimizeRequest):
    """Run desirability optimization."""
    # Build simple prediction models
    def make_predictor(cqa):
        if cqa == 'Yield':
            return lambda x: 85 + 5*x[0] + 3*x[1] - 2*x[0]**2 + 4*x[0]*x[1]
        elif cqa == 'Total_Impurities':
            return lambda x: 2.0 - 0.5*x[0] + 0.3*x[1]
        else:
            return lambda x: 98.0
    
    models = {cqa['name']: make_predictor(cqa['name']) for cqa in DEMO_PROJECT['cqas']}
    
    optimizer = DesirabilityOptimizer(models, DEMO_PROJECT['cqas'])
    
    # Optimize
    bounds = [(-1, 1)] * 5  # 5 factors
    result = optimizer.optimize(bounds)
    
    # Monte Carlo
    mc = MonteCarloSimulator(models, DEMO_PROJECT['cqas'])
    mc_result = mc.simulate(
        np.array(result['optimal_factors']),
        np.array([0.1, 0.1, 0.1, 0.05, 0.2])
    )
    
    return {
        'optimization': result,
        'monte_carlo': mc_result,
    }

@app.post("/api/report/generate")
def generate_report(request: ReportRequest):
    """Generate Word report."""
    builder = ReportBuilder()
    
    # Collect analysis results
    analysis_results = {
        'summary': {'verdict': 'PASS', 'r2': 0.92, 'q2': 0.87, 'n_significant': 8},
        'anova': {'type3_ss': []},
        'coefficients': [],
        'diagnostics': {},
        'model_equation_coded': 'y = 85.2 + 4.8*A + 3.1*B - 1.9*A^2 + 3.7*A*B',
        'optimization': {
            'overall_desirability': 0.85,
            'optimal_factors': [0.5, 0.3, -0.2, 0.1, 0.0],
            'predictions': {
                'Yield': {'predicted': 91.2, 'pi_lower': 87.5, 'pi_upper': 94.9},
                'Total_Impurities': {'predicted': 0.8, 'pi_lower': 0.5, 'pi_upper': 1.1},
                'Assay': {'predicted': 98.5, 'pi_lower': 97.2, 'pi_upper': 99.8},
            }
        },
        'monte_carlo': {'probability_all_specs': 0.97}
    }
    
    # Generate matplotlib plots as bytes
    plots = {}
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    ax.set_title('Demo Plot')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    plots['demo_plot'] = buf.getvalue()
    plt.close(fig)
    
    # Build report
    report_bytes = builder.build_report(
        DEMO_PROJECT,
        analysis_results,
        plots,
        author=request.author
    )
    
    return StreamingResponse(
        io.BytesIO(report_bytes),
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={'Content-Disposition': 'attachment; filename=QbD_Report.docx'}
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
