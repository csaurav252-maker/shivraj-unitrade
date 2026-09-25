import datetime
import urllib.parse
from fpdf import FPDF
import streamlit as st

st.set_page_config(page_title="Shivraj Unitrade | Merchant Exporter", page_icon="🌐", layout="wide")

# Session State मध्ये स्टॉक आणि लॉग्स जतन करणे
if "products" not in st.session_state:
    st.session_state.products = {
        "EX101": {"name": "Onion Powder (Premium)", "price_per_kg": 350, "stock_kg": 5000},
        "EX102": {"name": "Garlic Powder (Premium)", "price_per_kg": 450, "stock_kg": 3500},
        "EX103": {"name": "Mix Spices Blend (Garam Masala)", "price_per_kg": 600, "stock_kg": 2000},
    }
if "export_logs" not in st.session_state:
    st.session_state.export_logs = []

# --- Professional Header with Banner Image ---
st.title("🌐 SHIVRAJ UNITRADE")
st.markdown("### *Merchant Exporter India*")

st.image(
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80",
    caption="Global Export & Quality Spices Hub",
    use_container_width=True
)

st.divider()

# --- BUSINESS ANALYTICS METRICS (Top Summary) ---
total_revenue = sum(log['amount'] for log in st.session_state.export_logs)
total_orders_count = len(st.session_state.export_logs)
total_stock_qty = sum(p['stock_kg'] for p in st.session_state.products.values())

m1, m2, m3 = st.columns(3)
m1.metric("💰 Total Business Revenue", f"₹{total_revenue:,.2f}")
m2.metric("📦 Total Orders Completed", f"{total_orders_count}")
m3.metric("⚖️ Total Warehouse Stock Left", f"{total_stock_qty:,} KG")

st.divider()

# --- TABS SETUP ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Live Stock & Inventory", 
    "🛒 New Sales / Export Booking", 
    "📜 Transaction & Dispatch Logs",
    "⚙️ Inventory Management (Add/Remove)"
])

# --- TAB 1: STOCK ---
with tab1:
    st.subheader("Available Warehouse Stock")
    if not st.session_state.products:
        st.warning("सध्या वखारमध्ये (Warehouse) एकही प्रॉडक्ट उपलब्ध नाही. कृपया 'Inventory Management' टॅबमधून नवीन प्रॉडक्ट ॲड करा.")
    else:
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]

        for idx, (pid, p) in enumerate(st.session_state.products.items()):
            with cols[idx % 3]:
                st.info(f"**{p['name']}**\n\n* **ID:** `{pid}`\n* **Rate:** ₹{p['price_per_kg']} / KG\n* **Stock Left:** **{p['stock_kg']} KG**")

