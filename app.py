import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="SHIVRAJ UNITRADE", page_icon="📊", layout="wide")

st.title("SHIVRAJ UNITRADE - Ledger App")

# गुगल शीट कनेक्शन
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(worksheet="Sheet1", usecols=list(range(5)), ttl=0)
    existing_data = existing_data.dropna(how="all")
except Exception as e:
    st.error("गुगल शीट जोडताना अडचण येत आहे. कृपया Streamlit Secrets मध्ये लिंक तपासा.")
    existing_data = pd.DataFrame(columns=["Date", "Customer", "Location", "Amount", "Status"])

# फॉर्म
st.subheader("नवीन ट्रान्झॅक्शन भरा")
with st.form("entry_form", clear_on_submit=True):
    date_val = st.date_input("Date")
    customer = st.text_input("Customer Name")
    location = st.text_input("Location")
    amount = st.number_input("Amount", min_value=0.0)
    status = st.selectbox("Status", ["Pending", "Completed"])
    
    submit_button = st.form_submit_button(label="Save to Google Sheet")

    if submit_button:
        if customer.strip() == "":
            st.warning("कृपया कस्टमरचे नाव लिहा!")
        else:
            new_row = pd.DataFrame(
                [[str(date_val), customer, location, amount, status]],
                columns=["Date", "Customer", "Location", "Amount", "Status"]
            )
            updated_df = pd.concat([existing_data, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("डेटा यशस्वीरित्या सेव्ह झाला! रिफ्रेश केल्यावरही कायम राहील.")
            st.rerun()

st.markdown("---")
st.subheader("मागील सर्व ट्रान्झॅक्शन (History)")
if not existing_data.empty:
    st.dataframe(existing_data, use_container_width=True)
else:
    st.info("सध्या कोणतीही एंट्री नाही.")
