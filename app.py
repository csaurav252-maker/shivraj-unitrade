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
        st.error("Supabase connection not found.")
        return False
    try:
        data = {
            "pid": pid, 
            "name": name, 
            "cost_price": float(cost_price), 
            "price_per_kg": float(price_per_kg), 
            "stock_kg": float(stock_kg)
        }
        supabase.table("products").upsert(data).execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
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

        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

        st.markdown(f"### **Grand Total: ₹{cart_total:,.2f}**")
        st.caption(f"🔤 In Words: {number_to_words(cart_total)}")
        st.divider()
        
        st.subheader("📝 Secure Checkout")
        buyer_name = st.text_input("Customer/Buyer Name:", key="checkout_buyer_name").strip()
        buyer_phone = st.text_input("WhatsApp Number (with country code):", key="checkout_buyer_phone").strip()
        location = st.text_input("Destination Port/City:", key="checkout_location").strip()
        
        payment_options = ["Cash", "UPI / Bank Transfer", "Cheque", "Dual Payment Mode"]
        payment_mode = st.selectbox("Payment Mode:", payment_options, key="checkout_payment_mode")
        
        paid_amount = 0.0
        p1_type, p1_amt, p2_type, p2_amt = "Cash", 0.0, "UPI / Bank Transfer", 0.0
        current_grand_total = float(sum(float(item['price']) * float(item['qty']) for item in st.session_state.cart)) if st.session_state.cart else 0.0

        if payment_mode == "Dual Payment Mode":
            c1, c2 = st.columns(2)
            with c1:
                p1_type = st.selectbox("Type 1:", ["Cash", "UPI / Bank Transfer", "Cheque"], index=0, key="d_t1")
            with c2:
                p1_amt = float(st.number_input("Amount 1:", min_value=0.0, max_value=float(current_grand_total), value=0.0, key="amt1"))
            c3, c4 = st.columns(2)
            with c3:
                p2_type = st.selectbox("Type 2:", ["Cash", "UPI / Bank Transfer", "Cheque"], index=1, key="d_t2")
            with c4:
                p2_amt = float(st.number_input("Amount 2:", min_value=0.0, max_value=float(current_grand_total - p1_amt), value=0.0, key="amt2"))
            paid_amount = float(p1_amt + p2_amt)
        else:
            paid_amount = float(st.number_input("Amount Paid Now:", min_value=0.0, max_value=float(current_grand_total), value=float(current_grand_total), key="single_paid_amt"))

        credit_amount = float(max(0.0, current_grand_total - paid_amount))

        if st.button("Confirm Order & Generate Invoice", type="primary", use_container_width=True):
            if not buyer_name or not location:
                st.error("❌ Please provide Buyer Name and Destination City/Port!")
            elif not st.session_state.cart:
                st.error("❌ Cart is empty!")
            else:
                stock_error = False
                current_prods = get_db_products()
                for c_item in st.session_state.cart:
                    if float(c_item['qty']) > float(current_prods[c_item['pid']]['stock_kg']):
                        st.error(f"❌ Insufficient stock available for {c_item['name']}!")
                        stock_error = True
                        break

                if not stock_error:
                    grand_total = float(current_grand_total)
                    total_order_profit = sum((float(c_item['price']) - float(current_prods[c_item['pid']]['cost_price'])) * float(c_item['qty']) for c_item in st.session_state.cart)

                    final_payment_desc = f"Initial: {payment_mode} (Paid: ₹{paid_amount:,.2f})"

                    for c_item in st.session_state.cart:
                        update_db_stock(c_item['pid'], current_prods[c_item['pid']]['stock_kg'] - float(c_item['qty']))

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                    items_summary_str = "\n".join([f"- {it['name']} ({it['qty']} KG @ ₹{it['price']})" for it in st.session_state.cart])
                    credit_section_msg = f"🔴 Credit / Balance Due: ₹{credit_amount:,.2f}\n" if credit_amount > 0 else "✅ Payment Status: Fully Paid\n"

                    whatsapp_msg = (
                        f"🌐 *SHIVRAJ UNITRADE - COMMERCIAL INVOICE* 🌐\n"
                        f"_Merchant Exporter India_\n"
                        f"--------------------------------\n"
                        f"📅 Date: {timestamp}\n"
                        f"👤 Customer: {buyer_name}\n"
                        f"📍 Destination: {location}\n"
                        f"📦 Products Ordered:\n{items_summary_str}\n"
                        f"--------------------------------\n"
                        f"💰 Grand Total: ₹{grand_total:,.2f}\n"
                        f"💵 Paid Amount: ₹{paid_amount:,.2f}\n"
                        f"{credit_section_msg}"
                        f"💳 Mode: {final_payment_desc}\n"
                        f"--------------------------------\n"
                        f"Thank you for your business! 🙏"
                    )

                    if not is_trial_mode:
                        insert_db_log({
                            "time": timestamp, "buyer": buyer_name, "phone": buyer_phone, "location": location,
                            "items": list(st.session_state.cart), "amount": float(grand_total), "paid_amount": float(paid_amount),
                            "profit": float(total_order_profit), "balance_due": float(credit_amount), "payment": final_payment_desc,
                            "msg": whatsapp_msg, "status": f"Pending (Due: ₹{credit_amount:,.2f})" if credit_amount > 0 else "Paid"
                        })
                        st.success("✅ Order successfully saved to Supabase cloud database!")
                    else:
                        st.warning("🧪 [Trial Mode] Invoice generated, record not saved to database.")

                    st.session_state.cart = []
                    st.balloons()

