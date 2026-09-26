import datetime
import urllib.parse
import streamlit as st
import pandas as pd
import sqlite3
import os
import json

# --- DATABASE SETUP ---
DB_FILE = "shivraj_unitrade.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            pid TEXT PRIMARY KEY,
            name TEXT,
            cost_price REAL,
            price_per_kg REAL,
            stock_kg REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS export_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            buyer TEXT,
            phone TEXT,
            location TEXT,
            items TEXT,
            amount REAL,
            paid_amount REAL,
            profit REAL,
            balance_due REAL,
            payment TEXT,
            msg TEXT,
            status TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

def seed_default_products():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    if count == 0:
        default_prods = [
            ("EX101", "Onion Powder (Premium Export Grade)", 250.0, 350.0, 5000.0),
            ("EX102", "Garlic Powder (Premium Export Grade)", 320.0, 450.0, 3500.0),
            ("EX103", "Mix Spices Blend (Garam Masala)", 420.0, 600.0, 2000.0),
        ]
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", default_prods)
        conn.commit()
    conn.close()

seed_default_products()

fn_logo_path = "s__2.png"
page_icon_file = fn_logo_path if os.path.exists(fn_logo_path) else "🌐"

st.set_page_config(page_title="Shivraj Unitrade | Enterprise Merchant Exporter", page_icon=page_icon_file, layout="wide")

def get_db_products():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT pid, name, cost_price, price_per_kg, stock_kg FROM products")
    rows = cursor.fetchall()
    conn.close()
    prods = {}
    for r in rows:
        prods[r[0]] = {
            "name": r[1],
            "cost_price": r[2],
            "price_per_kg": r[3],
            "stock_kg": r[4]
        }
    return prods

def update_db_stock(pid, new_stock):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock_kg = ? WHERE pid = ?", (new_stock, pid))
    conn.commit()
    conn.close()

def add_db_product(pid, name, cost_price, price_per_kg, stock_kg):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)", (pid, name, cost_price, price_per_kg, stock_kg))
    conn.commit()
    conn.close()

def delete_db_product(pid):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE pid = ?", (pid,))
    conn.commit()
    conn.close()

def get_db_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, time, buyer, phone, location, items, amount, paid_amount, profit, balance_due, payment, msg, status FROM export_logs")
    rows = cursor.fetchall()
    conn.close()
    logs = []
    for r in rows:
        try:
            items_parsed = json.loads(r[5])
        except:
            items_parsed = []
            
        logs.append({
            "id": r[0], "time": r[1], "buyer": r[2], "phone": r[3], "location": r[4],
            "items": items_parsed, "amount": r[6], "paid_amount": r[7], "profit": r[8],
            "balance_due": r[9], "payment": r[10], "msg": r[11], "status": r[12]
        })
    return logs

def insert_db_log(log_data):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO export_logs (time, buyer, phone, location, items, amount, paid_amount, profit, balance_due, payment, msg, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_data['time'], log_data['buyer'], log_data['phone'], log_data['location'],
        json.dumps(log_data['items']), log_data['amount'], log_data['paid_amount'],
        log_data['profit'], log_data['balance_due'], log_data['payment'],
        log_data['msg'], log_data['status']
    ))
    conn.commit()
    conn.close()

def delete_db_log(log_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM export_logs WHERE id = ?", (log_id,))
    conn.commit()
    conn.close()

def update_db_credit_payment(log_id, new_paid_total, new_balance_due, status, payment_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE export_logs SET paid_amount = ?, balance_due = ?, status = ?, payment = ? WHERE id = ?", 
                   (new_paid_total, new_balance_due, status, payment_str, log_id))
    conn.commit()
    conn.close()

def get_db_expenses():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, category, amount, description FROM expenses")
    rows = cursor.fetchall()
    conn.close()
    expenses = [{"id": r[0], "date": r[1], "category": r[2], "amount": r[3], "description": r[4]} for r in rows]
    return expenses

def add_db_expense(date, category, amount, description):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)", (date, category, amount, description))
    conn.commit()
    conn.close()

