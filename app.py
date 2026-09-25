import datetime
import urllib.parse
import streamlit as st
import pandas as pd
import sqlite3
import os

# --- DATABASE SETUP (SQLite) ---
DB_FILE = "shivraj_unitrade.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Products Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            pid TEXT PRIMARY KEY,
            name TEXT,
            cost_price REAL,
            price_per_kg REAL,
            stock_kg REAL
        )
    ''')
    
    # Transactions / Export Logs Table
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
            ("EX101", "Onion Powder (Premium)", 250.0, 350.0, 5000.0),
            ("EX102", "Garlic Powder (Premium)", 320.0, 450.0, 3500.0),
            ("EX103", "Mix Spices Blend (Garam Masala)", 420.0, 600.0, 2000.0),
        ]
        cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", default_prods)
        conn.commit()
    conn.close()

seed_default_products()

fn_logo_path = "s_.png"
page_icon_file = fn_logo_path if os.path.exists(fn_logo_path) else "🌐"

st.set_page_config(page_title="Shivraj Unitrade | Merchant Exporter", page_icon=page_icon_file, layout="wide")

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
        import json
        try:
            items_parsed = json.loads(r[5])
        except:
            items_parsed = []
            
        logs.append({
            "id": r[0],
            "time": r[1],
            "buyer": r[2],
            "phone": r[3],
            "location": r[4],
            "items": items_parsed,
            "amount": r[6],
            "paid_amount": r[7],
            "profit": r[8],
            "balance_due": r[9],
            "payment": r[10],
            "msg": r[11],
            "status": r[12]
        })
    return logs

def insert_db_log(log_data):
    import json
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO export_logs (time, buyer, phone, location, items, amount, paid_amount, profit, balance_due, payment, msg, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        log_data['time'],
        log_data['buyer'],
        log_data['phone'],
        log_data['location'],
        json.dumps(log_data['items']),
        log_data['amount'],
        log_data['paid_amount'],
        log_data['profit'],
        log_data['balance_due'],
        log_data['payment'],
        log_data['msg'],
        log_data['status']
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

# --- SIDEBAR ---
with st.sidebar:
    st.header("🛒 Live Shopping Cart")
    is_trial_mode = st.toggle("🧪 Trial Mode (इतिहास सेव्ह करू नका)", value=False)
    
    if not st.session_state.cart:
        st.info("Your cart is empty.")
    else:
        cart_total = 0.0
        for index, c_item in enumerate(st.session_state.cart):
            item_cost = float(c_item['price']) * float(c_item['qty'])
            cart_total += item_cost
            st.markdown(f"**{index+1}. {c_item['name']}**\n{c_item['qty']} KG x Rs.{c_item['price']} = **Rs.{item_cost:,.2f}**")

        if st.button("🗑️ Clear Cart"):
            st.session_state.cart = []
            st.rerun()

        st.markdown(f"### **Grand Total: Rs.{cart_total:,.2f}**")
        st.caption(f"🔤 In Words: {number_to_words(cart_total)}")
        st.divider()
        
        st.subheader("📝 Quick Checkout & Payment")
        buyer_name = st.text_input("Customer Name:", key="checkout_buyer_name").strip()
        buyer_phone = st.text_input("WhatsApp Number (with country code, e.g. 91...):", key="checkout_buyer_phone").strip()
        location = st.text_input("Destination City:", key="checkout_location").strip()
        
        payment_options = ["Cash", "UPI / Online", "Cheque", "Dual Payment (Two Modes)"]
        payment_mode = st.selectbox("Payment Mode:", payment_options, key="checkout_payment_mode")
        
        paid_amount = 0.0
        p1_type, p1_amt, p2_type, p2_amt = "Cash", 0.0, "UPI / Online", 0.0
        current_grand_total = float(sum(float(item['price']) * float(item['qty']) for item in st.session_state.cart)) if st.session_state.cart else 0.0

        if payment_mode == "Dual Payment (Two Modes)":
            c1, c2 = st.columns(2)
            with c1:
                p1_type = st.selectbox("Type 1:", ["Cash", "UPI / Online", "Cheque"], index=0, key="d_t1")
            with c2:
                p1_amt = float(st.number_input("Amount 1:", min_value=0.0, max_value=float(current_grand_total), value=0.0, key="amt1"))
            c3, c4 = st.columns(2)
            with c3:
                p2_type = st.selectbox("Type 2:", ["Cash", "UPI / Online", "Cheque"], index=1, key="d_t2")
            with c4:
                p2_amt = float(st.number_input("Amount 2:", min_value=0.0, max_value=float(current_grand_total - p1_amt), value=0.0, key="amt2"))
            paid_amount = float(p1_amt + p2_amt)
        else:
            paid_amount = float(st.number_input("Amount Paid Now:", min_value=0.0, max_value=float(current_grand_total), value=float(current_grand_total), key="single_paid_amt"))

        credit_amount = float(max(0.0, current_grand_total - paid_amount))

        if st.button("Confirm Order & Generate Bill", type="primary", use_container_width=True):
            if not buyer_name or not location:
                st.error("❌ कृपया ग्राहकाचे नाव आणि पत्ता भरा!")
            elif not st.session_state.cart:
                st.error("❌ तुमची कार्टी रिकामी आहे!")
            else:
                stock_error = False
                current_prods = get_db_products()
                for c_item in st.session_state.cart:
                    if float(c_item['qty']) > float(current_prods[c_item['pid']]['stock_kg']):
                        st.error(f"❌ {c_item['name']} साठी पुरेसा स्टॉक उपलब्ध नाही!")
                        stock_error = True
                        break

                if not stock_error:
                    grand_total = float(current_grand_total)
                    total_order_profit = sum((float(c_item['price']) - float(current_prods[c_item['pid']]['cost_price'])) * float(c_item['qty']) for c_item in st.session_state.cart)

                    final_payment_desc = f"Dual ({p1_type}: Rs.{p1_amt:,.2f} + {p2_type}: Rs.{p2_amt:,.2f})" if payment_mode == "Dual Payment (Two Modes)" else f"{payment_mode} (Paid Now: Rs.{paid_amount:,.2f})"

                    for c_item in st.session_state.cart:
                        update_db_stock(c_item['pid'], current_prods[c_item['pid']]['stock_kg'] - float(c_item['qty']))

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                    items_summary_str = "\n".join([f"- {it['name']} ({it['qty']} KG @ Rs.{it['price']})" for it in st.session_state.cart])
                    credit_section_msg = f"🔴 Credit / Udhar Balance (बाकी): Rs.{credit_amount:,.2f}\n" if credit_amount > 0 else "✅ Payment Status: Fully Paid\n"

                    whatsapp_msg = (
                        f"🌐 *SHIVRAJ UNITRADE - INVOICE* 🌐\n"
                        f"_Merchant Exporter India_\n"
                        f"--------------------------------\n"
                        f"📅 Date: {timestamp}\n"
                        f"👤 Customer: {buyer_name}\n"
                        f"📍 Location: {location}\n"
                        f"📦 Products:\n{items_summary_str}\n"
                        f"--------------------------------\n"
                        f"💰 Grand Total: Rs.{grand_total:,.2f}\n"
                        f"💵 Paid Amount: Rs.{paid_amount:,.2f}\n"
                        f"{credit_section_msg}"
                        f"💳 Payment Mode: {final_payment_desc}\n"
                        f"--------------------------------\n"
                        f"Thank you! 🙏"
                    )

                    if not is_trial_mode:
                        insert_db_log({
                            "time": timestamp, "buyer": buyer_name, "phone": buyer_phone, "location": location,
                            "items": list(st.session_state.cart), "amount": float(grand_total), "paid_amount": float(paid_amount),
                            "profit": float(total_order_profit), "balance_due": float(credit_amount), "payment": final_payment_desc,
                            "msg": whatsapp_msg, "status": f"Pending (Credit: Rs.{credit_amount:,.2f})" if credit_amount > 0 else "Paid"
                        })
                        st.success("✅ स्थायी स्वरूपात डेटाबेसमध्ये ऑर्डर सेव्ह झाली!")
                    else:
                        st.warning("🧪 [Trial Mode] बिल तयार झाले, पण डेटाबेसमध्ये सेव्ह झाले नाही!")

                    st.session_state.cart = []
                    st.balloons()

# --- MAIN DASHBOARD ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("s_.png"):
        st.image("s_.png", width=100)
    else:
        st.markdown("🟢 **[SU Logo]**")
with col_title:
    st.title("SHIVRAJ UNITRADE")
    st.markdown("### *Merchant Exporter India*")

st.image("https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80", use_container_width=True)
st.divider()

current_logs = get_db_logs()
current_prods_main = get_db_products()

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total Revenue", f"Rs.{sum(log['amount'] for log in current_logs):,.2f}")
m2.metric("📦 Total Orders", f"{len(current_logs)}")
m3.metric("⚖️ Stock Left", f"{sum(p['stock_kg'] for p in current_prods_main.values()):,.1f} KG")
m4.metric("📉 Total Credit", f"Rs.{sum(log['balance_due'] for log in current_logs):,.2f}", delta_color="inverse")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Catalog & Store", 
    "📜 Transaction Logs",
    "📉 Credit Ledger (उधार खाते)",
    "📈 Profit Dashboard (Admin Locked)",
    "⚙️ Inventory Management (Admin Locked)"
])

with tab1:
    st.subheader("Available Warehouse Products & Quick Shopping")
    live_prods = get_db_products()
    if not live_prods:
        st.warning("No products available.")
    else:
        cols = st.columns(3)
        for i, (pid, p) in enumerate(live_prods.items()):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"### **{p['name']}**")
                    st.caption(f"ID: `{pid}`")
                    st.markdown(f"💰 **Rate:** Rs.{p['price_per_kg']} / KG | 📦 **Stock:** `{p['stock_kg']} KG`")
                    qty_to_add = float(st.number_input("Qty (KG):", min_value=1.0, value=50.0, key=f"qty_{pid}"))
                    if st.button("🛒 Add to Cart", key=f"add_{pid}", use_container_width=True):
                        if qty_to_add > p['stock_kg']:
                            st.error("Not enough stock!")
                        else:
                            for item in st.session_state.cart:
                                if item['pid'] == pid:
                                    item['qty'] += qty_to_add
                                    break
                            else:
                                st.session_state.cart.append({"pid": pid, "name": p['name'], "price": p['price_per_kg'], "qty": qty_to_add})
                            st.success("Added!")
                            st.rerun()

with tab2:
    st.subheader("All Sales & Dispatch History")
    logs_data = get_db_logs()
    if logs_data:
        st.download_button("📥 Download All History as CSV", data=pd.DataFrame(logs_data).to_csv(index=False).encode('utf-8'), file_name='history.csv', mime='text/csv')
        st.markdown("---")

    if not logs_data:
        st.info("No orders recorded yet.")
    else:
        search_query = st.text_input("🔍 Search Customer/Location:", key="search_txn").strip().lower()
        for i, log in enumerate(reversed([l for l in logs_data if search_query in l['buyer'].lower() or search_query in l['location'].lower()]), 1):
            with st.container(border=True):
                st.markdown(f"**{i}. {log['time']}** | **Customer:** {log['buyer']} ({log['location']}) | **Status:** {log['status']}")
                st.markdown(f"Total: Rs.{log['amount']:,.2f} | Paid: Rs.{log['paid_amount']:,.2f} | **Due: Rs.{log['balance_due']:,.2f}**")
                
                if log.get('phone'):
                    wa_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(log['msg'])}"
                    st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
                
                single_pass = st.text_input("Admin Password to Delete:", type="password", key=f"del_pass_{log['id']}")
                if st.button("🗑️ Delete Record", key=f"btn_del_{log['id']}"):
                    if single_pass == "admin123":
                        delete_db_log(log['id'])
                        st.success("Deleted!")
                        st.rerun()
                    else:
                        st.error("Wrong password!")

with tab3:
    st.subheader("📉 Credit Ledger (उधार खाते - Partial & Full Payment)")
    pending_logs = [log for log in get_db_logs() if log['balance_due'] > 0]
    if not pending_logs:
        st.success("🎉 कोणतीही उधार बाकी नाही. सर्व हिशोब चोख आहेत!")
    else:
        for log in pending_logs:
            with st.container(border=True):
                c_info, c_action = st.columns([2, 2])
                with c_info:
                    st.markdown(f"👤 **{log['buyer']}** (`{log['location']}`)")
                    st.markdown(f"Total Bill: Rs.{log['amount']:,.2f} | Paid: Rs.{log['paid_amount']:,.2f}")
                    st.markdown(f"🔴 **Current Due Balance: Rs.{log['balance_due']:,.2f}**")
                
                with c_action:
                    partial_pay = st.number_input("Jama kelele paise (Enter amount):", min_value=0.0, max_value=float(log['balance_due']), value=0.0, key=f"partial_{log['id']}")
                    
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("💵 Add Partial Pay", key=f"btn_part_{log['id']}"):
                            if partial_pay > 0:
                                new_paid_tot = float(log['paid_amount'] + partial_pay)
                                new_due = float(log['balance_due'] - partial_pay)
                                new_status = "Paid (Cleared)" if new_due <= 0 else f"Pending (Due: Rs.{new_due:,.2f})"
                                new_pay_desc = log['payment'] + f" + Partial Paid: Rs.{partial_pay:,.2f}"
                                
                                update_db_credit_payment(log['id'], new_paid_tot, new_due, new_status, new_pay_desc)
                                st.success(f"Rs.{partial_pay:,.2f} जमा झाले! नवीन बाकी: Rs.{new_due:,.2f}")
                                st.rerun()
                            else:
                                st.warning("कृपया योग्य रक्कम टाaka.")
                    with col_b2:
                        if st.button("✅ Fully Clear Due", key=f"full_{log['id']}"):
                            new_paid_tot = float(log['amount'])
                            update_db_credit_payment(log['id'], new_paid_tot, 0.0, "Paid", log['payment'] + " -> [Fully Settled]")
                            st.success("पूर्ण उधार रक्कम जमा झाली!")
                            st.rerun()

                if log.get('phone'):
                    rem_msg = f"Hello {log['buyer']}, gentle reminder from Shivraj Unitrade for your remaining credit due of Rs. {log['balance_due']:,.2f}. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(rem_msg)}"
                    st.markdown(f"🔔 [Send WhatsApp Reminder]({rem_url})")

with tab4:
    st.subheader("🔒 Profit Dashboard")
    if st.text_input("Password:", type="password", key="p_prof") == "admin123":
        st.metric("Total Net Profit", f"Rs.{sum(log.get('profit', 0) for log in get_db_logs()):,.2f}")
    else:
        st.info("Enter password.")

with tab5:
    st.subheader("🔒 Inventory Management")
    if st.text_input("Password:", type="password", key="p_inv") == "admin123":
        c1, c2 = st.columns(2)
        with c1:
            pid = st.text_input("Product ID:", key="n_id").strip().upper()
            pname = st.text_input("Name:", key="n_name").strip()
            pcost = float(st.number_input("Cost Price:", value=300.0, key="n_cost"))
            pprice = float(st.number_input("Selling Price:", value=500.0, key="n_price"))
            pstock = float(st.number_input("Stock (KG):", value=1000.0, key="n_stock"))
            if st.button("Save Product"):
                if pid and pname:
                    add_db_product(pid, pname, pcost, pprice, pstock)
                    st.success("Saved!")
                    st.rerun()
        with c2:
            prods = get_db_products()
            if prods:
                sel_p = st.selectbox("Delete Product:", list(prods.keys()), key="del_p_box")
                if st.button("Delete"):
                    delete_db_product(sel_p)
                    st.success("Deleted!")
                    st.rerun()
    else:
        st.info("Enter password.")
