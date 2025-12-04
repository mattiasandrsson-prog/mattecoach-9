import streamlit as st
import google.generativeai as genai
import os
import re
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen Åk 9", page_icon="🎓")

# Hämta API-nyckeln säkert från Secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen nyckel hittad! Lägg in den i Streamlit Secrets.")
    st.stop()

# --- 2. FUNKTION: LÄS ALLA PDF:ER I SAMMA MAPP ---
def get_all_pdfs_text():
    text_content = ""
    # Hitta alla filer som slutar på .pdf i nuvarande mapp (.)
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        return ""

    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- DOKUMENT: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            continue
            
    return text_content

# --- 3. LÄS IN KUNSKAPEN ---
pdf_text = get_all_pdfs_text()

# --- 4. INSTRUKTIONEN (Hjärnan) ---
# Här kombinerar vi din PDF-text med strikta regler
master_prompt = f"""
DU ÄR EN MATTECOACH FÖR ÅRSKURS 9.
Du har tillgång till följande kursmaterial (Sammanfattningar & Gamla Prov):
{pdf_text}

REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven.
2. [cite_start]Använd fakta från texten ovan (t.ex. formler för geometri eller sannolikhet [cite: 336-352, 607-610]).
3. Härma stilen från de gamla nationella proven när du skapar uppgifter.
"""

# --- 5. STARTA AI-MODELLEN ---
genai.configure(api_key=api_key)

# Vi använder den nya modellen du hittade i listan!
try:
    # Denna är snabb och smart (från din lista)
    model = genai.GenerativeModel('models/gemini-2.5-flash') 
except:
    # Reservplan
    model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

# --- 6. CHATTEN ---
st.title("🎓 Mattecoachen Åk 9")
st.caption(f"Läste in {len([f for f in os.listdir('.') if f.endswith('.pdf')])} st PDF-filer.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Vad behöver du hjälp med?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            chat = model.start_chat(history=[])
            # Vi skickar prompten + elevens fråga
            response = chat.send_message(master_prompt + "\n\nELEVEN FRÅGAR: " + prompt)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Något gick fel (oftast för mycket text). Försök igen om en minut! Fel: {e}")


