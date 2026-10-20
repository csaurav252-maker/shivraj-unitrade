import datetime
import urllib.parse
import streamlit as st
import pandas as pd
import os
import json
from supabase import create_client, Client

# --- SUPABASE CONFIGURATION ---
SUPABASE_URL = "https://fwlckedxrtkymwqbegos.supabase.co"
SUPABASE_KEY = "sb_publishable_UJinMiq1Fln8ckiLH0cvlA_2ApxVLLS"

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        return None

supabase: Client = init_supabase()

# --- DEFAULT PRODUCTS SEEDING ---
def seed_default_products():
    if not supabase:
        return
    try:
        res = supabase.table("products").select("pid").execute()
        if not res.data:
            default_prods = [
                {"pid": "EX101", "name": "Onion Powder (Premium Export Grade)", "cost_price": 250.0, "price_per_kg": 350.0, "stock_kg": 5000.0},
                {"pid": "EX102", "name": "Garlic Powder (Premium Export Grade)", "cost_price": 320.0, "price_per_kg": 450.0, "stock_kg": 3500.0},
                {"pid": "EX103", "name": "Mix Spices Blend (Garam Masala)", "cost_price": 420.0, "price_per_kg": 600.0, "stock_kg": 2000.0},
            ]
            supabase.table("products").insert(default_prods).execute()
    except Exception as e:
        pass

seed_default_products()

fn_logo_path = "s_.png"
page_icon_file = fn_logo_path if os.path.exists(fn_logo_path) else "🌐"

st.set_page_config(page_title="Shivraj Unitrade | Enterprise Merchant Exporter", page_icon=page_icon_file, layout="wide")

# --- DATABASE HELPER FUNCTIONS (Supabase) ---
def get_db_products():
    if not supabase: return {}
    try:
        res = supabase.table("products").select("*").execute()
        prods = {}
        for r in res.data:
            prods[r["pid"]] = {
                "name": r["name"],
                "cost_price": r["cost_price"],
                "price_per_kg": r["price_per_kg"],
                "stock_kg": r["stock_kg"]
            }
        return prods
    except:
        return {}

def update_db_stock(pid, new_stock):
    if not supabase: return
    try:
        supabase.table("products").update({"stock_kg": new_stock}).eq("pid", pid).execute()
    except:
        pass

def add_db_product(pid, name, cost_price, price_per_kg, stock_kg):
    if not supabase: 
        st.error("❌ Supabase connection not found!")
        return False
    try:
        data = {"pid": pid, "name": name, "cost_price": cost_price, "price_per_kg": price_per_kg, "stock_kg": stock_kg}
        supabase.table("products").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"❌ Database Error: {e}")
        return False

def delete_db_product(pid):
    if not supabase: return
    try:
        supabase.table("products").delete().eq("pid", pid).execute()
    except:
        pass

def get_db_logs():
    if not supabase: return []
    try:
        res = supabase.table("export_logs").select("*").order("id", desc=False).execute()
        logs = []
        for r in res.data:
            try:
                items_parsed = json.loads(r["items"]) if isinstance(r["items"], str) else r["items"]
            except:
                items_parsed = []
            
            logs.append({
                "id": r["id"], "time": r["time"], "buyer": r["buyer"], "phone": r["phone"], "location": r["location"],
                "items": items_parsed, "amount": r["amount"], "paid_amount": r["paid_amount"], "profit": r["profit"],
                "balance_due": r["balance_due"], "payment": r["payment"], "msg": r["msg"], "status": r["status"]
            })
        return logs
    except:
        return []

def insert_db_log(log_data):
    if not supabase: return
    try:
        payload = {
            "time": log_data['time'], "buyer": log_data['buyer'], "phone": log_data['phone'], "location": log_data['location'],
            "items": json.dumps(log_data['items']), "amount": log_data['amount'], "paid_amount": log_data['paid_amount'],
            "profit": log_data['profit'], "balance_due": log_data['balance_due'], "payment": log_data['payment'],
            "msg": log_data['msg'], "status": log_data['status']
        }
        supabase.table("export_logs").insert(payload).execute()
    except Exception as e:
        st.error(f"Error saving to cloud: {e}")

def delete_db_log(log_id):
    if not supabase: return
    try:
        supabase.table("export_logs").delete().eq("id", log_id).execute()
    except:
        pass

def update_db_credit_payment(log_id, new_paid_total, new_balance_due, status, payment_str):
    if not supabase: return
    try:
        supabase.table("export_logs").update({
            "paid_amount": new_paid_total, "balance_due": new_balance_due, "status": status, "payment": payment_str
        }).eq("id", log_id).execute()
    except:
        pass

def get_db_expenses():
    if not supabase: return []
    try:
        res = supabase.table("expenses").select("*").execute()
        expenses = [{"id": r["id"], "date": r["date"], "category": r["category"], "amount": r["amount"], "description": r["description"]} for r in res.data]
        return expenses
    except:
        return []

def add_db_expense(date, category, amount, description):
    if not supabase: return
    try:
        supabase.table("expenses").insert({"date": date, "category": category, "amount": amount, "description": description}).execute()
    except:
        pass

def delete_db_expense(exp_id):
    if not supabase: return
    try:
        supabase.table("expenses").delete().eq("id", exp_id).execute()
    except:
        pass

def number_to_words(num):
    if num == 0:
        return "Zero Rupees Only"
    
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten", 
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]

    def convert_section(n):
        if n == 0:
            return ""
        elif n < 20:
            return units[n] + " "
        elif n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "") + " "
        elif n < 1000:
            return units[n // 100] + " Hundred " + convert_section(n % 100)
        elif n < 100000:
            return convert_section(n // 1000) + "Thousand " + convert_section(n % 1000)
        elif n < 10000000:
            return convert_section(n // 100000) + "Lakh " + convert_section(n % 100000)
        else:
            return convert_section(n // 10000000) + "Crore " + convert_section(n // 10000000)

    try:
        int_part = int(num)
        fractional_part = int(round((num - int_part) * 100))
        words = convert_section(int_part).strip()
        result = f"{words} Rupees"
        if fractional_part > 0:
            result += f" and {convert_section(fractional_part).strip()} Paisa"
        return result + " Only"
    except:
        return ""

if "cart" not in st.session_state:
    st.session_state.cart = []

# --- SIDEBAR: LIVE SHOPPING CART & CHECKOUT ---
with st.sidebar:
    st.header("🛒 Live Order Cart")
    is_trial_mode = st.toggle("🧪 Trial Mode (Do not save history)", value=False)
    
    if not st.session_state.cart:
        st.info("Cart is currently empty.")
    else:
        cart_total = 0.0
        for index, c_item in enumerate(st.session_state.cart):
            item_cost = float(c_item['price']) * float(c_item['qty'])
            cart_total += item_cost
            st.markdown(f"**{index+1}. {c_item['name']}**\n{c_item['qty']} KG x ₹{c_item['price']:,.2f} = **₹{item_cost:,.2f}**")
            
