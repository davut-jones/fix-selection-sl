# Copilot Instructions: Service Checker Call Label Modelling Dashboard

## Project Overview

**Streamlit analytics dashboard** analyzing 50k+ Service Checker Hub 4 calls (Aug-Nov) with LLM-derived Wi-Fi issue labels. Purpose: assess label quality and compare outcome performance across repeat calls, churn, and costs.

**Note:** Comparisons are descriptive, not causal—they show historical performance patterns for similar calls.

## Data Model & Schema

### Key Columns
- **Label & Evidence:** `label` (Wi-Fi issue type), `other_label`, `long_reason`, `evidence`, `confidence` (model confidence score)
- **Outcomes:** `selected_outcome_cleaned` (e.g., "Self-service fix", "Engineer visit", "Escalation"), `outcome_cost` (must coerce to numeric), `outcome_ts`
- **Engineer Data:** `engineer_reported_symptom`, `engineer_reported_cause`, `engineer_reported_action` (BBTTE calls only)
- **KPIs:** `sc_call_next_7d_flag`, `bb_churn_next_30d`, `bb_churn_next_60d` (binary flags), `call_date` (string in CSV, converted to `.dt.date`)
- **Integration:** `csg_reason` (CSG system call reason)

### Critical Data Type Handling
- Load with explicit dtypes for nullable string columns: `dtype={"other_label": "string", "engineer_reported_cause": "string", ...}`
- Date columns: convert `call_date` to `.dt.date` (not datetime)—Streamlit's `date_input()` expects date objects
- Numeric KPIs: **always** coerce before calculations: `pd.to_numeric(df[col], errors="coerce")`
- Outcomes: use `.dropna()` when building filter options—some rows have null `selected_outcome_cleaned`

## Architecture & Code Organization

### Key Design Pattern: Single Entry Point + Stateless Views
- **`app.py`** (235 lines): 
  - Data loading & caching via `@st.cache_data`
  - Session state initialization (filter options, metadata) + reset detection
  - Global filter controls (sidebar: labels, outcomes, date range)
  - View routing with filter application logic—**Background receives unfiltered data; all others receive `df_filtered`**
  - Navigation via `streamlit-option-menu`

- **View modules** (`views/*.py`): Each is **stateless**, receives filtered DataFrame, returns `None` (renders via `st.` calls)
  ```python
  def render_view(df_filtered):  # Signature for all views
      st.write("...")
  ```
  - `background.py` - No filters applied; full context
  - `overview.py` - KPI cards + label summary table with outcomes breakdown
  - `label_evaluation.py` - Engineer reason distributions per label; BBTTE calls only
  - `outcome_analysis.py` - Outcome distribution charts by label + KPI comparison tables
  - `raw_data.py` - Text search, repeat/churn filters, CSV export

- **Utilities:**
  - `colours.py` - `build_global_color_scale(values)` returns Altair `category20` scale for consistent categorical coloring
  - `style.py` - Branding helpers (primary: `#5A67D8`)

### Data Flow & Filtering
1. Load CSV once (cached) with explicit `dtype` for nullable strings
2. Initialize session state with filter options from data + reset detection (detects new deployments)
3. Apply filters: `df_filtered = df_label[label filter & outcome filter & date range]` (except Background)
4. Pass to view; view renders filtered data

### Critical Session State Variables
```python
st.session_state.selected_labels      # List[str] - Active labels
st.session_state.selected_outcomes    # List[str] - Active outcomes
st.session_state.start_date / .end_date  # date - Filter period
st.session_state.df_label_total_rows  # int - Total rows
st.session_state.global_outcomes      # List[str] - Distinct outcomes
```

## Development Workflows

