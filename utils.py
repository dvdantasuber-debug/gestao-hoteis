import streamlit as st
import requests

@st.cache_data(ttl=86400)
def get_countries():
    try:
        url = "https://countriesnow.space/api/v0.1/countries/positions"
        r = requests.get(url, timeout=5)
        return sorted([c['name'] for c in r.json()['data']]) if r.status_code == 200 else ["Brazil"]
    except: return ["Brazil"]

def get_states(country):
    try:
        url = "https://countriesnow.space/api/v0.1/countries/states"
        r = requests.post(url, json={"country": country}, timeout=5)
        return sorted([s['name'] for s in r.json()['data']['states']]) if r.status_code == 200 else []
    except: return []

def get_cities(country, state):
    try:
        url = "https://countriesnow.space/api/v0.1/countries/state/cities"
        r = requests.post(url, json={"country": country, "state": state}, timeout=5)
        return sorted(r.json()['data']) if r.status_code == 200 else []
    except: return []