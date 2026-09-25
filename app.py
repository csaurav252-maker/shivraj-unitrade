import datetime
import urllib.parse
import streamlit as st

st.set_page_config(page_title="Shivraj Unitrade | Merchant Exporter", page_icon="🌐", layout="wide")

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

# Initialize Session State securely
if "products" not in st.session_state:
    st.session_state.products = {
        "EX101": {"name": "Onion Powder (Premium)", "cost_price": 250, "price_per_kg": 350, "stock_kg": 5000},
        "EX102": {"name": "Garlic Powder (Premium)", "cost_price": 320, "price_per_kg": 450, "stock_kg": 3500},
        "EX103": {"name": "Mix Spices Blend (Garam Masala)", "cost_price": 420, "price_per_kg": 600, "stock_kg": 2000},
    }

if "export_logs" not in st.session_state:
    st.session_state.export_logs = []

if "cart" not in st.session_state:
    st.session_state.cart = []

# --- SIDEBAR: SHOPPING CART & CHECKOUT ---
with st.sidebar:
    st.header("🛒 Live Shopping Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is empty.")
    else:
        cart_total = 0
        for index, c_item in enumerate(st.session_state.cart):
            item_cost = c_item['price'] * c_item['qty']
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
        
        # Payment options (Credit is NOT a mode, it's calculated automatically based on paid amount)
        payment_options = ["Cash", "UPI / Online", "Cheque", "Dual Payment (Two Modes)"]
        payment_mode = st.selectbox("Payment Mode:", payment_options, key="checkout_payment_mode")
        
        paid_amount = 0.0
        p1_type = "Cash"
        p1_amt = 0.0
        p2_type = "UPI / Online"
        p2_amt = 0.0

        # We need grand_total early to calculate credit/due
        current_grand_total = sum(item['price'] * item['qty'] for item in st.session_state.cart) if st.session_state.cart else 0.0

        if payment_mode == "Dual Payment (Two Modes)":
            st.markdown("---")
            st.write("🔄 **Payment 1:**")
            c1, c2 = st.columns(2)
            with c1:
                p1_type = st.selectbox("Type 1:", ["Cash", "UPI / Online", "Cheque"], index=0, key="d_t1")
            with c2:
                p1_amt = st.number_input("Amount 1 (Rs.):", min_value=0.0, value=0.0, key="amt1")
            
            st.write("🔄 **Payment 2:**")
            c3, c4 = st.columns(2)
            with c3:
                p2_type = st.selectbox("Type 2:", ["Cash", "UPI / Online", "Cheque"], index=1, key="d_t2")
            with c4:
                p2_amt = st.number_input("Amount 2 (Rs.):", min_value=0.0, value=0.0, key="amt2")
            
            paid_amount = p1_amt + p2_amt
            st.markdown(f"**Total Paid Now:** Rs.{paid_amount:,.2f}")
            st.markdown("---")
        else:
            paid_amount = st.number_input("Amount Paid Now (Rs.):", min_value=0.0, max_value=current_grand_total, value=current_grand_total, step=100.0, key="single_paid_amt")
            if paid_amount < current_grand_total:
                st.caption(f"⚠️ Remaining amount will go to **Credit / Udhar**.")

        # Calculate Credit / Pending Due automatically
        credit_amount = max(0.0, current_grand_total - paid_amount)

        if st.button("Confirm Order & Generate Bill", type="primary", use_container_width=True):
            if not buyer_name or not location:
                st.error("❌ Please fill customer name and location!")
            elif not st.session_state.cart:
                st.error("❌ Your cart is empty!")
            else:
                stock_error = False
                for c_item in st.session_state.cart:
                    if c_item['qty'] > st.session_state.products[c_item['pid']]['stock_kg']:
                        st.error(f"❌ Not enough stock for {c_item['name']}!")
                        stock_error = True
                        break

                if not stock_error:
                    grand_total = current_grand_total
                    
                    total_order_profit = 0
                    for c_item in st.session_state.cart:
                        p_info = st.session_state.products[c_item['pid']]
                        item_profit = (c_item['price'] - p_info['cost_price']) * c_item['qty']
                        total_order_profit += item_profit

                    # Prepare description
                    if payment_mode == "Dual Payment (Two Modes)":
                        final_payment_desc = f"Dual ({p1_type}: Rs.{p1_amt:,.2f} + {p2_type}: Rs.{p2_amt:,.2f})"
                    else:
                        final_payment_desc = f"{payment_mode} (Paid: Rs.{paid_amount:,.2f})"

                    for c_item in st.session_state.cart:
                        st.session_state.products[c_item['pid']]['stock_kg'] -= c_item['qty']

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                    items_summary_str = "\n".join([f"- {it['name']} ({it['qty']} KG @ Rs.{it['price']})" for it in st.session_state.cart])

                    # WhatsApp bill clearly showing Paid vs Credit breakdown
                    credit_section_msg = f"🔴 Credit / Due Amount: Rs.{credit_amount:,.2f}\n" if credit_amount > 0 else "✅ Payment Status: Fully Paid\n"

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

                    log_entry = {
                        "id": len(st.session_state.export_logs) + 1,
                        "time": timestamp,
                        "buyer": buyer_name,
                        "phone": buyer_phone,
                        "location": location,
                        "items": list(st.session_state.cart),
                        "amount": grand_total,
                        "paid_amount": paid_amount,
                        "profit": total_order_profit,
                        "balance_due": credit_amount,
                        "payment": final_payment_desc,
                        "msg": whatsapp_msg,
                        "status": f"Pending (Credit: Rs.{credit_amount:,.2f})" if credit_amount > 0 else "Paid"
                    }
                    st.session_state.export_logs.append(log_entry)
                    st.session_state.cart = [] 

                    st.success(f"✅ Order Booked Successfully! Grand Total: Rs.{grand_total:,.2f} | Credit Due: Rs.{credit_amount:,.2f}")
                    st.balloons()

