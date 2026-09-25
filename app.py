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

# Initialize Database on load
init_db()

# Default Products Insert if Database is empty
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

# Helper Functions for Database Interaction
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
        # items is stored as string representation or we can parse if needed. Let's keep it safe.
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

def clear_all_db_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM export_logs")
    conn.commit()
    conn.close()

def update_db_log_credit(log_id, paid_amt, status, payment_str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE export_logs SET paid_amount = ?, balance_due = 0.0, status = ?, payment = ? WHERE id = ?", (paid_amt, status, payment_str, log_id))
    conn.commit()
    conn.close()

# Helper function to convert number to English words
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

# --- SIDEBAR: SHOPPING CART & CHECKOUT ---
with st.sidebar:
    st.header("🛒 Live Shopping Cart")
    
    products_dict = get_db_products()
    
    st.markdown("---")
    is_trial_mode = st.toggle("🧪 Trial Mode (इतिहास सेव्ह करू नका)", value=False, help="जर हा पर्याय चालू केला, तर ऑर्डर तयार होईल पण ट्रान्झॅक्शन हिस्ट्री किंवा लेजरमध्ये सेव्ह होणार नाही.")
    if is_trial_mode:
        st.warning("⚠️ **Trial Mode चालू आहे:** या व्यवहाराचा रेकॉर्ड स्थायी डेटाबेसमध्ये जतन केला जाणार नाही.")
    st.markdown("---")

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
        buyer_phone = st.text_input("WhatsApp Number:", key="checkout_buyer_phone").strip()
        location = st.text_input("Destination City:", key="checkout_location").strip()
        
        payment_options = ["Cash", "UPI / Online", "Cheque", "Dual Payment (Two Modes)"]
        payment_mode = st.selectbox("Payment Mode:", payment_options, key="checkout_payment_mode")
        
        paid_amount = 0.0
        p1_type = "Cash"
        p1_amt = 0.0
        p2_type = "UPI / Online"
        p2_amt = 0.0

        current_grand_total = float(sum(float(item['price']) * float(item['qty']) for item in st.session_state.cart)) if st.session_state.cart else 0.0

        if payment_mode == "Dual Payment (Two Modes)":
            st.markdown("---")
            st.write("🔄 **Payment 1 (आता दिलेली रक्कम):**")
            c1, c2 = st.columns(2)
            with c1:
                p1_type = st.selectbox("Type 1:", ["Cash", "UPI / Online", "Cheque"], index=0, key="d_t1")
            with c2:
                p1_amt = float(st.number_input("Amount 1 (Rs.):", min_value=0.0, max_value=float(current_grand_total), value=0.0, step=10.0, key="amt1"))
            
            st.write("🔄 **Payment 2 (उरलेली रक्कम):**")
            c3, c4 = st.columns(2)
            with c3:
                p2_type = st.selectbox("Type 2:", ["Cash", "UPI / Online", "Cheque"], index=1, key="d_t2")
            with c4:
                p2_amt = float(st.number_input("Amount 2 (Rs.):", min_value=0.0, max_value=float(current_grand_total - p1_amt), value=0.0, step=10.0, key="amt2"))
            
            paid_amount = float(p1_amt + p2_amt)
            st.markdown(f"**Total Paid Now:** Rs.{paid_amount:,.2f}")
            st.markdown("---")
        else:
            paid_amount = float(st.number_input("Amount Paid Now (आता किती दिले?):", min_value=0.0, max_value=float(current_grand_total), value=float(current_grand_total), step=10.0, key="single_paid_amt"))
            if paid_amount < current_grand_total:
                st.caption(f"⚠️ उरलेली रक्कम आपोआप **Credit (उधार बाकी)** म्हणून जोडली जाईल.")

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
                    
                    total_order_profit = 0.0
                    for c_item in st.session_state.cart:
                        p_info = current_prods[c_item['pid']]
                        item_profit = (float(c_item['price']) - float(p_info['cost_price'])) * float(c_item['qty'])
                        total_order_profit += float(item_profit)

                    if payment_mode == "Dual Payment (Two Modes)":
                        final_payment_desc = f"Dual ({p1_type}: Rs.{p1_amt:,.2f} + {p2_type}: Rs.{p2_amt:,.2f})"
                    else:
                        final_payment_desc = f"{payment_mode} (Paid Now: Rs.{paid_amount:,.2f})"

                    # Reduce Stock in DB permanently
                    for c_item in st.session_state.cart:
                        new_stock_val = current_prods[c_item['pid']]['stock_kg'] - float(c_item['qty'])
                        update_db_stock(c_item['pid'], new_stock_val)

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
                        f"💵 Paid Amount (दिले): Rs.{paid_amount:,.2f}\n"
                        f"{credit_section_msg}"
                        f"💳 Payment Mode: {final_payment_desc}\n"
                        f"--------------------------------\n"
                        f"Thank you! 🙏"
                    )

                    if not is_trial_mode:
                        log_entry = {
                            "time": timestamp,
                            "buyer": buyer_name,
                            "phone": buyer_phone,
                            "location": location,
                            "items": list(st.session_state.cart),
                            "amount": float(grand_total),
                            "paid_amount": float(paid_amount),
                            "profit": float(total_order_profit),
                            "balance_due": float(credit_amount),
                            "payment": final_payment_desc,
                            "msg": whatsapp_msg,
                            "status": f"Pending (Credit: Rs.{credit_amount:,.2f})" if credit_amount > 0 else "Paid"
                        }
                        insert_db_log(log_entry)
                        success_text = f"✅ स्थायी स्वरूपात डेटाबेसमध्ये ऑर्डर सेव्ह झाली! एकूण: Rs.{grand_total:,.2f}"
                    else:
                        success_text = f"🧪 [Trial Mode] बिल तयार झाले, पण डेटाबेसमध्ये सेव्ह झाले नाही!"

                    st.session_state.cart = [] 
                    st.success(success_text)
                    st.balloons()

