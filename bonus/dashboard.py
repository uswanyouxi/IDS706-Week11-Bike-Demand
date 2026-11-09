"""Multipage wrapper keeps the original Part 2 page byte-for-byte unchanged."""
import streamlit as st
page=st.navigation([
    st.Page("/opt/project/dashboard/app.py",title="Verified Part 2",icon=":material/check_circle:"),
    st.Page("/opt/project/bonus/view.py",title="Optional Part 3",icon=":material/account_tree:",default=True)])
page.run()