# --- MAIN DASHBOARD AREA ---
st.title("🌐 SHIVRAJ UNITRADE")
st.markdown("### *Merchant Exporter India*")

st.image(
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80",
    caption="Global Export & Quality Spices Hub",
    use_container_width=True
)

st.divider()

# Metrics Summary
total_revenue = sum(log['amount'] for log in st.session_state.export_logs)
total_orders_count = len(st.session_state.export_logs)
total_stock_qty = sum(p['stock_kg'] for p in st.session_state.products.values())
total_pending_credit = sum(log['balance_due'] for log in st.session_state.export_logs)

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total Revenue", f"Rs.{total_revenue:,.2f}")
m2.metric("📦 Total Orders", f"{total_orders_count}")
m3.metric("⚖️ Stock Left", f"{total_stock_qty:,} KG")
m4.metric("📉 Total Credit (Udhar)", f"Rs.{total_pending_credit:,.2f}", delta_color="inverse")

st.divider()

# --- Professional Main Navigation Tabs ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Product Catalog & Store", 
    "📜 Transaction Logs",
    "📉 Credit Ledger",
    "📈 Profit Dashboard (Admin Locked)",
    "⚙️ Inventory Management (Admin Locked)"
])

# --- TAB 1: PRODUCT CATALOG & STORE ---
with tab1:
    st.subheader("Available Warehouse Products & Quick Shopping")
    if not st.session_state.products:
        st.warning("No products available in the warehouse currently.")
    else:
        cols = st.columns(3)
        for i, (pid, p) in enumerate(st.session_state.products.items()):
            col_idx = i % 3
            with cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"### **{p['name']}**")
                    st.caption(f"Product ID: `{pid}`")
                    st.markdown(f"💰 **Rate:** Rs.{p['price_per_kg']} / KG")
                    st.markdown(f"📦 **Stock Available:** `{p['stock_kg']} KG`")
                    
                    qty_to_add = st.number_input("Select Qty (KG):", min_value=1, value=50, step=10, key=f"qty_{pid}")
                    
                    if st.button("🛒 Add to Cart", key=f"add_{pid}", use_container_width=True):
                        if qty_to_add > p['stock_kg']:
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
                                    "price": p['price_per_kg'],
                                    "qty": qty_to_add
                                })
                            st.success(f"Added {qty_to_add}kg!")
                            st.rerun()

# --- TAB 2: TRANSACTION LOGS ---
with tab2:
    st.subheader("All Sales & Dispatch History")
    if not st.session_state.export_logs:
        st.info("No orders recorded yet.")
    else:
        search_query = st.text_input("🔍 Search Customer or Location:", key="search_txn").strip().lower()
        filtered_logs = [
            log for log in st.session_state.export_logs 
            if search_query in log['buyer'].lower() or search_query in log['location'].lower()
        ]

        for i, log in enumerate(reversed(filtered_logs), 1):
            status_color = "🔴" if log['balance_due'] > 0 else "🟢"
            items_str = ", ".join([f"{it['name']} ({it['qty']}kg)" for it in log['items']])
            st.markdown(f"""
            **{i}. Timestamp:** {log['time']} {status_color} Status: **{log['status']}**  
            * **Customer:** {log['buyer']} ({log['location']}) — *Ph: {log.get('phone', 'N/A')}*  
            * **Products:** {items_str}  
            * **Grand Total:** Rs.{log['amount']:,.2f} | **Paid:** Rs.{log['paid_amount']:,.2f} | **📉 Credit Due:** **Rs.{log['balance_due']:,.2f}**  
            * **Payment Mode:** `{log['payment']}`  
            """)
            if log.get('phone'):
                encoded_msg = urllib.parse.quote(log['msg'])
                wa_url = f"https://wa.me/{log['phone']}?text={encoded_msg}"
                st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
            st.markdown("---")

