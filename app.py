import streamlit as st
import google.generativeai as genai

st.title("🕵️‍♀️ Detektiv-läge")

# 1. Hämta nyckeln
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    st.write(f"Nyckel laddad (slutar på ...{api_key[-4:]})")
except:
    st.error("Ingen nyckel i Secrets!")
    st.stop()

# 2. Konfigurera
genai.configure(api_key=api_key)

# 3. Lista alla modeller
st.write("### Tillgängliga modeller:")

try:
    # Vi ber biblioteket lista allt det ser
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            # Skriv ut det EXAKTA namnet vi måste använda
            st.code(f"model = genai.GenerativeModel('{m.name}')")
            
except Exception as e:
    st.error(f"Kunde inte lista modeller: {e}")
