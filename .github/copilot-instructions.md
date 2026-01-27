# Copilot Instructions: Service Checker Call Label Modelling Dashboard

## Project Overview

This is a **Streamlit data analytics dashboard** for exploring LLM-derived call issue labels and their associated customer outcomes. The dashboard analyzes 50k+ Service Checker Hub 4 calls to evaluate label quality and identify which outcomes to offer for each issue type.

## Architecture Patterns

### Multi-View Modular Structure
- **Single entry point**: `app.py` handles authentication, navigation, global filters, and data loading
- **View modules** (`views/`): Each view is a standalone module with a `render_view(df_filtered)` function:
  - `background.py` - Project context and business rationale (no filters)
  - `overview.py` - High-level KPI summaries by label/outcome
  - `label_evaluation.py` - Deep-dive into label quality metrics
  - `outcome_analysis.py` - KPI comparison across outcomes with weighted scoring
  - `raw_data.py` - Filtered raw data export
- **Utilities** (`utils/`): Visual helpers (`colours.py` for Altair scales, `style.py` for custom Streamlit styling)

### Data Flow
1. CSV loaded once with `@st.cache_data` decorator
2. Global filters (labels, outcomes, date range) stored in `st.session_state`
3. Filtered DataFrame passed to view module based on navigation selection
4. Views are stateless—they receive already-filtered data and render visualizations

### Critical Session State Variables
```python
st.session_state.selected_labels         # List of active call issue labels
st.session_state.selected_outcomes       # List of active outcomes
st.session_state.start_date / end_date   # Date range filter
st.session_state.authenticated           # Auth flag (currently disabled: AUTH_ENABLED = False)
st.session_state.df_label_total_rows     # Total row count for context
st.session_state.global_outcomes         # Distinct outcomes from source data
```

## Development Workflows

### Setup & Execution
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run app.py
```
Dashboard runs on `http://localhost:8501` by default.

### Adding New Views
1. Create `views/new_view_name.py` with `def render_view(df_filtered):` signature
2. Import the view in `app.py` alongside other view imports
3. Add to navigation menu options and icon list
4. Add conditional branch in view selection logic to call `render_new_view_name(df_filtered)`

### Dependency Management
- **Minimal required**: Streamlit, pandas, streamlit-option-menu (see `requirements.txt`)
- Data visualization uses Altair for Streamlit interop—check `outcome_analysis.py` for color scale patterns
- **No test framework configured**—this is a prototype/analytics tool, not production backend code

## Project-Specific Conventions

### Data Type Handling
- CSV loads `other_label` as string type to preserve nulls
- Date columns converted to `.dt.date` after loading (not datetime, for sidebar UI compatibility)
- Numeric KPI columns (`outcome_cost`, churn flags) must be coerced to numeric in views due to CSV data quality: `pd.to_numeric(df[col], errors="coerce")`

### Filter Behavior
- Filters applied **only on non-Background views** (Background shows full dataset for context)
- Filter state **persists across view navigation** (stored in session state)
- Filters have smart reset logic to detect data updates (deploy/refresh)—see filter initialization logic in `app.py`
- Sidebar only displays filter controls when not on Background view

### KPI Metrics & Calculations
Standard metrics exposed in views:
- **Repeat Call Rate (7d)**: `sc_call_next_7d_flag` summed / total calls
- **Churn Rate (30d/60d)**: `bb_churn_next_30d` / `bb_churn_next_60d` summed / total calls
- **Outcome Cost**: Mean of `outcome_cost` column
- Outcome Analysis uses **weighted KPI scoring** (user-configurable via sliders)—see `outcome_analysis.py` for weighting formula

### Visualization Patterns
- Altair charts use `build_global_color_scale(values)` from `utils/colours.py` for consistent categorical coloring
- Custom Streamlit styling via `utils/style.py` (primary color: `#5A67D8`)—use for custom headers when brand consistency needed
- Bootstrap icons integrated via CDN in page config for sidebar menu icons

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| [app.py](app.py) | App entry point, auth, navigation, filter logic, data loading, view routing |
| [views/background.py](views/background.py) | Project overview, business context, metrics grid (no filtering) |
| [views/overview.py](views/overview.py) | KPI summary cards and trends, label/outcome distributions |
| [views/label_evaluation.py](views/label_evaluation.py) | Validate label quality against ground truth or patterns |
| [views/outcome_analysis.py](views/outcome_analysis.py) | Weighted KPI scoring for outcomes, decision support |
| [views/raw_data.py](views/raw_data.py) | Filterable data export (CSV download) |
| [utils/colours.py](utils/colours.py) | Altair color scale builder for consistent charts |
| [utils/style.py](utils/style.py) | Custom Streamlit text styling |
| [requirements.txt](requirements.txt) | Core dependencies (streamlit, pandas, altair) |

## Deployment & Access Control

- **Production hosting**: Streamlit Cloud
- **Authentication**: Currently **disabled** (`AUTH_ENABLED = False`)—set to `True` and add `app_password` to Streamlit secrets to enable password-based access
- **Email-based access** via Streamlit Cloud app settings (requires user sign-in at streamlit.io first)

## Testing & Debugging Notes

- **No unit tests**—this is an exploratory analytics dashboard
- Debug filters by printing `st.session_state` in views or checking sidebar state
- For CSV data issues, inspect with raw_data view or re-run with fresh data in `data/` folder
- Watch for date parsing issues if CSV format changes—current logic expects `call_date` column as string-formatted dates