# --- TAB 3: CREDIT LEDGER ---
with tab3:
    st.subheader("📉 Credit / Pending Dues Ledger")
    pending_logs = [log for log in st.session_state.export_logs if log['balance_due'] > 0]

    if not pending_logs:
        st.success("🎉 Great! No credit balance pending from any customer right now.")
    else:
        st.warning(f"Total **{len(pending_logs)}** customers have active credit balances.")
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
                    log['paid_amount'] = log['amount']
                    log['balance_due'] = 0.0
                    log['status'] = "Paid (Cleared)"
                    log['payment'] += " -> [Credit Fully Settled]"
                    st.success("Credit payment received! Ledger updated.")
                    st.rerun()
                
                if log.get('phone'):
                    reminder_msg = f"Hello {log['buyer']}, Gentle reminder from Shivraj Unitrade regarding your pending credit balance of Rs. {log['balance_due']:,.2f}. Please clear it at your earliest convenience. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(reminder_msg)}"
                    st.markdown(f"🔔 [Send Reminder]({rem_url})")
            st.markdown("---")

# --- TAB 4: PROFIT DASHBOARD (PASSWORD PROTECTED) ---
with tab4:
    st.subheader("🔒 Admin Restricted Area: Profit Dashboard")
    admin_pass_1 = st.text_input("Enter Admin Password to View Profit:", type="password", key="pass_profit")
    
    if admin_pass_1 == "admin123":
        st.success("✅ Access Granted! Confidential Profit Analytics:")
        total_net_profit = sum(log.get('profit', 0) for log in st.session_state.export_logs)
        
        st.metric("🔥 Total Net Profit Earned", f"Rs.{total_net_profit:,.2f}")
        st.divider()

        st.markdown("### Order-wise Confidential Profit Breakdown")
        if not st.session_state.export_logs:
            st.info("No orders yet to calculate profit.")
        else:
            for i, log in enumerate(reversed(st.session_state.export_logs), 1):
                order_profit = log.get('profit', 0)
                st.markdown(f"""
                **{i}. Order Date:** {log['time']} | **Customer:** {log['buyer']}  
                * **Total Bill Amount:** Rs.{log['amount']:,.2f}  
                * 🟢 **Net Profit:** **Rs.{order_profit:,.2f}**  
                """)
                st.markdown("---")
    elif admin_pass_1 != "":
        st.error("❌ Incorrect Password! Only Admin can view profits.")
    else:
        st.info("🔒 Please enter the password above to view confidential profit records.")

# --- TAB 5: INVENTORY MANAGEMENT (PASSWORD PROTECTED) ---
with tab5:
    st.subheader("🔒 Admin Restricted Area: Inventory Management")
    admin_pass_2 = st.text_input("Enter Admin Password to Manage Inventory:", type="password", key="pass_inventory")

    if admin_pass_2 == "admin123":
        st.success("✅ Access Granted! You can now add or remove products.")
        col_add, col_rem = st.columns(2)

        with col_add:
            st.markdown("### ➕ Add New Product")
            new_id = st.text_input("Product ID (e.g., EX104):", key="new_p_id").strip().upper()
            new_name = st.text_input("Product Name:", key="new_p_name").strip()
            new_cost = st.number_input("Cost Price per KG (Rs.) [Hidden from Customer]:", min_value=1, value=300, key="new_p_cost")
            new_price = st.number_input("Selling Price per KG (Rs.):", min_value=1, value=500, key="new_p_price")
            new_stock = st.number_input("Initial Stock (in KG):", min_value=1, value=1000, key="new_p_stock")
            
            if st.button("Add Product to Warehouse", key="btn_add_prod"):
                if not new_id or not new_name:
                    st.error("❌ Please provide both Product ID and Name!")
                elif new_id in st.session_state.products:
                    st.error("❌ This Product ID already exists!")
                else:
                    st.session_state.products[new_id] = {
                        "name": new_name,
                        "cost_price": new_cost,
                        "price_per_kg": new_price,
                        "stock_kg": new_stock
                    }
                    st.success(f"✅ Product '{new_name}' added successfully!")
                    st.rerun()

        with col_rem:
            st.markdown("### ❌ Remove Existing Product")
            if not st.session_state.products:
                st.info("No products available to remove.")
            else:
                rem_options = {f"{p['name']} (ID: {pid})": pid for pid, p in st.session_state.products.items()}
                rem_selected = st.selectbox("Select Product to Delete:", list(rem_options.keys()), key="rem_p_sel")
                rem_pid = rem_options[rem_selected]

                if st.button("Delete Selected Product", key="btn_rem_prod"):
                    deleted_name = st.session_state.products[rem_pid]['name']
                    del st.session_state.products[rem_pid]
                    st.success(f"🗑️ Product '{deleted_name}' deleted successfully!")
                    st.rerun()
    elif admin_pass_2 != "":
        st.error("❌ Incorrect Password!")
    else:
        st.info("🔒 Please enter the password above to unlock inventory controls.")