### Local Setup
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run app.py  # Runs on http://localhost:8501
```

### Adding a New View (Standard Pattern)
1. Create `views/my_view.py` with `def render_view(df_filtered):` function
2. Import in `app.py` line ~10 and add to navigation menu `option_menu` (line ~155)
3. Add conditional render logic (line ~220)
4. **Rule:** If view needs full context (like Background), call `render_view(df_label)` directly; otherwise receives `df_filtered`

### Modifying Filters
- Initialization: `app.py` lines ~115–135 (reset detection, label/outcome option extraction)
- UI widgets: `app.py` lines ~170–200 (multiselect controls)
- Application: `app.py` lines ~201–215 (filter conditions)
- To add new filter: Add to session state init → add UI widget → add to filter condition

### Data Column Changes
If CSV schema changes:
1. Update `dtype` dict in `load_label_data()` for new string columns
2. Update column lists in affected views (e.g., `raw_columns` in `raw_data.py`)
3. Update KPI calculations (coerce numeric types in views, not in `app.py`)
4. Deploy: filter reset detection auto-resets stale filters on new data

## Project-Specific Conventions

### Data Type Handling (Critical)
- **CSV Loading**: Explicitly specify string dtypes for nullable columns:
  ```python
  dtype={"other_label": "string", "engineer_reported_cause": "string", ...}
  ```
- **Date Conversion**: Convert to `.dt.date` (not datetime) for `st.date_input()` compatibility:
  ```python
  df["call_date"] = pd.to_datetime(df["call_date"]).dt.date
  ```
- **Numeric KPIs**: Always coerce in views before calculations:
  ```python
  numeric_cols = ["outcome_cost", "sc_call_next_7d_flag", "bb_churn_next_30d"]
  for col in numeric_cols:
      df[col] = pd.to_numeric(df[col], errors="coerce")
  ```
- **Nullable Outcomes**: Use `.dropna()` when extracting distinct values:
  ```python
  df_label["selected_outcome_cleaned"].dropna().unique()
  ```

### Filter Behavior
- **Background Exception**: Receives full `df_label` unfiltered; filters hidden in sidebar
- **Filter Persistence**: All filters persist in session state across view navigation
- **Reset Logic** (lines ~115–135, `app.py`):
  - Detects when filter options change (new deployment)
  - Compares current `selected_labels` against data's label options
  - Auto-resets stale filters to prevent "no data" errors

### KPI Metrics (Standard Across All Views)
- **Total Calls**: `len(df_filtered)`
- **Repeat Rate (7d)**: `df_filtered["sc_call_next_7d_flag"].mean()` → displayed as %
- **Churn Rate (30d/60d)**: `df_filtered["bb_churn_next_30d"].mean()` → displayed as %
- **Avg Outcome Cost**: `df_filtered["outcome_cost"].mean()` → formatted as £
- **Total Outcome Cost**: `df_filtered["outcome_cost"].sum()` → formatted as £

### Visualization & Styling
- **Color Consistency**: All categorical charts use `build_global_color_scale()` from `colours.py`
- **Branding**: Primary color `#5A67D8` (indigo); use in headers for custom styling
- **Metric Cards**: `background-color` divs with `padding: 20px`, `border-radius: 12px`, `color: #FAF9F6` (see `overview.py` template)
- **Info Boxes**: Use `st.info()` for filtering assumptions and data caveats

## Dependencies & Requirements

**Core Dependencies** (from `requirements.txt`):
```
altair==6.0.0          # Interactive charting
pandas==2.2.0          # Data manipulation
streamlit==1.53.1      # Web app framework
streamlit_option_menu==0.4.0  # Sidebar navigation menu
streamlit_tags==1.2.8  # Tag input widget
```

- **No test framework** configured—this is an exploratory analytics tool
- **No external APIs** required—all data sourced from CSV in `data/` folder

## Key Files & Their Roles

| File | Purpose |
|------|---------|
| `app.py` | Entry point, navigation, filter logic, data loading, session state |
| `views/background.py` | Project overview, business context |
| `views/overview.py` | KPI cards, label summary table |
| `views/label_evaluation.py` | Engineer reason distributions (BBTTE calls only) |
| `views/outcome_analysis.py` | Outcome distribution charts, KPI comparison |
| `views/raw_data.py` | Raw data inspection, text search, CSV export |
| `utils/colours.py` | Altair color scale builder for consistency |
| `utils/style.py` | Custom Streamlit styling helpers |
| `requirements.txt` | Frozen dependency versions |

## Deployment & Access Control

- **Production Hosting**: Streamlit Cloud (recommended)
- **Authentication State**: Currently **disabled** (`AUTH_ENABLED = False` in `app.py` line ~90)
  - To enable: Set `AUTH_ENABLED = True` and add `app_password` secret to Streamlit Cloud secrets
  - Password check logic: Lines ~70–86 in `app.py`
  - Security note: Password stored in Streamlit secrets (not hardcoded)

- **Email-based Access**: Via Streamlit Cloud app settings (requires user to sign in with streamlit.io account first)

## Testing, Debugging & Best Practices

### Debugging Patterns
- **Inspect Session State**: Add `st.json(st.session_state)` to see all filter values
- **Check Filter Application**: Print `len(df_filtered)` in views to verify filtering
- **Validate Data**: Use Raw Data view to inspect rows behind visualizations

### Known Data Issues & Mitigations
- **Missing Engineer Notes**: Only ~10–20% of calls have `engineer_reported_*` columns (BBTTE visits only)
  - Filter to non-null in Label Evaluation view; display row count
- **Numeric Type Coercion**: CSV `outcome_cost` loads as string
  - Use `pd.to_numeric(..., errors="coerce")` before calculations
- **Outcome Nulls**: Some rows missing `selected_outcome_cleaned`
  - Use `.dropna()` when building filter options

### Best Practices
1. **Always use `@st.cache_data`** for data loading and expensive operations
2. **Pass filtered data to views**, not unfiltered—views consume pre-filtered data
3. **Preserve session state** in `st.session_state`, not local variables
4. **Coerce numeric types early** with `pd.to_numeric()` in views before calculations
5. **Use `.dropna()`** when extracting distinct values for filter options
6. **Color consistency**: Always use `build_global_color_scale()` for categorical charts
7. **Document assumptions** using `st.info()` boxes for data filters
8. **Monitor CSV schema**: Update `dtype` dict and affected views when columns change
9. **Understand Streamlit reruns**: Every interaction causes full script re-run—use session state for persistence


