import datetime
import urllib.parse
import streamlit as st
import pandas as pd
import os
import json
from supabase import create_client, Client
from fpdf import FPDF

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

st.set_page_config(page_title="Shivraj Unitrade | Global Export Management", page_icon=page_icon_file, layout="wide")

# --- CUSTOM PROFESSIONAL UI STYLING (CSS) ---
st.markdown("""
    <style>
    .main {
        background-color: #f8fafc;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: 600;
        color: #334155;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    if not supabase: return
    try:
        data = {"pid": pid, "name": name, "cost_price": cost_price, "price_per_kg": price_per_kg, "stock_kg": stock_kg}
        supabase.table("products").upsert(data).execute()
    except:
        pass

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
                "id": r["id"], 
                "time": r["time"], 
                "buyer": r["buyer"], 
                "email": r.get("email", "N/A"), 
                "phone": r["phone"], 
                "location": r["location"],
                "gstin": r.get("gstin", "N/A"),
                "items": items_parsed, 
                "amount": r["amount"], 
                "paid_amount": r["paid_amount"], 
                "profit": r["profit"],
                "balance_due": r["balance_due"], 
                "payment": r["payment"], 
                "msg": r["msg"], 
                "status": r["status"]
            })
        return logs
    except:
        return []

def insert_db_log(log_data):
    if not supabase: return
    try:
        payload = {
            "time": log_data['time'], 
            "buyer": log_data['buyer'], 
            "email": log_data.get('email', ''), 
            "phone": log_data['phone'], 
            "location": log_data['location'],
            "gstin": log_data.get('gstin', ''),
            "items": json.dumps(log_data['items']), 
            "amount": log_data['amount'], 
            "paid_amount": log_data['paid_amount'],
            "profit": log_data['profit'], 
            "balance_due": log_data['balance_due'], 
            "payment": log_data['payment'],
            "msg": log_data['msg'], 
            "status": log_data['status']
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

# --- PROFESSIONAL GST PDF GENERATOR ---
def clean_pdf_text(text):
    if not text:
        return ""
    return str(text).replace("₹", "INR ").encode('latin-1', 'ignore').decode('latin-1')

def generate_pdf_invoice(log):
    pdf = FPDF()
    pdf.add_page()
    
    # Company Header
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 7, txt=clean_pdf_text("SHIVRAJ UNITRADE"), ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(200, 5, txt=clean_pdf_text("Global Merchant Exporter & Enterprise Trading Hub"), ln=True, align="C")
    pdf.cell(200, 5, txt=clean_pdf_text("GSTIN: 27AAAAA0000A1Z5 | Email: support@shivrajunitrade.com"), ln=True, align="C")
    pdf.cell(200, 5, txt=clean_pdf_text("------------------------------------------------------------------------------------------------------------------------"), ln=True, align="C")
    
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(200, 6, txt=clean_pdf_text("TAX INVOICE / EXPORT BILL OF SUPPLY"), ln=True, align="C")
    
    pdf.ln(3)
    pdf.set_font("Arial", "", 9)
    # Left Box: Customer Info
    pdf.cell(100, 5, txt=clean_pdf_text(f"Invoice No: #{log['id']}"), ln=0)
    pdf.cell(90, 5, txt=clean_pdf_text(f"Date & Time: {log['time']}"), ln=1)
    
    pdf.cell(100, 5, txt=clean_pdf_text(f"Buyer / Customer: {log['buyer']}"), ln=0)
    pdf.cell(90, 5, txt=clean_pdf_text(f"Destination Port: {log['location']}"), ln=1)
    
    pdf.cell(100, 5, txt=clean_pdf_text(f"Email: {log.get('email', 'N/A')}"), ln=0)
    pdf.cell(90, 5, txt=clean_pdf_text(f"Phone: {log['phone']}"), ln=1)
    
    pdf.cell(100, 5, txt=clean_pdf_text(f"Customer GSTIN: {log.get('gstin', 'Unregistered / B2C')}"), ln=1)
    
    pdf.ln(5)
    # Table Header
    pdf.set_font("Arial", "B", 9)
    pdf.cell(10, 7, txt=clean_pdf_text("Sr"), border=1, align="C")
    pdf.cell(80, 7, txt=clean_pdf_text("Product Description"), border=1)
    pdf.cell(25, 7, txt=clean_pdf_text("Qty (KG)"), border=1, align="C")
    pdf.cell(35, 7, txt=clean_pdf_text("Rate (INR)"), border=1, align="R")
    pdf.cell(40, 7, txt=clean_pdf_text("Total (INR)"), border=1, align="R", ln=1)
    
    pdf.set_font("Arial", "", 9)
    for idx, item in enumerate(log['items'], 1):
        item_total = float(item['qty']) * float(item['price'])
        pdf.cell(10, 6, txt=clean_pdf_text(str(idx)), border=1, align="C")
        pdf.cell(80, 6, txt=clean_pdf_text(str(item['name'])), border=1)
        pdf.cell(25, 6, txt=clean_pdf_text(f"{item['qty']:,.2f}"), border=1, align="C")
        pdf.cell(35, 6, txt=clean_pdf_text(f"{item['price']:,.2f}"), border=1, align="R")
        pdf.cell(40, 6, txt=clean_pdf_text(f"{item_total:,.2f}"), border=1, align="R", ln=1)
        
    pdf.ln(2)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(150, 6, txt=clean_pdf_text("Grand Total Amount:"), align="R")
    pdf.cell(40, 6, txt=clean_pdf_text(f"INR {log['amount']:,.2f}"), align="R", ln=1)
    
    pdf.cell(150, 6, txt=clean_pdf_text("Total Amount Paid:"), align="R")
    pdf.cell(40, 6, txt=clean_pdf_text(f"INR {log['paid_amount']:,.2f}"), align="R", ln=1)
    
    pdf.cell(150, 6, txt=clean_pdf_text("Balance Due / Credit:"), align="R")
    pdf.cell(40, 6, txt=clean_pdf_text(f"INR {log['balance_due']:,.2f}"), align="R", ln=1)
    
    pdf.ln(3)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 4, txt=clean_pdf_text(f"Amount in Words: {number_to_words(log['amount'])}"))
    
    pdf.ln(3)
    pdf.set_font("Arial", "", 8)
    pdf.multi_cell(0, 4, txt=clean_pdf_text(f"Payment Status & Audit Trail:\n{log['payment']}"))
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(0, 4, txt=clean_pdf_text("Bank Details for Wire Transfer / NEFT:"), ln=1)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 4, txt=clean_pdf_text("Bank Name: HDFC Bank | A/C No: 50200012345678 | IFSC: HDFC0001234 | Branch: Pune, India"), ln=1)
    
    pdf.ln(8)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(0, 5, txt=clean_pdf_text("For SHIVRAJ UNITRADE"), align="R", ln=1)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 4, txt=clean_pdf_text("[ Authorized Signatory & Company Stamp ]"), align="R", ln=1)
    
    return pdf.output(dest='S').encode('latin1')

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
            st.markdown(f"**{index+1}. {c_item['name']}**\n{c_item['qty']} KG x INR {c_item['price']:,.2f} = **INR {item_cost:,.2f}**")

        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

        st.markdown(f"### **Grand Total: INR {cart_total:,.2f}**")
        st.caption(f"🔤 In Words: {number_to_words(cart_total)}")
        st.divider()
        
        st.subheader("📝 Secure Checkout & Customer Info")
        buyer_name = st.text_input("Customer/Buyer Name:", key="checkout_buyer_name").strip()
        buyer_email = st.text_input("Customer Email ID (Saved for records):", key="checkout_buyer_email").strip()
        buyer_phone = st.text_input("WhatsApp Number (with country code):", key="checkout_buyer_phone").strip()
        buyer_gstin = st.text_input("Customer GSTIN (Optional):", key="checkout_buyer_gstin").strip().upper()
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

                    final_payment_desc = f"Initial: {payment_mode} (Paid: INR {paid_amount:,.2f})"

                    for c_item in st.session_state.cart:
                        update_db_stock(c_item['pid'], current_prods[c_item['pid']]['stock_kg'] - float(c_item['qty']))

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                    items_summary_str = "\n".join([f"- {it['name']} ({it['qty']} KG @ INR {it['price']})" for it in st.session_state.cart])
                    credit_section_msg = f"🔴 Credit / Balance Due: INR {credit_amount:,.2f}\n" if credit_amount > 0 else "✅ Payment Status: Fully Paid\n"

                    whatsapp_msg = (
                        f"🌐 *SHIVRAJ UNITRADE - COMMERCIAL INVOICE* 🌐\n"
                        f"_Merchant Exporter India_\n"
                        f"--------------------------------\n"
                        f"📅 Date: {timestamp}\n"
                        f"👤 Customer: {buyer_name}\n"
                        f"📧 Email: {buyer_email}\n"
                        f"📍 Destination: {location}\n"
                        f"📦 Products Ordered:\n{items_summary_str}\n"
                        f"--------------------------------\n"
                        f"💰 Grand Total: INR {grand_total:,.2f}\n"
                        f"💵 Paid Amount: INR {paid_amount:,.2f}\n"
                        f"{credit_section_msg}"
                        f"💳 Mode: {final_payment_desc}\n"
                        f"--------------------------------\n"
                        f"Thank you for your business! 🙏"
                    )

                    if not is_trial_mode:
                        insert_db_log({
                            "time": timestamp, 
                            "buyer": buyer_name, 
                            "email": buyer_email,
                            "phone": buyer_phone, 
                            "location": location,
                            "gstin": buyer_gstin,
                            "items": list(st.session_state.cart), 
                            "amount": float(grand_total), 
                            "paid_amount": float(paid_amount),
                            "profit": float(total_order_profit), 
                            "balance_due": float(credit_amount), 
                            "payment": final_payment_desc,
                            "msg": whatsapp_msg, 
                            "status": f"Pending (Due: INR {credit_amount:,.2f})" if credit_amount > 0 else "Paid"
                        })
                        st.success("✅ Order successfully saved to Supabase cloud database with customer email!")
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
        st.markdown("🟢 **[SU Logo]**")
with col_title:
    st.title("SHIVRAJ UNITRADE")
    st.markdown("### *Enterprise Merchant Exporter & Global Trade Hub*")

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
m1.metric("💰 Total Revenue", f"INR {total_rev:,.2f}")
m2.metric("📦 Total Orders", f"{len(current_logs)}")
m3.metric("📉 Outstanding Credit", f"INR {sum(log['balance_due'] for log in current_logs):,.2f}", delta_color="inverse")
m4.metric("📈 True Net Profit", f"INR {net_true_profit:,.2f}", delta_color="normal" if net_true_profit >= 0 else "inverse")

st.divider()

# --- TABS CONFIGURATION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Catalog & Store", 
    "📜 Transaction Logs & GST Invoices",
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
                    st.markdown(f"💰 **Rate:** INR {p['price_per_kg']:,.2f} / KG")
                    
                    if p['stock_kg'] <= 500:
                        st.markdown(f"⚠️ **Stock:** `{p['stock_kg']} KG` *(Low Stock Alert)*")
                        supplier_msg = f"Hello, stock for {p['name']} (ID: {pid}) has dropped to {p['stock_kg']} KG at Shivraj Unitrade warehouse. Kindly arrange quick restock."
                        sup_url = f"https://wa.me/?text={urllib.parse.quote(supplier_msg)}"
                        st.markdown(f"🚨 [Send WhatsApp Restock Alert]({sup_url})")
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
    st.subheader("All Sales History, Customer Emails & Printable GST Invoices")
    logs_data = get_db_logs()
    if logs_data:
        st.download_button("📥 Download Transaction History (CSV)", data=pd.DataFrame(logs_data).to_csv(index=False).encode('utf-8'), file_name='merchant_export_history.csv', mime='text/csv')
        st.markdown("---")

    if not logs_data:
        st.info("No transaction records found.")
    else:
        search_query = st.text_input("🔍 Search Buyer Name, Email or Destination:", key="search_txn").strip().lower()
        filtered_logs = [l for l in logs_data if search_query in l['buyer'].lower() or search_query in l['location'].lower() or search_query in l.get('email', '').lower()]
        
        for i, log in enumerate(reversed(filtered_logs), 1):
            with st.container(border=True):
                st.markdown(f"**{i}. Date:** `{log['time']}` | **Customer:** 👤 **{log['buyer']}** (`{log['location']}`) | **Status:** {log['status']}")
                st.markdown(f"📧 **Email:** `{log.get('email', 'N/A')}` | 🏢 **GSTIN:** `{log.get('gstin', 'N/A')}`")
                st.markdown(f"💰 **Total Invoice:** INR {log['amount']:,.2f} | 💵 **Total Paid:** INR {log['paid_amount']:,.2f} | 🔴 **Current Balance Due:** **INR {log['balance_due']:,.2f}**")
                
                with st.expander("📋 View GST Invoice & Details"):
                    st.markdown("### **SHIVRAJ UNITRADE - TAX INVOICE**")
                    st.text(f"Date & Time: {log['time']}")
                    st.text(f"Customer Name: {log['buyer']}")
                    st.text(f"Customer Email: {log.get('email', 'N/A')}")
                    st.text(f"Destination: {log['location']}")
                    st.text(f"Contact Phone: {log['phone']}")
                    st.text(f"Customer GSTIN: {log.get('gstin', 'N/A')}")
                    st.markdown("---")
                    st.markdown("**Purchased Items:**")
                    for item in log['items']:
                        st.text(f"- {item['name']}: {item['qty']} KG @ INR {item['price']:,.2f}/KG = INR {float(item['qty'])*float(item['price']):,.2f}")
                    st.markdown("---")
                    st.text(f"Grand Total Amount: INR {log['amount']:,.2f}")
                    st.text(f"Total Amount Paid: INR {log['paid_amount']:,.2f}")
                    st.text(f"Balance Due: INR {log['balance_due']:,.2f}")
                    st.markdown(f"**Payment History & Trail:**\n{log['payment']}")
                    
                    # --- DOWNLOAD PDF INVOICE BUTTON ---
                    pdf_bytes = generate_pdf_invoice(log)
                    st.download_button(
                        label="📄 Download Professional GST PDF Invoice", 
                        data=pdf_bytes, 
                        file_name=f"Tax_Invoice_{log['buyer']}_{log['id']}.pdf", 
                        mime="application/pdf", 
                        key=f"dl_pdf_{log['id']}"
                    )

                c_act1, c_act2 = st.columns(2)
                with c_act1:
                    if log.get('phone'):
                        wa_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(log['msg'])}"
                        st.markdown(f"📲 [Send Invoice via WhatsApp]({wa_url})")
                with c_act2:
                    if log.get('email') and log['email'] != 'N/A':
                        mail_subject = urllib.parse.quote(f"Tax Invoice #{log['id']} - Shivraj Unitrade")
                        mail_body = urllib.parse.quote(f"Dear {log['buyer']},\n\nPlease find your export invoice details below:\nTotal Amount: INR {log['amount']:,.2f}\nBalance Due: INR {log['balance_due']:,.2f}\n\nThank you for your business!\nShivraj Unitrade")
                        mailto_url = f"mailto:{log['email']}?subject={mail_subject}&body={mail_body}"
                        st.markdown(f"📧 [Send Email to Customer]({mailto_url})")
                
                single_pass = st.text_input("Admin Password to Delete Record:", type="password", key=f"del_pass_{log['id']}")
                if st.button("🗑️ Delete Transaction Record", key=f"btn_del_{log['id']}"):
                    if single_pass == "admin123":
                        delete_db_log(log['id'])
                        st.success("Record deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Authentication Failed: Wrong Admin Password.")

with tab3:
    st.subheader("📉 Credit Ledger & Accounts Receivable (Partial & Full Payments)")
    pending_logs = [log for log in get_db_logs() if log['balance_due'] > 0]
    if not pending_logs:
        st.success("🎉 Outstanding accounts clear! No pending credit balances found.")
    else:
        for log in pending_logs:
            with st.container(border=True):
                c_info, c_action = st.columns([2, 2])
                with c_info:
                    st.markdown(f"👤 **{log['buyer']}** (`{log['location']}`) | 📧 `{log.get('email', 'N/A')}`")
                    st.markdown(f"💰 **Total Invoice:** INR {log['amount']:,.2f} | 💵 **Paid So Far:** INR {log['paid_amount']:,.2f}")
                    st.markdown(f"🔴 **Current Balance Due:** **INR {log['balance_due']:,.2f}**")
                    with st.expander("📜 View Full Payment Audit Trail"):
                        st.text(log['payment'])
                
                with c_action:
                    partial_pay = st.number_input("Enter Partial Payment Amount Received:", min_value=0.0, max_value=float(log['balance_due']), value=0.0, key=f"partial_{log['id']}")
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("💵 Record Partial Payment", key=f"btn_part_{log['id']}"):
                            if partial_pay > 0:
                                new_paid_tot = float(log['paid_amount'] + partial_pay)
                                new_due = float(log['balance_due'] - partial_pay)
                                new_status = "Paid (Cleared)" if new_due <= 0 else f"Pending (Due: INR {new_due:,.2f})"
                                
                                timestamp_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                                new_pay_desc = log['payment'] + f"\n-> Received INR {partial_pay:,.2f} on {timestamp_now}"
                                
                                update_db_credit_payment(log['id'], new_paid_tot, new_due, new_status, new_pay_desc)
                                st.success(f"Successfully recorded INR {partial_pay:,.2f}! Remaining Balance: INR {new_due:,.2f}")
                                st.rerun()
                            else:
                                st.warning("Please enter a valid amount greater than zero.")
                    with col_b2:
                        if st.button("✅ Fully Clear Dues", key=f"full_{log['id']}"):
                            new_paid_tot = float(log['amount'])
                            timestamp_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                            new_pay_desc = log['payment'] + f"\n-> Fully Settled on {timestamp_now}"
                            update_db_credit_payment(log['id'], new_paid_tot, 0.0, "Paid", new_pay_desc)
                            st.success("Credit balance fully settled and cleared!")
                            st.rerun()

                if log.get('phone'):
                    rem_msg = f"Hello {log['buyer']}, gentle reminder from Shivraj Unitrade for your remaining credit balance of INR {log['balance_due']:,.2f}. Kindly clear dues at your earliest convenience. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(rem_msg)}"
                    st.markdown(f"🔔 [Send WhatsApp Payment Reminder]({rem_url})")

with tab4:
    st.subheader("🔒 Profit & Expense Dashboard & Analytics")
    admin_pass_prof = st.text_input("Enter Admin Password:", type="password", key="p_prof")
    if admin_pass_prof == "admin123":
        st.success("Authentication successful.")
        
        st.markdown("### **📊 Visual Business Analytics**")
        if current_logs:
            chart_df = pd.DataFrame([{"Date": l['time'].split()[0], "Revenue": l['amount'], "Profit": l['profit']} for l in current_logs])
            chart_grouped = chart_df.groupby("Date").sum().reset_index()
            st.line_chart(chart_grouped.set_index("Date"))
        else:
            st.info("Insufficient data for chart visualization.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("### **Operational Expense Tracker**")
            with st.form("expense_form"):
                exp_date = st.text_input("Expense Date:", value=datetime.datetime.now().strftime("%d-%m-%Y"))
                exp_cat = st.selectbox("Expense Category:", ["Logistics & Shipping", "Packaging & Materials", "Customs & Clearance", "Office & Miscellaneous"])
                exp_amt = float(st.number_input("Expense Amount (INR):", min_value=0.0, value=1000.0))
                exp_desc = st.text_input("Description/Notes:")
                submitted_exp = st.form_submit_button("Record Expense")
                if submitted_exp:
                    if exp_amt > 0:
                        add_db_expense(exp_date, exp_cat, exp_amt, exp_desc)
                        st.success("Expense added successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a valid expense amount.")

            st.markdown("### **Recorded Expenses List**")
            if not all_expenses:
                st.info("No operational expenses recorded.")
            else:
                for exp in reversed(all_expenses):
                    with st.container(border=True):
                        st.markdown(f"**Date:** `{exp['date']}` | **Category:** {exp['category']} | **Amount:** **INR {exp['amount']:,.2f}**")
                        st.text(f"Notes: {exp['description']}")
                        if st.button("Delete Expense", key=f"del_exp_{exp['id']}"):
                            delete_db_expense(exp['id'])
                            st.success("Expense record removed.")
                            st.rerun()

        with col_p2:
            st.markdown("### **Financial Summary & True Net Profit**")
            gross_prof = sum(log.get('profit', 0) for log in get_db_logs())
            total_exp = sum(e['amount'] for e in get_db_expenses())
            net_prof = gross_prof - total_exp
            
            st.metric("Gross Product Margin Profit", f"INR {gross_prof:,.2f}")
            st.metric("Total Operational Expenses", f"INR {total_exp:,.2f}")
            st.metric("True Net Business Profit", f"INR {net_prof:,.2f}", delta_color="normal" if net_prof >= 0 else "inverse")
            
            st.markdown("---")
            st.markdown("### **📥 Download Financial Reports & Customer Emails**")
            if current_logs:
                email_list_df = pd.DataFrame([{"Customer Name": l['buyer'], "Email": l.get('email', ''), "Phone": l['phone'], "GSTIN": l.get('gstin', '')} for l in current_logs])
                st.download_button("📥 Download Saved Customer Email List (CSV)", data=email_list_df.to_csv(index=False).encode('utf-8'), file_name="shivraj_unitrade_customers.csv", mime="text/csv")

            if all_expenses:
                st.download_button("Download Expenses Report (CSV)", data=pd.DataFrame(all_expenses).to_csv(index=False).encode('utf-8'), file_name="shivraj_unitrade_expenses.csv", mime="text/csv")

    elif admin_pass_prof:
        st.error("Incorrect password.")
    else:
        st.info("Please enter the admin password to view financial analytics.")

with tab5:
    st.subheader("🔒 Inventory Management Control (Admin Authentication Required)")
    admin_pass_inv = st.text_input("Enter Admin Password:", type="password", key="p_inv")
    if admin_pass_inv == "admin123":
        st.success("Authentication successful.")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### **Add / Update Product**")
            pid = st.text_input("Product ID (e.g., EX104):", key="n_id").strip().upper()
            pname = st.text_input("Product Name & Specification:", key="n_name").strip()
            pcost = float(st.number_input("Cost Price per KG (INR):", value=300.0, key="n_cost"))
            pprice = float(st.number_input("Selling Price per KG (INR):", value=500.0, key="n_price"))
            pstock = float(st.number_input("Available Stock (KG):", value=1000.0, key="n_stock"))
            if st.button("Save Product to Warehouse"):
                if pid and pname:
                    add_db_product(pid, pname, pcost, pprice, pstock)
                    st.success("Product inventory updated successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in both Product ID and Name.")
        with c2:
            st.markdown("### **Remove Product**")
            prods = get_db_products()
            if prods:
                sel_p = st.selectbox("Select Product ID to Delete:", list(prods.keys()), key="del_p_box")
                st.text(f"Selected Product: {prods[sel_p]['name']}")
                if st.button("Delete Product"):
                    delete_db_product(sel_p)
                    st.success("Product removed from warehouse inventory!")
                    st.rerun()
            else:
                st.info("No products available to delete.")
    elif admin_pass_inv:
        st.error("Incorrect password.")
    else:
        st.info("Please enter the admin password to access inventory controls.")
