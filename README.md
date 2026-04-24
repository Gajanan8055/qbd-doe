# QbD-DOE Application

Production-grade Quality by Design – Design of Experiments web application for pharmaceutical process development.

## Quick Start

```bash
# 1. Clone and setup
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 2. Start with Docker
docker-compose up

# 3. Open browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/docs
```

## Architecture

```
qbd-doe/
├── backend/           FastAPI + Python scientific stack
│   ├── app/
│   │   ├── api/       REST endpoints
│   │   ├── core/      Business logic
│   │   │   ├── designs/      DOE design generators
│   │   │   ├── analysis/     Regression, ANOVA, diagnostics
│   │   │   ├── optimization/ Desirability, Monte Carlo
│   │   │   ├── plots/        Plotly figure generators
│   │   │   └── llm/          Anthropic Claude integration
│   │   ├── models/    SQLAlchemy models
│   │   ├── schemas/     Pydantic v2 schemas
│   │   └── reports/     Word document generation
│   └── tests/         pytest suite
└── frontend/          React 18 + Vite + TypeScript
    └── src/
        ├── pages/       Route components
        ├── components/  Reusable UI
        ├── lib/         API client
        └── store/       Zustand state
```

## Demo

Click "Load Demo" on the landing page to explore a pre-loaded Suzuki coupling project with full CCD design, analysis, and report generation.

## Implemented Features

### Module 1: LLM-Powered Suggestion
- Two-stage Claude-sonnet-4-5 pipeline
- CQA/CPP extraction with confidence scores
- Safety flags for hazardous chemistry
- Mandatory chemist review gates

### Module 2: Design Generation
- **CCD** (fully implemented): rotatable/face-centered alpha, center points, randomization
- Factorial, Fractional Factorial, DSD, BBD, D-optimal, Plackett-Burman (stubbed)
- Engineering unit encoding/decoding
- CSV export with Run/StdOrder/RunOrder/Block columns

### Module 3: Upload & Validation
- Schema validation against template
- Missing value detection
- Out-of-range flagging
- Duplicate run detection

### Module 4: Statistical Analysis
- OLS regression with full quadratic model
- ANOVA Type I & Type III SS
- Stepwise backward elimination (preserving hierarchy)
- Residual diagnostics (Shapiro-Wilk, Breusch-Pagan, Durbin-Watson, Cook's distance)
- Box-Cox transformation recommendation
- Model adequacy verdict (PASS/WARN/FAIL)

### Module 5: Visualization
- 3D response surface plots
- 2D contour plots with design points
- Interaction plots, main effects, Pareto charts
- Residual diagnostics plots
- Desirability contours
- Sweet-spot overlay plots
- Interactive prediction profiler

### Module 6: Optimization
- Derringer-Suich desirability (maximize/minimize/target)
- scipy.optimize.differential_evolution + L-BFGS-B polish
- Monte Carlo design space simulation (10,000 samples)
- P(meeting all specs) calculation

### Module 7: Word Report
- 11-section professional report
- 300 DPI matplotlib figures
- Post-processed through LibreOffice for MS Word compatibility
- Editable author field, confidential footer

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

### Known-Answer References
- `test_ccd.py`: Montgomery Example 11-2 (chemical process CCD)
- `test_factorial.py`: Montgomery Example 6-2 (2³ factorial)
- `test_desirability.py`: Derringer & Suich 1980 Example 1

## Extension Guide

### Adding a New Design Type
1. Create file in `backend/app/core/designs/`
2. Inherit from `DesignGenerator` base class in `base.py`
3. Implement `generate()` → returns DesignMatrix
4. Add endpoint in `backend/app/api/designs.py`
5. Add UI option in `frontend/src/pages/DesignView.tsx`

### Adding a New Plot Type
1. Create generator in `backend/app/core/plots/`
2. Accept AnalysisResult → returns Plotly JSON
3. Add endpoint in `backend/app/api/plots.py`
4. Add tab/panel in `frontend/src/pages/Analysis.tsx`

## Known Limitations

- Mixture designs: stubbed (requires simplex-lattice/simplex-centroid)
- Split-plot designs: stubbed (requires random-effect modeling)
- PLS regression: stubbed (for highly collinear spectral data)
- 21 CFR Part 11 compliance: partial (audit trail present, electronic signatures not implemented)
- Multi-user authentication: single-user mode only

## Statistical Validation References

- Montgomery, D.C. (2017). *Design and Analysis of Experiments*, 9th ed. Wiley.
- Derringer, G. & Suich, R. (1980). Simultaneous optimization of several response variables. *Journal of Quality Technology*, 12(4), 214-219.
- Box, G.E.P. & Draper, N.R. (2007). *Response Surfaces, Mixtures, and Ridge Analyses*, 2nd ed. Wiley.
- ICH Q8(R2), Q9, Q10, Q12 Guidelines.

## License

Proprietary — Internal R&D Use Only
