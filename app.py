import datetime
import streamlit as st

st.set_page_config(page_title="Shivraj United | Export Pro", page_icon="🌶️", layout="wide")

if "products" not in st.session_state:
    st.session_state.products = {
        "EX101": {"name": "Onion Powder (Premium)", "price_per_kg": 350, "stock_kg": 5000},
        "EX102": {"name": "Garlic Powder (Premium)", "price_per_kg": 450, "stock_kg": 3500},
        "EX103": {"name": "Mix Spices Blend (Garam Masala)", "price_per_kg": 600, "stock_kg": 2000},
    }
if "export_logs" not in st.session_state:
    st.session_state.export_logs = []

USD_RATE = 84.0

st.title("🌶️ SHIVRAJ UNITED")
st.subheader("Spices & Powder Export Management System")
st.caption("📍 Operational Hub: Nagpur HQ ⇄ Malkapur Unit")
st.divider()

tab1, tab2, tab3 = st.tabs(["📦 Stock & Inventory", "✈️ Create Export Shipment", "📜 Shipment History Logs"])

with tab1:
    st.subheader("Current Available Stock for Export")
    col1, col2, col3 = st.columns(3)
    cols = [col1, col2, col3]

    for idx, (pid, p) in enumerate(st.session_state.products.items()):
        with cols[idx % 3]:
            st.info(f"**{p['name']}**\n\n* **Product ID:** `{pid}`\n* **Price:** ₹{p['price_per_kg']} / KG\n* **Available Stock:** {p['stock_kg']} KG")

with tab2:
    st.subheader("Generate International / Domestic Invoice")

    with st.form("shipment_form", clear_on_submit=True):
        buyer_name = st.text_input("Buyer Company Name:").strip()
        destination_country = st.text_input("Destination Country / City (e.g., Dubai, USA, Mumbai):").strip()

        product_options = {v["name"]: k for k, v in st.session_state.products.items()}
        selected_prod_name = st.selectbox("Select Product to Export:", list(product_options.keys()))
        pid = product_options[selected_prod_name]

        qty_kg = st.number_input("Order Quantity (in KG):", min_value=1, step=50)
        currency = st.selectbox("Invoice Currency:", ["INR (₹)", "USD ($)"])

        submit_btn = st.form_submit_button("Book & Generate Export Invoice")

    if submit_btn:
        try:
            if not buyer_name or not destination_country:
                raise ValueError("Buyer Name and Destination Country fields cannot be empty.")

            prod = st.session_state.products[pid]
            if qty_kg > prod["stock_kg"]:
                raise ValueError(f"Insufficient stock for export! Only {prod['stock_kg']} KG of {prod['name']} available.")

            total_inr = prod["price_per_kg"] * qty_kg
            total_usd = total_inr / USD_RATE

            prod["stock_kg"] -= qty_kg

            timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            if currency == "USD ($)":
                final_amt_str = f"${total_usd:.2f} USD"
            else:
                final_amt_str = f"₹{total_inr:,.2f} INR"

            record = f"{timestamp} | {buyer_name} ({destination_country}) | {prod['name']} x {qty_kg}KG | Total: {final_amt_str}"
            st.session_state.export_logs.append(record)

            st.success(f"✈️ Export Shipment Confirmed for Shivraj United! Invoice Total: {final_amt_str}")
            st.balloons()

        except ValueError as e:
            st.error(f"❌ Input Validation Error: {str(e)}")
        except Exception as e:
            st.error(f"⚠️ System Error occurred: {str(e)}")

with tab3:
    st.subheader("Shivraj United - Global Dispatch Log Book")
    if not st.session_state.export_logs:
        st.info("No shipments booked today.")
    else:
        st.text_area(
            label="Malkapur Trading Hub Outgoing Logs",
            value="\n".join(st.session_state.export_logs),
            height=250,
            disabled=True
        )