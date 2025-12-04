import streamlit as st
import google.generativeai as genai
import os
import re
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen Åk 9", page_icon="🎓")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad. Lägg in den i Streamlit Secrets!")
    st.stop()

# --- 2. FUNKTION: STÄDA BORT KÄLLHÄNVISNINGAR ---
def clean_text(text):
    # Vi använder dubbla citattecken här för att undvika syntaxfel
    # Detta tar bort allt som ser ut som
    pattern = r"\"
    return re.sub(pattern, "", text)

# --- 3. FUNKTION: LÄS PDF ---
def get_pdf_text_smart():
    text_content = ""
    # Läs alla PDF-filer i mappen
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- DOKUMENT: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except:
            continue
    return text_content

# --- 4. LÄS IN KUNSKAPEN ---
pdf_text = get_pdf_text_smart()

# --- 5. MASTER PROMPT (Hjärnan) ---
master_prompt = f"""
DU ÄR "MATTECOACHEN" (Stavat med e).
Du är en pedagogisk mattelärare för årskurs 9.
Presentera dig alltid som "Mattecoachen".

DIN KUNSKAP (Från dina uppladdade filer):
{pdf_text}

DINA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven steg för steg.
2. Använd fakta från texten ovan (t.ex. formler för geometri).
3. Härma stilen från de gamla nationella proven.
4. Stavning: Se till att stava matematiska begrepp korrekt på svenska.

PEDAGOGIK:
Var uppmuntrande men seriös. 
"""

# --- 6. STARTA MODELLEN ---
genai.configure(api_key=api_key)
# Vi använder 1.5 Flash för att den är stabilast med filer
model = genai.GenerativeModel('models/gemini-1.5-flash')

# --- 7. CHATTEN ---
st.title("🎓 Mattecoachen")
st.caption("Din digitala lärare inför NP")

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
        try:
            chat = model.start_chat(history=[])
            response = chat.send_message(master_prompt + "\n\nELEVEN FRÅGAR: " + prompt)
            
            # Här tvättar vi svaret innan det visas
            final_text = clean_text(response.text)
            
            st.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})
        except Exception as e:
            st.error(f"Ett fel uppstod. Försök igen! (Felkod: {e})")
