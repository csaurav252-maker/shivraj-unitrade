import datetime
import urllib.parse
from fpdf import FPDF
import streamlit as st

st.set_page_config(page_title="Shivraj Unitrade | Merchant Exporter", page_icon="🌐", layout="wide")

# Initialize Session State
if "products" not in st.session_state:
    st.session_state.products = {
        "EX101": {"name": "Onion Powder (Premium)", "price_per_kg": 350, "stock_kg": 5000},
        "EX102": {"name": "Garlic Powder (Premium)", "price_per_kg": 450, "stock_kg": 3500},
        "EX103": {"name": "Mix Spices Blend (Garam Masala)", "price_per_kg": 600, "stock_kg": 2000},
    }
if "export_logs" not in st.session_state:
    st.session_state.export_logs = []

# Shopping Cart state
if "cart" not in st.session_state:
    st.session_state.cart = []

# --- Header & Banner ---
st.title("🌐 SHIVRAJ UNITRADE")
st.markdown("### *Merchant Exporter India*")

st.image(
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80",
    caption="Global Export & Quality Spices Hub",
    use_container_width=True
)

st.divider()

# --- Metrics Summary ---
total_revenue = sum(log['amount'] for log in st.session_state.export_logs)
total_orders_count = len(st.session_state.export_logs)
total_stock_qty = sum(p['stock_kg'] for p in st.session_state.products.values())
total_pending_udhar = sum(log['balance_due'] for log in st.session_state.export_logs)

m1, m2, m3, m4 = st.columns(4)
m1.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
m2.metric("📦 Total Orders", f"{total_orders_count}")
m3.metric("⚖️ Stock Left", f"{total_stock_qty:,} KG")
m4.metric("⚠️ Pending Udhar", f"₹{total_pending_udhar:,.2f}", delta_color="inverse")

st.divider()

# --- Tabs Setup ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📦 Live Stock", 
    "🛒 Multiple Items Cart & Booking", 
    "📜 Transaction Logs",
    "⚠️ Udhar Ledger",
    "⚙️ Inventory Management"
])

# --- TAB 1: STOCK ---
with tab1:
    st.subheader("Available Warehouse Stock")
    if not st.session_state.products:
        st.warning("No products available in the warehouse currently.")
    else:
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        for idx, (pid, p) in enumerate(st.session_state.products.items()):
            with cols[idx % 3]:
                st.info(f"**{p['name']}**\n\n* **ID:** `{pid}`\n* **Rate:** ₹{p['price_per_kg']} / KG\n* **Stock Left:** **{p['stock_kg']} KG**")