# --- MAIN DASHBOARD AREA ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("s_.png"):
        st.image("s_.png", width=100)
    else:
        st.markdown("🟢 **[SU Logo]**")
with col_title:
    st.title("SHIVRAJ UNITRADE")
    st.markdown("### *Merchant Exporter India*")

st.image(
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80",
    caption="Global Export & Quality Spices Hub",
    use_container_width=True
)

st.divider()

# Fetch live logs & products for metrics
current_logs = get_db_logs()
current_prods_main = get_db_products()

total_revenue = float(sum(log['amount'] for log in current_logs))
total_orders_count = len(current_logs)
total_stock_qty = float(sum(p['stock_kg'] for p in current_prods_main.values()))
total_pending_credit = float(sum(log['balance_due'] for log in current_logs))

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total Revenue", f"Rs.{total_revenue:,.2f}")
m2.metric("📦 Total Orders", f"{total_orders_count}")
m3.metric("⚖️ Stock Left", f"{total_stock_qty:,.1f} KG")
m4.metric("📉 Total Credit (उधार)", f"Rs.{total_pending_credit:,.2f}", delta_color="inverse")

st.divider()

# --- Professional Main Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Catalog & Store", 
    "📜 Transaction Logs",
    "📉 Credit Ledger (उधार खाते)",
    "📈 Profit Dashboard (Admin Locked)",
    "⚙️ Inventory Management (Admin Locked)"
])