# --- MAIN DASHBOARD HEADER ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("s_.png"):
        st.image("s_.png", width=100)
    else:
        st.markdown("🟢 **[SU Logo Missing]**")
with col_title:
    st.title("SHIVRAJ UNITRADE")
    st.markdown("### *Enterprise Merchant Exporter Management System*")

st.image("https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
st.divider()

current_logs = get_db_logs()
current_prods_main = get_db_products()
all_expenses = get_db_expenses()

total_rev = sum(log['amount'] for log in current_logs)
total_gross_prof = sum(log.get('profit', 0) for log in current_logs)
total_exp_amt = sum(e['amount'] for e in all_expenses)
net_true_profit = total_gross_prof - total_exp_amt

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total Revenue", f"₹{total_rev:,.2f}")
m2.metric("📦 Total Orders", f"{len(current_logs)}")
m3.metric("📉 Total Outstanding Credit", f"₹{sum(log['balance_due'] for log in current_logs):,.2f}", delta_color="inverse")
m4.metric("📈 True Net Profit", f"₹{net_true_profit:,.2f}", delta_color="normal" if net_true_profit >= 0 else "inverse")

st.divider()

# --- TABS CONFIGURATION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Catalog & Store", 
    "📜 Transaction Logs & Invoices",
    "📉 Credit Ledger (Accounts Receivable)",
    "📈 Profit & Expense Dashboard",
    "⚙️ Inventory & Warehouse Control"
])

with tab1:
    st.subheader("Available Warehouse Inventory & Quick Ordering")
    live_prods = get_db_products()
    if not live_prods:
        st.warning("No products available in inventory.")
    else:
        cols = st.columns(3)
        for i, (pid, p) in enumerate(live_prods.items()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### **{p['name']}**")
                    st.caption(f"Product ID: `{pid}`")
                    st.markdown(f"💰 **Rate:** ₹{p['price_per_kg']:,.2f} / KG")
                    
                    if p['stock_kg'] <= 500:
                        st.markdown(f"⚠️ **Stock:** `{p['stock_kg']} KG` *(Low Stock Alert)*")
                    else:
                        st.markdown(f"📦 **Stock:** `{p['stock_kg']} KG`")
                        
                    qty_to_add = float(st.number_input("Quantity (KG):", min_value=1.0, value=50.0, key=f"qty_{pid}"))
                    if st.button("🛒 Add to Cart", key=f"add_{pid}", use_container_width=True):
                        if qty_to_add > p['stock_kg']:
                            st.error("Error: Order quantity exceeds available stock limit.")
                        else:
                            for item in st.session_state.cart:
                                if item['pid'] == pid:
                                    item['qty'] += qty_to_add
                                    break
                            else:
                                st.session_state.cart.append({"pid": pid, "name": p['name'], "price": p['price_per_kg'], "qty": qty_to_add})
                            st.success("Successfully added to cart!")
                            st.rerun()

with tab2:
    st.subheader("All Sales History, Detailed Breakdowns & Printable Invoices")
    logs_data = get_db_logs()
    if logs_data:
        st.download_button("📥 Download Transaction History (CSV)", data=pd.DataFrame(logs_data).to_csv(index=False).encode('utf-8'), file_name='merchant_export_history.csv', mime='text/csv')
        st.markdown("---")

    if not logs_data:
        st.info("No transaction records found.")
    else:
        search_query = st.text_input("🔍 Search Buyer Name or Destination:", key="search_txn").strip().lower()
        filtered_logs = [l for l in logs_data if search_query in l['buyer'].lower() or search_query in l['location'].lower()]
        
        for i, log in enumerate(reversed(filtered_logs), 1):
            with st.container(border=True):
                st.markdown(f"**{