# --- TAB 2: MULTIPLE ITEMS CART & BOOKING ---
with tab2:
    st.subheader("Add Multiple Items to Cart & Checkout")

    if not st.session_state.products:
        st.warning("⚠️ Please add products first from 'Inventory Management' tab!")
    else:
        col_add_cart, col_checkout = st.columns([1, 1])

        with col_add_cart:
            st.markdown("### ➕ Add Item to Cart")
            with st.form("add_to_cart_form", clear_on_submit=True):
                product_options = {f"{v['name']} (₹{v['price_per_kg']}/kg - Stock: {v['stock_kg']}kg)": k for k, v in st.session_state.products.items()}
                selected_label = st.selectbox("Select Product:", list(product_options.keys()))
                cart_pid = product_options[selected_label]
                
                cart_qty = st.number_input("Quantity (in KG):", min_value=1, value=50, step=10)
                add_to_cart_btn = st.form_submit_button("Add to Cart 🛒")

            if add_to_cart_btn:
                prod_info = st.session_state.products[cart_pid]
                if cart_qty > prod_info["stock_kg"]:
                    st.error(f"❌ Not enough stock! Only {prod_info['stock_kg']} KG available.")
                else:
                    # Check if already in cart, update quantity
                    item_exists = False
                    for item in st.session_state.cart:
                        if item['pid'] == cart_pid:
                            item['qty'] += cart_qty
                            item_exists = True
                            break
                    if not item_exists:
                        st.session_state.cart.append({
                            "pid": cart_pid,
                            "name": prod_info['name'],
                            "price": prod_info['price_per_kg'],
                            "qty": cart_qty
                        })
                    st.success(f"✅ Added {cart_qty} KG of {prod_info['name']} to cart!")
                    st.rerun()

        with col_checkout:
            st.markdown("### 🛍️ Current Shopping Cart")
            if not st.session_state.cart:
                st.info("Your cart is empty. Add items from the left.")
            else:
                cart_total = 0
                for index, c_item in enumerate(st.session_state.cart):
                    item_cost = c_item['price'] * c_item['qty']
                    cart_total += item_cost
                    st.markdown(f"**{index+1}. {c_item['name']}** — {c_item['qty']} KG x ₹{c_item['price']} = **₹{item_cost:,.2f}**")

                if st.button("🗑️ Clear Cart"):
                    st.session_state.cart = []
                    st.rerun()

                st.markdown(f"### **Grand Total: ₹{cart_total:,.2f}**")
                
                st.markdown("---")
                st.markdown("### 📝 Final Checkout & Details")
                
                with st.form("checkout_form"):
                    buyer_name = st.text_input("Customer / Buyer Name:").strip()
                    buyer_phone = st.text_input("Customer WhatsApp Number (e.g., 9198xxxxxxxx):").strip()
                    location = st.text_input("Destination City / Location:").strip()
                    
                    payment_mode = st.selectbox("Payment Mode:", ["Cash", "UPI / Online", "Cheque", "Credit (Udhar)", "Split (Cash + UPI)"])
                    
                    cash_part = 0.0
                    upi_part = 0.0

                    if payment_mode == "Split (Cash + UPI)":
                        cs1, cs2 = st.columns(2)
                        with cs1:
                            cash_part = st.number_input("Cash Amount Received (₹):", min_value=0.0, value=0.0)
                        with cs2:
                            upi_part = st.number_input("UPI Amount Received (₹):", min_value=0.0, value=0.0)

                    checkout_btn = st.form_submit_button("Confirm Order & Generate Multi-Item Bill")

                if checkout_btn:
                    if not buyer_name or not location:
                        st.error("❌ Please fill in customer name and location!")
                    elif not st.session_state.cart:
                        st.error("❌ Cart is empty!")
                    else:
                        # Stock validation for all cart items
                        stock_error = False
                        for c_item in st.session_state.cart:
                            if c_item['qty'] > st.session_state.products[c_item['pid']]['stock_kg']:
                                st.error(f"❌ Stock expired/insufficient for {c_item['name']}!")
                                stock_error = True
                                break

                        if not stock_error:
                            # Deduct stock and calculate total
                            grand_total = sum(item['price'] * item['qty'] for item in st.session_state.cart)
                            
                            balance_due = 0.0
                            final_payment_desc = payment_mode

                            if payment_mode == "Split (Cash + UPI)":
                                paid_so_far = cash_part + upi_part
                                balance_due = max(0.0, grand_total - paid_so_far)
                                final_payment_desc = f"Split (Cash: ₹{cash_part:,.2f}, UPI: ₹{upi_part:,.2f}) | Due: ₹{balance_due:,.2f}"
                            elif payment_mode == "Credit (Udhar)":
                                balance_due = grand_total
                                final_payment_desc = f"Credit (Full Udhar) | Due: ₹{balance_due:,.2f}"
                            elif payment_mode in ["Cash", "UPI / Online", "Cheque"]:
                                balance_due = 0.0

                            # Deduct from actual warehouse stock
                            for c_item in st.session_state.cart:
                                st.session_state.products[c_item['pid']]['stock_kg'] -= c_item['qty']

                            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                            
                            # Construct items description for message & logs
                            items_summary_str = "\n".join([f"- {it['name']} ({it['qty']} KG @ ₹{it['price']})" for it in st.session_state.cart])

                            whatsapp_msg = (
                                f"🌐 *SHIVRAJ UNITRADE - MULTI-ITEM INVOICE* 🌐\n"
                                f"_Merchant Exporter India_\n"
                                f"--------------------------------\n"
                                f"📅 Date: {timestamp}\n"
                                f"👤 Customer: {buyer_name}\n"
                                f"📍 Location: {location}\n"
                                f"📦 Products Ordered:\n{items_summary_str}\n"
                                f"--------------------------------\n"
                                f"💰 Grand Total: ₹{grand_total:,.2f}\n"
                                f"💳 Payment: {final_payment_desc}\n"
                                f"--------------------------------\n"
                                f"Thank you for your business! 🙏"
                            )

                            log_entry = {
                                "id": len(st.session_state.export_logs) + 1,
                                "time": timestamp,
                                "buyer": buyer_name,
                                "phone": buyer_phone,
                                "location": location,
                                "items": list(st.session_state.cart),
                                "amount": grand_total,
                                "balance_due": balance_due,
                                "payment": final_payment_desc,
                                "msg": whatsapp_msg,
                                "status": "Pending" if balance_due > 0 else "Paid"
                            }
                            st.session_state.export_logs.append(log_entry)
                            
                            # Clear cart after successful checkout
                            st.session_state.cart = []

                            st.success(f"✅ Order booked successfully! Grand Total: ₹{grand_total:,.2f} | Balance Due: ₹{balance_due:,.2f}")
                            
                            # PDF Generation with Multiple Items
                            pdf = FPDF()
                            pdf.add_page()
                            pdf.set_font("Arial", size=12)
                            pdf.cell(200, 10, txt="SHIVRAJ UNITRADE - INVOICE", ln=True, align="C")
                            pdf.set_font("Arial", size=10)
                            pdf.cell(200, 10, txt="Merchant Exporter India", ln=True, align="C")
                            pdf.ln(5)
                            pdf.cell(200, 8, txt=f"Date: {timestamp}", ln=True)
                            pdf.cell(200, 8, txt=f"Customer Name: {buyer_name}", ln=True)
                            pdf.cell(200, 8, txt=f"Location: {location}", ln=True)
                            pdf.ln(5)
                            
                            pdf.set_font("Arial", style="B", size=10)
                            pdf.cell(100, 8, txt="Product Name", border=1)
                            pdf.cell(30, 8, txt="Qty (KG)", border=1, align="C")
                            pdf.cell(30, 8, txt="Price/kg", border=1, align="R")
                            pdf.cell(30, 8, txt="Total", border=1, align="R")
                            pdf.ln(8)

                            pdf.set_font("Arial", size=9)
                            for it in log_entry['items']:
                                row_total = it['price'] * it['qty']
                                pdf.cell(100, 7, txt=it['name'], border=1)
                                pdf.cell(30, 7, txt=str(it['qty']), border=1, align="C")
                                pdf.cell(30, 7, txt=str(it['price']), border=1, align="R")
                                pdf.cell(30, 7, txt=f"{row_total:,.2f}", border=1, align="R")
                                pdf.ln(7)

                            pdf.ln(5)
                            pdf.set_font("Arial", style="B", size=10)
                            pdf.cell(200, 8, txt=f"Grand Total: Rs. {grand_total:,.2f}", ln=True, align="R")
                            pdf.cell(200, 8, txt=f"Payment Details: {final_payment_desc}", ln=True, align="R")
                            pdf.ln(10)
                            pdf.set_font("Arial", size=10)
                            pdf.cell(200, 8, txt="Thank you for your business!", ln=True, align="C")
                            
                            pdf_bytes = pdf.output(dest='S').encode('latin1')

                            col_dl, col_wa = st.columns(2)
                            with col_dl:
                                st.download_button(
                                    label="📄 Download Multi-Item PDF Invoice",
                                    data=pdf_bytes,
                                    file_name=f"Invoice_{buyer_name}.pdf",
                                    mime="application/pdf"
                                )

                            with col_wa:
                                if buyer_phone:
                                    encoded_msg = urllib.parse.quote(whatsapp_msg)
                                    wa_url = f"https://wa.me/{buyer_phone}?text={encoded_msg}"
                                    st.markdown(f"### 📲 [Send on WhatsApp]({wa_url})", unsafe_allow_html=True)

                            st.balloons()

