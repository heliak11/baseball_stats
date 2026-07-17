import google.generativeai as genai
import streamlit as st

# Connexion avec ta clé API
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
