import streamlit as st
import google.generativeai as genai
import os
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen Åk 9", page_icon="🎓")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad. Lägg in den i Streamlit Secrets!")
    st.stop()

# --- 2. FUNKTION: LÄS PDF ---
def get_pdf_text_smart():
    text_content = ""
    # Läs alla PDF-filer i mappen
    if not os.path.exists('.'):
        return ""
        
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    
    if not pdf_files:
        return ""
    
    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- DOKUMENT: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except:
            continue
    return text_content

# --- 3. LÄS IN KUNSKAPEN ---
pdf_text = get_pdf_text_smart()

# --- 4. MASTER PROMPT (Hjärnan) ---
# Vi lägger detta i systeminstruktionen så den alltid minns vem den är
master_prompt = f"""
DU ÄR "MATTECOACHEN" (Stavat med e).
Du är en pedagogisk mattelärare för årskurs 9.
Presentera dig alltid som "Mattecoachen".

DIN KUNSKAP (Från dina uppladdade filer):
{pdf_text}

DINA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven steg för steg.
2. Använd fakta från texten ovan.
3. Härma stilen från de gamla nationella proven.
4. Stavning: Se till att stava matematiska begrepp korrekt på svenska.

PEDAGOGIK:
Var uppmuntrande men seriös. 
"""

# --- 5. STARTA MODELLEN MED MINNE ---
genai.configure(api_key=api_key)

# Vi sätter instruktionen HÄR istället, så den sitter i "ryggmärgen"
model = genai.GenerativeModel(
    'models/gemini-2.5-flash',
    system_instruction=master_prompt
)

# --- 6. CHATTEN ---
st.title("🎓 Mattecoachen")
st.caption("Din digitala lärare inför NP")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Visa historik på skärmen
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ta emot fråga
if prompt := st.chat_input("Vad behöver du hjälp med?"):
    # 1. Spara användarens fråga
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Bygg upp historiken för AI:n (HÄR ÄR FIXEN!)
    # Vi måste göra om Streamlits historik till Googles format
    gemini_history = []
    for msg in st.session_state.messages:
        # Streamlit heter "assistant", Google vill ha "model"
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # 3. Skicka allt till AI:n
    with st.chat_message("assistant"):
        try:
            # Vi startar chatten med hela historiken inladdad
            chat = model.start_chat(history=gemini_history)
            
            # Eftersom historiken redan innehåller senaste frågan (prompt)
            # via loopen ovan, behöver vi tekniskt sett inte skicka den igen,
            # men Gemini API:t kräver en input för att svara.
            # Vi skickar en tom sträng eller upprepar frågan, men snyggast är
            # att starta chatten med historiken MINUS den sista frågan, 
            # och sen skicka sista frågan nu.
            
            # Så vi backar ett steg i listan vi byggde:
            history_minus_last = gemini_history[:-1] 
            chat = model.start_chat(history=history_minus_last)
            
            response = chat.send_message(prompt)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ett fel uppstod. Försök igen! (Felkod: {e})")
