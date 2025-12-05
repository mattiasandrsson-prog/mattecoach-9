import streamlit as st
import google.generativeai as genai
import os
import base64
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen", page_icon="🎓")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad.")
    st.stop()

# --- 2. FUNKTIONER ---

# Läs text från filer (för AI:n)
def get_pdf_text_smart():
    text_content = ""
    if not os.path.exists('.'): return ""
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and "formelblad" not in f] # Undvik att läsa in formelbladet i AI-minnet om du inte vill
    if not pdf_files: return ""
    
    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- KÄLLA: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except: continue
    return text_content

# Visa PDF i rutan (för eleven)
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    # Vi bäddar in PDF:en med HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

pdf_text = get_pdf_text_smart()

# --- 3. MENY ---
with st.sidebar:
    st.header("⚙️ Välj fokus")
    
    selected_topic = st.selectbox(
        "Vad vill du göra idag?",
        [
            "🏆 Nationella Prov (Simulering)",
            "🔢 Taluppfattning",
            "🧮 Algebra & Ekvationer",
            "📐 Geometri",
            "🎲 Sannolikhet & Statistik",
            "📈 Samband & Funktioner"
        ]
    )
    
    st.divider()
    
    # --- HÄR ÄR NYHETEN: VISA PDF ---
    st.subheader("🧮 Hjälpmedel")
    
    # Vi använder en expander så den inte tar plats hela tiden
    with st.expander("📄 Visa Formelblad"):
        if os.path.exists("formelblad.pdf"):
            display_pdf("formelblad.pdf")
        else:
            st.warning("Hittade inte filen 'formelblad.pdf'. Ladda upp den till GitHub!")

    st.divider()
    if st.button("Nollställ chatten"):
        st.session_state.messages = []
        st.rerun()

# --- 4. KOLLA ÄMNESBYTE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_topic" not in st.session_state:
    st.session_state.last_topic = selected_topic

if st.session_state.last_topic != selected_topic:
    st.session_state.messages = []
    st.session_state.last_topic = selected_topic

# --- 5. DYNAMISK PROMPT ---
if "Nationella Prov" in selected_topic:
    mission_instruction = """
    DU ÄR EN PROVLEDARE INFÖR NATIONELLA PROVEN.
    1. Ditt mål är att simulera ett riktigt prov.
    2. Blanda uppgifter från alla områden.
    3. Härma stilen från de gamla proven.
    """
    welcome_text = "🏆 **NP-LÄGE:** Nu kör vi! Jag kommer blanda uppgifter från alla områden (Geometri, Algebra, etc). Är du redo för första frågan?"

else:
    mission_instruction = f"""
    DU ÄR EN PEDAGOGISK PRIVATLÄRARE I: {selected_topic.upper()}.
    1. Håll dig strikt till ämnet "{selected_topic}".
    2. Var extra tålmodig och förklara begrepp djupt.
    3. Använd fakta från din bok om just detta område.
    """
    welcome_text = f"📘 **FOKUS: {selected_topic.upper()}**\n\nHej! Jag är inställd på att bara köra {selected_topic} med dig. Vill du ha en genomgång eller en övningsuppgift?"

master_prompt = f"""
DU ÄR MATTECOACHEN.
{mission_instruction}

DIN KUNSKAPSBAS (Använd alltid denna fakta):
{pdf_text}

GENERELLA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven.
2. Svarar eleven RÄTT -> Ge beröm + Svårare fråga.
3. Svarar eleven FEL -> Förklara + Enklare fråga.

TON: Peppande, tydlig och hjälpsam.
"""

# --- 6. STARTA MODELLEN ---
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    'models/gemini-2.5-flash',
    system_instruction=master_prompt
)

# --- 7. CHATTEN ---
st.title(f"🎓 {selected_topic}")

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Skriv ditt svar eller din fråga här..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    gemini_history = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    with st.chat_message("assistant"):
        try:
            history_minus_last = gemini_history[:-1]
            chat = model.start_chat(history=history_minus_last)
            
            context_reminder = f"[SYSTEM: Eleven är i läget '{selected_topic}'. Håll dig till det.]"
            
            response = chat.send_message(context_reminder + "\n\nSVAR: " + prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ett fel uppstod: {e}")
