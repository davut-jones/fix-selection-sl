# Service Checker Call Label Modelling

A Streamlit analytics dashboard for exploring LLM-derived call issue labels and customer outcomes from 50k+ Service Checker Hub 4 calls.

## Dashboard Views

- **Background** - Project context and business rationale
- **Overview** - High-level KPI summaries by label and outcome
- **Label Evaluation** - Deep-dive into label quality metrics
- **Outcome Analysis** - KPI comparison across outcomes with weighted scoring
- **Raw Label Data** - Filtered raw data inspection and export

## First time setup

### 0 - clone repo
```bash
git clone https://github.com/[your-username]/fix-selection-sl.git
cd fix-selection-sl
```

### 1 - activate venv
python3 -m venv venv 
source venv/bin/activate

### 2 - install packages
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

### 3 - start streamlit
python3 -m streamlit run app.py

## Regular use
source venv/bin/activate
python3 -m streamlit run app.py

## Pip freeze with minimal packages
python3 -m pip install pipreqs
pipreqs . --force

## Access

### Step 1 — Ask the user to do this once

1. Go to streamlit.io/cloud
2. Click Sign in
3. Sign in using the same email you plan to grant access to

They don’t need to deploy anything.

### Step 2 — Add that exact email

In your app settings:

- Add the same email
- Save

### Step 3 — Have them open the app link

You should now be prompted to log in and then see the app.