# --- TAB 3: TRANSACTION LOGS ---
with tab3:
    st.subheader("All Sales & Dispatch History")
    
    if not st.session_state.export_logs:
        st.info("No orders recorded yet.")
    else:
        search_query = st.text_input("🔍 Search Customer or Location:").strip().lower()

        filtered_logs = [
            log for log in st.session_state.export_logs 
            if search_query in log['buyer'].lower() or search_query in log['location'].lower()
        ]

        for i, log in enumerate(reversed(filtered_logs), 1):
            status_color = "🔴" if log['balance_due'] > 0 else "🟢"
            
            # Format items list for display
            items_str = ", ".join([f"{it['name']} ({it['qty']}kg)" for it in log['items']])
            
            st.markdown(f"""
            **{i}. Timestamp:** {log['time']} {status_color} Status: **{log['status']}**  
            * **Customer:** {log['buyer']} ({log['location']}) — *Ph: {log.get('phone', 'N/A')}*  
            * **Products:** {items_str}  
            * **Grand Total:** ₹{log['amount']:,.2f} | **Balance Due:** ₹{log['balance_due']:,.2f}  
            * **Payment Mode:** `{log['payment']}`  
            """)
            if log.get('phone'):
                encoded_msg = urllib.parse.quote(log['msg'])
                wa_url = f"https://wa.me/{log['phone']}?text={encoded_msg}"
                st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
            st.markdown("---")

