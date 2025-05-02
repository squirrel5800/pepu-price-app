
import streamlit as st
import requests

# --- MUST BE FIRST ---
st.set_page_config(page_title="PEPU Tracker", page_icon="🐸", layout="centered")

# --- Settings ---
TOKEN_NAME = "PEPU"
TOKEN_HOLDINGS = 23955151
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/pairs/ethereum/0x3ebec0a1b4055c8d1180fce64db2a8c068170880"

st.title("🐸 PEPU Price Tracker")
st.markdown("Live tracking of your PEPU token holdings and total USD value.")

if st.button("🔁 Refresh Price"):
    try:
        response = requests.get(DEXSCREENER_API)
        data = response.json()
        price = float(data['pair']['priceUsd'])
        total_value = price * TOKEN_HOLDINGS

        st.metric(label="Current PEPU Price", value=f"${price:.6f}")
        st.metric(label="Your Holdings", value=f"{TOKEN_HOLDINGS:,} PEPU")
        st.metric(label="Total Value (USD)", value=f"${total_value:,.2f}")
    except Exception as e:
        st.error("Failed to fetch price data.")
        st.exception(e)
else:
    st.info("Click the button above to fetch the latest PEPU price.")

st.caption("Powered by Dexscreener API")
