import streamlit as st
import pandas as pd
import datetime
import os
import json
from supabase import create_client, Client

# --- PAGE CONFIG ---
st.set_page_config(page_title="Shivraj Unitrade", page_icon="🌐", layout="wide")

# --- SUPABASE CONNECTION ---
SUPABASE_URL = "https://fwlckedxrtkymwqbegos.supabase.co"
SUPABASE_KEY = "sb_publishable_UJinMiq1Fln8ckiLH0cvlA_2ApxVLLS"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except:
        return None

supabase = init_supabase()

# --- DATABASE HELPERS ---
def get_products():
    if not supabase: return {}
    try:
        res = supabase.table("products").select("*").execute()
        return {r["pid"]: r for r in res.data} if res.data else {}
    except:
        return {}

def get_logs():
    if not supabase: return []
    try:
        res = supabase.table("export_logs").select("*").execute()
        logs = []
        if res.data:
            for r in res.data:
                try:
                    r['items'] = json.loads(r['items']) if isinstance(r['items'], str) else r['items']
                except:
                    r['items'] = []
                logs.append(r)
        return logs
    except:
        return []

# --- SESSION STATE ---
if "cart" not in st.session_state:
    st.session_state.cart = []

# --- MAIN APP UI ---
st.title("🌐 SHIVRAJ UNITRADE")
st.subheader("Merchant Exporter & Order Management")
st.divider()

products = get_products()
logs = get_logs()

# Sidebar Cart
with st.sidebar:
    st.header("🛒 Order Cart")
    if not st.session_state.cart:
        st.info("Cart is empty.")
    else:
        total = 0
        for i, item in enumerate(st.session_state.cart):
            cost = item['price'] * item['qty']
            total += cost
            st.write(f"{i+1}. {item['name']} - {item['qty']} KG = INR {cost:,.2f}")
        
        st.markdown(f"### Total: INR {total:,.2f}")
        if st.button("Clear Cart"):
            st.session_state.cart = []
            st.rerun()
            
        st.divider()
        buyer = st.text_input("Customer Name:")
        phone = st.text_input("Phone Number:")
        location = st.text_input("Destination:")
        
        if st.button("Complete Order", type="primary"):
            if not buyer or not location:
                st.error("Please enter Customer Name and Destination!")
            else:
                st.success("Order placed successfully!")
                st.session_state.cart = []

# Tabs
tab1, tab2 = st.tabs(["📦 Products", "📜 Transactions"])

with tab1:
    st.subheader("Product Catalog")
    if not products:
        st.warning("No products found in database.")
    else:
        for pid, p in products.items():
            with st.container(border=True):
                st.markdown(f"### **{p['name']}**")
                st.write(f"Price: INR {p['price_per_kg']} / KG | Stock: {p['stock_kg']} KG")
                qty = st.number_input("Quantity (KG):", min_value=1.0, value=10.0, key=f"q_{pid}")
                if st.button(f"Add to Cart", key=f"add_{pid}"):
                    st.session_state.cart.append({
                        "pid": pid,
                        "name": p['name'],
                        "price": p['price_per_kg'],
                        "qty": qty
                    })
                    st.success("Added to cart!")
                    st.rerun()

with tab2:
    st.subheader("Sales History")
    if not logs:
        st.info("No transaction history available.")
    else:
        for log in logs:
            with st.container(border=True):
                st.write(f"**Customer:** {log.get('buyer')} | **Destination:** {log.get('location')}")
                st.write(f"**Amount:** INR {log.get('amount', 0):,.2f} | **Date:** {log.get('time')}")
                