# --- TAB 1: PRODUCT CATALOG & STORE ---
with tab1:
    st.subheader("Available Warehouse Products & Quick Shopping")
    live_prods = get_db_products()
    if not live_prods:
        st.warning("No products available in the warehouse currently.")
    else:
        cols = st.columns(3)
        for i, (pid, p) in enumerate(live_prods.items()):
            col_idx = i % 3
            with cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"### **{p['name']}**")
                    st.caption(f"Product ID: `{pid}`")
                    st.markdown(f"💰 **Rate:** Rs.{p['price_per_kg']} / KG")
                    st.markdown(f"📦 **Stock Available:** `{p['stock_kg']} KG`")
                    
                    qty_to_add = float(st.number_input("Select Qty (KG):", min_value=1.0, value=50.0, step=10.0, key=f"qty_{pid}"))
                    
                    if st.button("🛒 Add to Cart", key=f"add_{pid}", use_container_width=True):
                        if qty_to_add > float(p['stock_kg']):
                            st.error("Not enough stock!")
                        else:
                            item_exists = False
                            for item in st.session_state.cart:
                                if item['pid'] == pid:
                                    item['qty'] += qty_to_add
                                    item_exists = True
                                    break
                            if not item_exists:
                                st.session_state.cart.append({
                                    "pid": pid,
                                    "name": p['name'],
                                    "price": float(p['price_per_kg']),
                                    "qty": float(qty_to_add)
                                })
                            st.success(f"Added {qty_to_add}kg!")
                            st.rerun()

# --- TAB 2: TRANSACTION LOGS ---
with tab2:
    st.subheader("All Sales & Dispatch History (Permanent Database Records)")
    
    logs_data = get_db_logs()
    
    if logs_data:
        df_export = pd.DataFrame([{
            "Time": log['time'],
            "Customer": log['buyer'],
            "Phone": log.get('phone', ''),
            "Location": log['location'],
            "Amount": log['amount'],
            "Paid": log['paid_amount'],
            "Credit Due": log['balance_due'],
            "Payment Mode": log['payment'],
            "Status": log['status']
        } for log in logs_data])
        
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download All History as Excel/CSV (बॅकअप)",
            data=csv_data,
            file_name='shivraj_unitrade_history.csv',
            mime='text/csv'
        )
        st.markdown("---")

    with st.expander("⚙️ Danger Zone: Clear All History Options"):
        clear_pass = st.text_input("Enter Admin Password to Clear All History:", type="password", key="pass_clear_history")
        if clear_pass == "admin123":
            if st.button("🗑️ Clear All Transaction History", type="primary"):
                clear_all_db_logs()
                st.success("✅ सर्व ट्रान्झॅक्शन हिस्ट्री डेटाबेस मधून डिलीट केली गेली आहे!")
                st.rerun()
        elif clear_pass != "":
            st.error("❌ चुकिचा पासवर्ड!")

    if not logs_data:
        st.info("No permanent orders recorded yet in database.")
    else:
        search_query = st.text_input("🔍 Search Customer or Location:", key="search_txn").strip().lower()
        filtered_logs = [
            log for log in logs_data 
            if search_query in log['buyer'].lower() or search_query in log['location'].lower()
        ]

        for i, log in enumerate(reversed(filtered_logs), 1):
            status_color = "🔴" if log['balance_due'] > 0 else "🟢"
            items_str = ", ".join([f"{it['name']} ({it['qty']}kg)" for it in log['items']])
            
            with st.container(border=True):
                st.markdown(f"""
                **{i}. Timestamp:** {log['time']} {status_color} Status: **{log['status']}**  
                * **Customer:** {log['buyer']} ({log['location']}) — *Ph: {log.get('phone', 'N/A')}*  
                * **Products:** {items_str}  
                * **Grand Total:** Rs.{log['amount']:,.2f} | **Paid:** Rs.{log['paid_amount']:,.2f} | **📉 Credit Due:** **Rs.{log['balance_due']:,.2f}**  
                * **Payment Mode:** `{log['payment']}`  
                """)
                
                single_df = pd.DataFrame([{
                    "Time": log['time'],
                    "Customer": log['buyer'],
                    "Phone": log.get('phone', ''),
                    "Location": log['location'],
                    "Amount": log['amount'],
                    "Paid": log['paid_amount'],
                    "Credit Due": log['balance_due'],
                    "Payment Mode": log['payment'],
                    "Status": log['status']
                }])
                single_csv = single_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"💾 Download This Transaction ({log['buyer']}) as Excel",
                    data=single_csv,
                    file_name=f"invoice_{log['buyer'].replace(' ', '_')}_{log['id']}.csv",
                    mime='text/csv',
                    key=f"dl_single_{log['id']}"
                )
                st.markdown("---")
                
                c_wa, c_del = st.columns([2, 1])
                with c_wa:
                    if log.get('phone'):
                        encoded_msg = urllib.parse.quote(log['msg'])
                        wa_url = f"https://wa.me/{log['phone']}?text={encoded_msg}"
                        st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
                
                with c_del:
                    del_key = f"del_pass_{log['id']}"
                    single_pass = st.text_input("Admin Password:", type="password", key=del_key, placeholder="अ‍ॅडमिन पासवर्ड")
                    if st.button("🗑️ Delete This Record", key=f"btn_del_{log['id']}"):
                        if single_pass == "admin123":
                            delete_db_log(log['id'])
                            st.success(f"✅ ग्राहकाची ({log['buyer']}) ऑर्डर डेटाबेस मधून डिलीट केली गेली!")
                            st.rerun()
                        else:
                            st.error("❌ चुकिचा पासवर्ड!")

