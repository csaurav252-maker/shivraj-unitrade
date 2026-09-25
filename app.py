import streamlit as st
import pandas as pd

st.set_page_config(page_title="SHIVRAJ UNITRADE", page_icon="📊", layout="wide")

st.title("SHIVRAJ UNITRADE - Ledger App")

# डेटा सेव्ह ठेवण्यासाठी सेशन स्टेट
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Customer", "Location", "Amount", "Status"])

st.subheader("नवीन ट्रान्झॅक्शन भरा")
with st.form("entry_form", clear_on_submit=True):
    date_val = st.date_input("Date")
    customer = st.text_input("Customer Name")
    location = st.text_input("Location")
    amount = st.number_input("Amount", min_value=0.0)
    status = st.selectbox("Status", ["Pending", "Completed"])
    
    submit_button = st.form_submit_button(label="Add Entry")

    if submit_button:
        if customer.strip() == "":
            st.warning("कृपया कस्टमरचे नाव लिहा!")
        else:
            new_row = pd.DataFrame(
                [[str(date_val), customer, location, amount, status]],
                columns=["Date", "Customer", "Location", "Amount", "Status"]
            )
            st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
            st.success("डेटा यशस्वीरित्या जोडला गेला!")

st.markdown("---")
st.subheader("मागील सर्व ट्रान्झॅक्शन (History)")
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data, use_container_width=True)
    
    # डेटा सुरक्षित ठेवण्यासाठी डाऊनलोड बटण
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download History as Excel (CSV)",
        data=csv,
        file_name='shivraj_unitrade_ledger.csv',
        mime='text/csv',
    )
else:
    st.info("सध्या कोणतीही एंट्री नाही.")
