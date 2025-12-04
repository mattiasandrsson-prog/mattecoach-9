import streamlit as st
import google.generativeai as genai
import os
from pypdf import PdfReader

# --- SID-KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen Åk 9", page_icon="🎓")

# --- HÄMTA API-NYCKEL SÄKERT ---
# Vi hämtar nyckeln från Streamlits "kassaskåp" (Secrets) så den inte syns öppet
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittades. Lägg in den i Streamlit Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# --- FUNKTION: LÄS ALLA PDF:ER I SAMMA MAPP ---
def get_all_pdfs_text():
    text_content = ""
    # Hitta alla filer som slutar på .pdf i samma mapp som appen
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        return ""

    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- KÄLLDOKUMENT: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except Exception as e:
            continue
    return text_content

# --- LÄS IN KUNSKAPEN ---
pdf_text = get_all_pdfs_text()

# --- INSTRUKTIONEN TILL AI:N ---
master_prompt = f"""
DU ÄR EN MATTECOACH FÖR ÅRSKURS 9.
Din kunskap baseras på följande text som laddats upp (Sammanfattningar & Gamla NP):
{pdf_text}

REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven.
2. Om eleven frågar om ett begrepp, använd definitionerna från texten ovan.
3. Härma stilen från de gamla nationella proven i texten.
4. Fakta från din bok:
   - Geometri: Area rektangel=b*h, Triangel=(b*h)/2. [cite_start]Cirkel area=pi*r^2 [cite: 377-378].
   - [cite_start]Sannolikhet: P = Gynnsamma/Möjliga [cite: 607-610].
"""

# --- APPENS UTSEENDE ---
st.title("🎓 Mattecoachen Åk 9")
st.caption("Tränad på dina läroböcker och gamla NP")

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
            model = genai.GenerativeModel('gemini-1.5-flash-001')
            chat = model.start_chat(history=[])
            response = chat.send_message(master_prompt + "\n\nELEVEN FRÅGAR: " + prompt)
            message_placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Något gick fel. Felmeddelande: {e}")