# --- TAB 3: CREDIT LEDGER ---
with tab3:
    st.subheader("📉 Credit / Pending Dues Ledger (उधार खाते)")
    all_current_logs = get_db_logs()
    pending_logs = [log for log in all_current_logs if log['balance_due'] > 0]

    if not pending_logs:
        st.success("🎉 Great! सध्या कोणाचेही पैसे उधार बाकी नाहीत.")
    else:
        st.warning(f"एकूण **{len(pending_logs)}** ग्राहकांचे पैसे उधार बाकी आहेत.")
        for log in pending_logs:
            col_info, col_action = st.columns([3, 1])
            with col_info:
                items_str = ", ".join([f"{it['name']} ({it['qty']}kg)" for it in log['items']])
                st.markdown(f"""
                👤 **Customer:** {log['buyer']}  
                📍 **Location:** {log['location']} | 📱 **Phone:** {log.get('phone', 'N/A')}  
                📦 **Products:** {items_str}  
                💰 **Grand Total:** Rs.{log['amount']:,.2f} | 💵 **Paid:** Rs.{log['paid_amount']:,.2f}  
                🔴 **Active Credit Due:** **Rs.{log['balance_due']:,.2f}**  
                📅 **Order Date:** {log['time']}  
                """)
            with col_action:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Clear Credit / Mark Paid", key=f"paid_{log['id']}"):
                    new_paid = log['amount']
                    new_status = "Paid (Cleared)"
                    new_pay_str = log['payment'] + " -> [Credit Fully Settled]"
                    update_db_log_credit(log['id'], new_paid, new_status, new_pay_str)
                    st.success("उधार रक्कम जमा झाली! डेटाबेस अपडेट केला.")
                    st.rerun()
                
                if log.get('phone'):
                    reminder_msg = f"Hello {log['buyer']}, Gentle reminder from Shivraj Unitrade regarding your pending credit balance of Rs. {log['balance_due']:,.2f}. Please clear it at your earliest convenience. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(reminder_msg)}"
                    st.markdown(f"🔔 [Send Reminder]({rem_url})")
            st.markdown("---")