# --- TAB 4: UDHAR LEDGER ---
with tab4:
    st.subheader("⚠️ Udhar / Pending Dues Tracker")
    
    pending_logs = [log for log in st.session_state.export_logs if log['balance_due'] > 0]

    if not pending_logs:
        st.success("🎉 Great! No pending dues from any customer right now.")
    else:
        st.warning(f"Total **{len(pending_logs)}** customers have pending payments.")

        for log in pending_logs:
            col_info, col_action = st.columns([3, 1])
            with col_info:
                items_str = ", ".join([f"{it['name']} ({it['qty']}kg)" for it in log['items']])
                st.markdown(f"""
                👤 **Customer:** {log['buyer']}  
                📍 **Location:** {log['location']} | 📱 **Phone:** {log.get('phone', 'N/A')}  
                📦 **Products:** {items_str}  
                🔴 **Pending Amount:** **₹{log['balance_due']:,.2f}** *(Total Bill: ₹{log['amount']:,.2f})*  
                📅 **Order Date:** {log['time']}  
                """)
            with col_action:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("✅ Mark as Paid", key=f"paid_{log['id']}"):
                    log['balance_due'] = 0.0
                    log['status'] = "Paid (Cleared)"
                    log['payment'] += " -> [Fully Paid & Settled]"
                    st.success("Payment received! Udhar cleared.")
                    st.rerun()
                
                if log.get('phone'):
                    reminder_msg = f"Hello {log['buyer']}, Gentle reminder from Shivraj Unitrade regarding your pending balance of Rs. {log['balance_due']:,.2f}. Please clear it at your earliest convenience. Thank you!"
                    rem_url = f"https://wa.me/{log['phone']}?text={urllib.parse.quote(reminder_msg)}"
                    st.markdown(f"🔔 [Send Reminder]({rem_url})")

            st.markdown("---")

# --- TAB 5: INVENTORY MANAGEMENT ---
with tab5:
    st.subheader("Manage Products (Add or Remove)")

    col_add, col_rem = st.columns(2)

    with col_add:
        st.markdown("### ➕ Add New Product")
        with st.form("add_product_form", clear_on_submit=True):
            new_id = st.text_input("Product ID (e.g., EX104):").strip().upper()
            new_name = st.text_input("Product Name:").strip()
            new_price = st.number_input("Price per KG (₹):", min_value=1, value=500)
            new_stock = st.number_input("Initial Stock (in KG):", min_value=1, value=1000)
            
            add_btn = st.form_submit_button("Add Product to Warehouse")

        if add_btn:
            if not new_id or not new_name:
                st.error("❌ Please provide both Product ID and Name!")
            elif new_id in st.session_state.products:
                st.error("❌ This Product ID already exists!")
            else:
                st.session_state.products[new_id] = {
                    "name": new_name,
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
            with st.form("remove_product_form"):
                rem_options = {f"{p['name']} (ID: {pid})": pid for pid, p in st.session_state.products.items()}
                rem_selected = st.selectbox("Select Product to Delete:", list(rem_options.keys()))
                rem_pid = rem_options[rem_selected]

                remove_btn = st.form_submit_button("Delete Selected Product")

            if remove_btn:
                deleted_name = st.session_state.products[rem_pid]['name']
                del st.session_state.products[rem_pid]
                st.success(f"🗑️ Product '{deleted_name}' deleted successfully!")
                st.rerun()
