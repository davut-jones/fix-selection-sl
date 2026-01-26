# Service Checker Call Label Modelling

## First time setup

### 0 - clone repo
git clone ...

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