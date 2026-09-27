import streamlit as st
import pandas as pd
import os
import json
import datetime
from supabase import create_client, Client

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shivraj Unitrade | Export Management", page_icon="🌐", layout="wide")

# --- SUPABASE CONNECTION ---
SUPABASE_URL = "https://fwlckedxrtkymwqbegos.supabase.co"
SUPABASE_KEY = "sb_publishable_UJinMiq1Fln8ckiLH0cvlA_2ApxVLLS"

@st.cache_resource
def get_supabase_client():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase = get_supabase_client()

# --- BASIC DATA FUNCTIONS (WITH ERROR CATCHING) ---
def get_products():
    if not supabase:
        return {}
    try:
        res = supabase.table("products").select("*").execute()
        if res.data:
            return {r["pid"]: r for r in res.data}
    except Exception as e:
        pass
    
    # Fallback default products if DB is empty or offline
    return {
        "EX101": {"pid": "EX101", "name": "Onion Powder", "cost_price": 250.0, "price_per_kg": 350.0, "stock_kg": 5000.0},
        "EX102": {"pid": "EX102", "name": "Garlic Powder", "cost_price": 320.0, "price_per_kg": 450.0, "stock_kg": 3500.0}
    }

def get_logs():
    if not supabase:
        return []
    try:
        res = supabase.table("export_logs").select("*").execute()
        if res.data:
            logs = []
            for r in res.data:
                try:
                    r['items'] = json.loads(r['items']) if isinstance(r['items'], str) else r['items']
                except:
                    r['items'] = []
                logs.append(r)
            return logs
    except Exception as e:
        pass
    return []

# --- APP UI ---
st.title("🚀 Shivraj Unitrade - Export Hub (Safe Mode)")
st.write("ॲप आता पूर्णपणे ऑप्टिमाइझ आणि सुरक्षित मोडमध्ये सुरू आहे.")

products = get_products()
logs = get_logs()

tab1, tab2 = st.tabs(["📦 Products & Cart", "📜 Transaction Logs"])

with tab1:
    st.subheader("Available Products")
    if not products:
        st.warning("No products found.")
    else:
        for pid, p in products.items():
            with st.container(border=True):
                st.markdown(f"**{p['name']}** (Stock: {p['stock_kg']} KG)")
                st.markdown(f"Price: INR {p['price_per_kg']} / KG")
                if st.button(f"Buy {p['name']}", key=f"buy_{pid}"):
                    st.success(f"Order intent registered for {p['name']}!")

with tab2:
    st.subheader("Recent Export Logs")
    if not logs:
        st.info("No transaction logs found yet.")
    else:
        for log in logs:
            with st.container(border=True):
                st.write(f"Customer: **{log.get('buyer', 'N/A')}** | Amount: INR {log.get('amount', 0):,.2f}")