# --- TAB 2: BOOKING / SALES ---
with tab2:
    st.subheader("Create New Order / Export Booking")

    if not st.session_state.products:
        st.warning("⚠️ प्रथम 'Inventory Management' मधून प्रॉडक्ट ॲड करा, मगच ऑर्डर बुक करता येईल!")
    else:
        with st.form("order_form", clear_on_submit=True):
            buyer_name = st.text_input("Customer / Buyer Name:").strip()
            buyer_phone = st.text_input("Customer WhatsApp Number (with country code, e.g., 9198xxxxxxxx):").strip()
            location = st.text_input("Destination City / Location:").strip()

            product_options = {f"{v['name']} (₹{v['price_per_kg']}/kg)": k for k, v in st.session_state.products.items()}
            selected_label = st.selectbox("Select Product:", list(product_options.keys()))
            pid = product_options[selected_label]

            qty_kg = st.number_input("Quantity Required (in KG):", min_value=1, value=100, step=10)
            payment_mode = st.selectbox("Payment Mode:", ["Cash (रोख)", "UPI / Online", "Cheque (चेक)", "Udhar (उधारी)"])

            submit_btn = st.form_submit_button("Confirm Order & Generate Bill")

        if submit_btn:
            if not buyer_name or not location:
                st.error("❌ कृपया कस्टमरचे नाव आणि पत्ता भरा!")
            else:
                prod = st.session_state.products[pid]
                if qty_kg > prod["stock_kg"]:
                    st.error(f"❌ अपुरा स्टॉक! सध्या फक्त {prod['stock_kg']} KG उपलब्ध आहे.")
                else:
                    total_amount = prod["price_per_kg"] * qty_kg
                    prod["stock_kg"] -= qty_kg

                    timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                    
                    whatsapp_msg = (
                        f"🌐 *SHIVRAJ UNITRADE - INVOICE* 🌐\n"
                        f"_Merchant Exporter India_\n"
                        f"--------------------------------\n"
                        f"📅 Date: {timestamp}\n"
                        f"👤 Customer: {buyer_name}\n"
                        f"📍 Location: {location}\n"
                        f"📦 Product: {prod['name']}\n"
                        f"⚖️ Quantity: {qty_kg} KG\n"
                        f"💰 Total Amount: ₹{total_amount:,.2f}\n"
                        f"💳 Payment Mode: {payment_mode}\n"
                        f"--------------------------------\n"
                        f"Thank you for your business! 🙏"
                    )

                    log_entry = {
                        "time": timestamp,
                        "buyer": buyer_name,
                        "phone": buyer_phone,
                        "location": location,
                        "product": prod["name"],
                        "qty": qty_kg,
                        "amount": total_amount,
                        "payment": payment_mode,
                        "msg": whatsapp_msg
                    }
                    st.session_state.export_logs.append(log_entry)

                    st.success(f"✅ ऑर्डर यशस्वीपणे बुक झाली! एकूण बिल: ₹{total_amount:,.2f}")
                    
                    # PDF जनरेट करण्याचे फिचर
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", size=12)
                    pdf.cell(200, 10, txt="SHIVRAJ UNITRADE - INVOICE", ln=True, align="C")
                    pdf.set_font("Arial", size=10)
                    pdf.cell(200, 10, txt="Merchant Exporter India", ln=True, align="C")
                    pdf.ln(10)
                    pdf.cell(200, 8, txt=f"Date: {timestamp}", ln=True)
                    pdf.cell(200, 8, txt=f"Customer Name: {buyer_name}", ln=True)
                    pdf.cell(200, 8, txt=f"Location: {location}", ln=True)
                    pdf.cell(200, 8, txt=f"Product: {prod['name']}", ln=True)
                    pdf.cell(200, 8, txt=f"Quantity: {qty_kg} KG", ln=True)
                    pdf.cell(200, 8, txt=f"Total Amount: Rs. {total_amount:,.2f}", ln=True)
                    pdf.cell(200, 8, txt=f"Payment Mode: {payment_mode}", ln=True)
                    pdf.ln(10)
                    pdf.cell(200, 8, txt="Thank you for your business!", ln=True, align="C")
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin1')

                    col_dl, col_wa = st.columns(2)
                    with col_dl:
                        st.download_button(
                            label="📄 Download PDF Invoice",
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

# --- TAB 3: LOGS WITH SEARCH ---
with tab3:
    st.subheader("All Sales & Dispatch History")
    
    if not st.session_state.export_logs:
        st.info("अद्याप कोणतीही ऑर्डर नोंदवली गेलेली नाही.")
    else:
        search_query = st.text_input("🔍 Search Customer or Location:").strip().lower()

        filtered_logs = [
            log for log in st.session_state.export_logs 
            if search_query in log['buyer'].lower() or search_query in log['location'].lower()
        ]

        if not filtered_logs:
            st.warning("कोणतीही जुळणारी नोंद सापडली नाही.")
        else:
            for i, log in enumerate(reversed(filtered_logs), 1):
                st.markdown(f"""
                **{i}. ट्रान्साक्शन वेळ:** {log['time']}  
                * **कस्टमर:** {log['buyer']} ({log['location']}) — *Ph: {log.get('phone', 'N/A')}*  
                * **प्रॉडक्ट:** {log['product']} — **{log['qty']} KG**  
                * **एकूण रक्कम:** ₹{log['amount']:,.2f}  
                * **पेमेंट प्रकार:** `{log['payment']}`  
                """)
                
                if log.get('phone'):
                    encoded_msg = urllib.parse.quote(log['msg'])
                    wa_url = f"https://wa.me/{log['phone']}?text={encoded_msg}"
                    st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
                
                st.markdown("---")

# --- TAB 4: ADD / REMOVE PRODUCTS (Inventory Management) ---
with tab4:
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
                st.error("❌ कृपया प्रॉडक्ट आयडी आणि नाव दोन्ही भरा!")
            elif new_id in st.session_state.products:
                st.error(f"❌ हा आयडी (`{new_id}`) आधीपासूनच अस्तित्वात आहे!")
            else:
                st.session_state.products[new_id] = {
                    "name": new_name,
                    "price_per_kg": new_price,
                    "stock_kg": new_stock
                }
                st.success(f"✅ नवीन प्रॉडक्ट '{new_name}' यशस्वीपणे ॲड झाला!")
                st.rerun()

    with col_rem:
        st.markdown("### ❌ Remove Existing Product")
        if not st.session_state.products:
            st.info("काढून टाकण्यासाठी कोणताही प्रॉडक्ट उपलब्ध नाही.")
        else:
            with st.form("remove_product_form"):
                rem_options = {f"{p['name']} (ID: {pid})": pid for pid, p in st.session_state.products.items()}
                rem_selected = st.selectbox("Select Product to Delete:", list(rem_options.keys()))
                rem_pid = rem_options[rem_selected]

                remove_btn = st.form_submit_button("Delete Selected Product")

            if remove_btn:
                deleted_name = st.session_state.products[rem_pid]['name']
                del st.session_state.products[rem_pid]
                st.success(f"🗑️ प्रॉडक्ट '{deleted_name}' यशस्वीपणे डिलीट केला गेला!")
                st.rerun()
