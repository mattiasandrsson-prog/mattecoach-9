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
    # Vi kollar bara i nuvarande mapp (.)
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
master_prompt = f"""
DU ÄR "MATTECOACHEN" (Stavat med e).
Du är en pedagogisk mattelärare för årskurs 9.
Presentera dig alltid som "Mattecoachen".

DIN KUNSKAP (Från dina uppladdade filer):
{pdf_text}

DINA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven steg för steg.
2. Använd fakta från texten ovan (t.ex. formler för geometri).
3. SKAPA NYA UPPGIFTER: Du SKA generera egna, unika uppgifter när eleven ber om träning.
   - Kopiera inte uppgifter ordagrant från filerna.
   - Hitta på nya siffror och sammanhang, men behåll samma svårighetsgrad och stil som i de gamla proven.
   - Var ärlig: Säg "Här är en uppgift i NP-stil som jag tagit fram åt dig", påstå inte att det är ett specifikt nummer från ett gammalt prov.

4. Stavning: Se till att stava matematiska begrepp korrekt på svenska.

PEDAGOGIK:
Var uppmuntrande men seriös. 
"""

# --- 5. STARTA MODELLEN ---
genai.configure(api_key=api_key)
# Vi använder 2.5 Flash för att den är stabilast med filer
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 6. CHATTEN ---
st.title("🎓 Mattecoachen")
st.caption("Din digitala lärare inför NP")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Visa historik
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ta emot fråga
if prompt := st.chat_input("Vad behöver du hjälp med?"):
    # Spara elevens fråga
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Förbered historik för Google
    gemini_history = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    with st.chat_message("assistant"):
        try:
            # Vi startar chatten med historik utom sista meddelandet
            history_minus_last = gemini_history[:-1]
            chat = model.start_chat(history=history_minus_last)
            
            # Vi skickar Master Prompten osynligt varje gång för att påminna den om reglerna
            full_prompt = master_prompt + "\n\nELEVEN SÄGER: " + prompt
            
            response = chat.send_message(full_prompt)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ett fel uppstod. Försök igen! (Felkod: {e})")