# --- TAB 4: PROFIT DASHBOARD ---
with tab4:
    st.subheader("🔒 Admin Restricted Area: Profit Dashboard")
    admin_pass_1 = st.text_input("Enter Admin Password to View Profit:", type="password", key="pass_profit")
    
    if admin_pass_1 == "admin123":
        st.success("✅ Access Granted! Confidential Profit Analytics:")
        profit_logs = get_db_logs()
        total_net_profit = float(sum(log.get('profit', 0.0) for log in profit_logs))
        
        st.metric("🔥 Total Net Profit Earned", f"Rs.{total_net_profit:,.2f}")
        st.divider()

        st.markdown("### Order-wise Confidential Profit Breakdown")
        if not profit_logs:
            st.info("No permanent orders yet to calculate profit.")
        else:
            for i, log in enumerate(reversed(profit_logs), 1):
                order_profit = log.get('profit', 0.0)
                st.markdown(f"""
                **{i}. Order Date:** {log['time']} | **Customer:** {log['buyer']}  
                * **Total Bill Amount:** Rs.{log['amount']:,.2f}  
                * 🟢 **Net Profit:** **Rs.{order_profit:,.2f}**  
                """)
                st.markdown("---")
    elif admin_pass_1 != "":
        st.error("❌ चुकिचा पासवर्ड!")
    else:
        st.info("🔒 नफा पाहण्यासाठी वरील पासवर्ड प्रविष्ट करा.")

# --- TAB 5: INVENTORY MANAGEMENT ---
with tab5:
    st.subheader("🔒 Admin Restricted Area: Inventory Management")
    admin_pass_2 = st.text_input("Enter Admin Password to Manage Inventory:", type="password", key="pass_inventory")

    if admin_pass_2 == "admin123":
        st.success("✅ Access Granted! तुम्ही आता नवीन प्रॉडक्ट जोडू, स्टॉक अपडेट करू किंवा काढू शकता.")
        col_add, col_rem = st.columns(2)

        with col_add:
            st.markdown("### ➕ Add / Update Product")
            new_id = st.text_input("Product ID (e.g., EX104):", key="new_p_id").strip().upper()
            new_name = st.text_input("Product Name:", key="new_p_name").strip()
            new_cost = float(st.number_input("Cost Price per KG (Rs.):", min_value=1.0, value=300.0, key="new_p_cost"))
            new_price = float(st.number_input("Selling Price per KG (Rs.):", min_value=1.0, value=500.0, key="new_p_price"))
            new_stock = float(st.number_input("Initial/Refill Stock (in KG):", min_value=1.0, value=1000.0, key="new_p_stock"))
            
            if st.button("Save Product to Database", key="btn_add_prod"):
                if not new_id or not new_name:
                    st.error("❌ कृपया प्रॉडक्ट आयडी आणि नाव दोन्ही भरा!")
                else:
                    add_db_product(new_id, new_name, new_cost, new_price, new_stock)
                    st.success(f"✅ प्रॉडक्ट '{new_name}' यशस्वीरित्या डेटाबेसमध्ये सेव्ह झाले!")
                    st.rerun()

        with col_rem:
            st.markdown("### ❌ Remove Existing Product")
            current_inv_prods = get_db_products()
            if not current_inv_prods:
                st.info("काढण्यासाठी कोणतेही प्रॉडक्ट उपलब्ध नाही.")
            else:
                rem_options = {f"{p['name']} (ID: {pid})": pid for pid, p in current_inv_prods.items()}
                rem_selected = st.selectbox("डिलिट करण्यासाठी प्रॉडक्ट निवडा:", list(rem_options.keys()), key="rem_p_sel")
                rem_pid = rem_options[rem_selected]

                if st.button("Delete Selected Product from DB", key="btn_rem_prod"):
                    deleted_name = current_inv_prods[rem_pid]['name']
                    delete_db_product(rem_pid)
                    st.success(f"🗑️ प्रॉडक्ट '{deleted_name}' डेटाबेस मधून काढून टाकले गेले!")
                    st.rerun()
    elif admin_pass_2 != "":
        st.error("❌ चुकिचा पासवर्ड!")
    else:
        st.info("🔒 इन्व्हेंटरी कंट्रोल उघडण्यासाठी वरील पासवर्ड टाका.")
