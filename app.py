import datetime
import urllib.parse
import streamlit as st
import os

# --- PAGE CONFIG WITH LOGO ---
fn_logo_path = "s__2.png"
page_icon_file = fn_logo_path if os.path.exists(fn_logo_path) else "🌐"

st.set_page_config(page_title="Shivraj Unitrade | Merchant Exporter", page_icon=page_icon_file, layout="wide")

# Session State मध्ये स्टॉक आणि लॉग्स जतन करणे
if "products" not in st.session_state:
    st.session_state.products = {
        "EX101": {"name": "Onion Powder (Premium)", "price_per_kg": 350, "stock_kg": 5000},
        "EX102": {"name": "Garlic Powder (Premium)", "price_per_kg": 450, "stock_kg": 3500},
        "EX103": {"name": "Mix Spices Blend (Garam Masala)", "price_per_kg": 600, "stock_kg": 2000},
    }
if "export_logs" not in st.session_state:
    st.session_state.export_logs = []

# --- Professional Header with Exact Logo Image (`s__2.png`) ---
col_logo, col_title = st.columns([1, 6])
with col_logo:
    if os.path.exists("s__2.png"):
        st.image("s__2.png", width=100)
    else:
        st.markdown("<h1>🌐</h1>", unsafe_allow_html=True)
with col_title:
    st.title("SHIVRAJ UNITRADE")
    st.markdown("### *Merchant Exporter India*")

# ब्रँडशी संबंधित ग्लोबल ट्रेड आणि स्पायसेसचा सुंदर फोटो
st.image(
    "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?auto=format&fit=crop&w=1200&q=80",
    caption="Global Export & Quality Spices Hub",
    use_container_width=True
)

st.divider()

tab1, tab2, tab3 = st.tabs(["📦 Live Stock & Inventory", "🛒 New Sales / Export Booking", "📜 Transaction & Dispatch Logs"])

# --- TAB 1: STOCK ---
with tab1:
    st.subheader("Available Warehouse Stock")
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, (pid, p) in enumerate(st.session_state.products.items()):
        with cols[idx % 3]:
            st.info(f"**{p['name']}**\n\n* **ID:** `{pid}`\n* **Rate:** ₹{p['price_per_kg']} / KG\n* **Stock Left:** **{p['stock_kg']} KG**")

# --- TAB 2: BOOKING / SALES ---
with tab2:
    st.subheader("Create New Order / Export Booking")

    with st.form("order_form", clear_on_submit=True):
        buyer_name = st.text_input("Customer / Buyer Name:").strip()
        buyer_phone = st.text_input("Customer WhatsApp Number (with country code, e.g., 9198xxxxxxxx):").strip()
        location = st.text_input("Destination City / Location:").strip()

        # प्रॉडक्ट निवडण्यासाठी पर्याय
        product_options = {f"{v['name']} (₹{v['price_per_kg']}/kg)": k for k, v in st.session_state.products.items()}
        selected_label = st.selectbox("Select Product:", list(product_options.keys()))
        pid = product_options[selected_label]

        qty_kg = st.number_input("Quantity Required (in KG):", min_value=1, value=100, step=10)

        # पेमेंटचे पर्याय (Payment Type)
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
                # हिशोब आणि स्टॉक वजा करणे
                total_amount = prod["price_per_kg"] * qty_kg
                prod["stock_kg"] -= qty_kg  # स्टॉक मधून वजा झाले!

                timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                
                # बिलाचा संदेश तयार करणे
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

                # लॉग रेकॉर्ड तयार करणे
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
                
                # व्हॉट्सॲप डायरेक्ट लिंक तयार करणे
                if buyer_phone:
                    encoded_msg = urllib.parse.quote(whatsapp_msg)
                    wa_url = f"https://wa.me/{buyer_phone}?text={encoded_msg}"
                    st.markdown(f"### 📲 [Click here to send Bill on WhatsApp]({wa_url})", unsafe_allow_html=True)
                else:
                    st.info("💡 जर कस्टमरचा मोबाईल नंबर टाकला असता, तर इथे डायरेक्ट व्हॉट्सॲप बिलाची लिंक आली असती!")

                st.balloons()

# --- TAB 3: LOGS ---
with tab3:
    st.subheader("All Sales & Dispatch History")
    if not st.session_state.export_logs:
        st.info("अद्याप कोणतीही ऑर्डर नोंदवली गेलेली नाही.")
    else:
        for i, log in enumerate(reversed(st.session_state.export_logs), 1):
            st.markdown(f"""
            **{i}. ट्रान्साक्शन वेळ:** {log['time']}  
            * **कस्टमर:** {log['buyer']} ({log['location']}) — *Ph: {log.get('phone', 'N/A')}*  
            * **प्रॉडक्ट:** {log['product']} — **{log['qty']} KG**  
            * **एकूण रक्कम:** ₹{log['amount']:,.2f}  
            * **पेमेंट प्रकार:** `{log['payment']}`  
            """)
            
            # जुन्या ट्रान्साक्शनसाठी देखील व्हॉट्सॲप बटण
            if log.get('phone'):
                encoded_msg = urllib.parse.quote(log['msg'])
                wa_url = f"https://wa.me/{log['phone']}?text={encoded_msg}"
                st.markdown(f"📲 [Send Bill on WhatsApp]({wa_url})")
            
            st.markdown("---")