def delete_db_expense(exp_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
    conn.commit()
    conn.close()

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
                        st.success("✅ Order successfully saved to database!")
                    else:
                        st.warning("🧪 [Trial Mode] Invoice generated, record not saved to database.")

                    st.session_state.cart = []
                    st.balloons()

# --- MAIN DASHBOARD HEADER WITH EXACT LOGO IMAGE (`s__2.png`) ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("s__2.png"):
        st.image("s__2.png", width=110)
    else:
        st.markdown("<h1>🌐</h1>", unsafe_allow_html=True)
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
                st.markdown(f"**{i}. Date:** `{log['time']}` | **Customer:** 👤 **{log['buyer']}** (`{log['location']}`) | **Status:** {log['status']}")
                st.markdown(f"💰 **Total Invoice:** ₹{log['amount']:,.2f} | 💵 **Total Paid:** ₹{log['paid_amount']:,.2f} | 🔴 **Current Balance Due:** **₹{log['balance_due']:,.2f}**")
                
                with st.expander("📋 View Detailed Ledger Breakdown & Commercial Invoice"):
                    st.markdown("### **SHIVRAJ UNITRADE - COMMERCIAL INVOICE**")
                    st.text(f"Date & Time: {log['time']}")
                    st.text(f"Customer Name: {log['buyer']}")
                    st.text(f"Destination: {log['location']}")
                    st.text(f"Contact Phone: {log['phone']}")
                    st.markdown("---")
                    st.markdown("**Purchased Items:**")
                    for item in log['items']:
                        st.text(f"- {item['name']}: {item['qty']} KG @ ₹{item['price']:,.2f}/KG = ₹{float(item['qty'])*float(item['price']):,.2f}")
                    st.markdown("---")
                    st.text(f"Grand Total Amount: ₹{log['amount']:,.2f}")
                    st.text(f"Total Amount Paid: ₹{log['paid_amount']:,.2f}")
                    st.text(f"Balance Due: ₹{log['balance_due']:,.2f}")
                    st.markdown(f"**Payment History & Trail:**\n{log['payment']}")
                    
                    invoice_text = f"""SHIVRAJ UNITRADE - COMMERCIAL INVOICE
=====================================
Date: {log['time']}
Customer: {log['buyer']}
Destination: {log['location']}
-------------------------------------
Grand Total: INR {log['amount']:,.2f}
Total Paid: INR {log['paid_amount']:,.2f}
Balance Due: INR {log['balance_due']:,.2f}
Payment Status: {log['status']}
-------------------------------------
Payment Record Logs:
{log['payment']}
=====================================
Thank you for doing business with Shivraj Unitrade!"""
                    st.download_button("📥 Download Official Printable Invoice (.txt)", data=invoice_text.encode('utf-8'), file_name=f"Invoice_{log['buyer']}_{log['id']}.txt", mime="text/plain", key=f"dl_inv_{log['id']}")

                if log.get('phone'):
                    wa_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(log['msg'])}"
                    st.markdown(f"📲 [Send Commercial Invoice via WhatsApp]({wa_url})")
                
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
                    st.markdown(f"👤 **{log['buyer']}** (`{log['location']}`)")
                    st.markdown(f"💰 **Total Invoice:** ₹{log['amount']:,.2f} | 💵 **Paid So Far:** ₹{log['paid_amount']:,.2f}")
                    st.markdown(f"🔴 **Current Balance Due:** **₹{log['balance_due']:,.2f}**")
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
                                new_status = "Paid (Cleared)" if new_due <= 0 else f"Pending (Due: ₹{new_due:,.2f})"
                                
                                timestamp_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                                new_pay_desc = log['payment'] + f"\n-> Received ₹{partial_pay:,.2f} on {timestamp_now}"
                                
                                update_db_credit_payment(log['id'], new_paid_tot, new_due, new_status, new_pay_desc)
                                st.success(f"Successfully recorded ₹{partial_pay:,.2f}! Remaining Balance: ₹{new_due:,.2f}")
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
                    rem_msg = f"Hello {log['buyer']}, gentle reminder from Shivraj Unitrade for your remaining credit balance of ₹{log['balance_due']:,.2f}. Kindly clear dues at your earliest convenience. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(rem_msg)}"
                    st.markdown(f"🔔 [Send WhatsApp Payment Reminder]({rem_url})")

with tab4:
    st.subheader("🔒 Profit & Expense Dashboard (Admin Authentication Required)")
    admin_pass_prof = st.text_input("Enter Admin Password:", type="password", key="p_prof")
    if admin_pass_prof == "admin123":
        st.success("Authentication successful.")
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.markdown("### **Operational Expense Tracker**")
            with st.form("expense_form"):
                exp_date = st.text_input("Expense Date:", value=datetime.datetime.now().strftime("%d-%m-%Y"))
                exp_cat = st.selectbox("Expense Category:", ["Logistics & Shipping", "Packaging & Materials", "Customs & Clearance", "Office & Miscellaneous"])
                exp_amt = float(st.number_input("Expense Amount (₹):", min_value=0.0, value=1000.0))
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
                        st.markdown(f"**Date:** `{exp['date']}` | **Category:** {exp['category']} | **Amount:** **₹{exp['amount']:,.2f}**")
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
            
            st.metric("Gross Product Margin Profit", f"₹{gross_prof:,.2f}")
            st.metric("Total Operational Expenses", f"₹{total_exp:,.2f}")
            st.metric("True Net Business Profit", f"₹{net_prof:,.2f}", delta_color="normal" if net_prof >= 0 else "inverse")
            
            st.info("True Net Profit is calculated automatically by subtracting operational expenses from gross product margins.")

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
            pcost = float(st.number_input("Cost Price per KG (₹):", value=300.0, key="n_cost"))
            pprice = float(st.number_input("Selling Price per KG (₹):", value=500.0, key="n_price"))
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
