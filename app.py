import streamlit as st
import google.generativeai as genai
import os
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen", page_icon="🎓")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad.")
    st.stop()

# --- 2. LÄS PDF ---
def get_pdf_text_smart():
    text_content = ""
    if not os.path.exists('.'): return ""
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]
    if not pdf_files: return ""
    
    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- KÄLLA: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except: continue
    return text_content

pdf_text = get_pdf_text_smart()

# --- 3. MENY (Nu med NP-val) ---
with st.sidebar:
    st.header("⚙️ Välj fokus")
    
    # Här lägger vi till "Nationella Prov" som ett specifikt val
    selected_topic = st.selectbox(
        "Vad vill du göra idag?",
        [
            "🏆 Nationella Prov (Simulering)",  # <--- NYTT VAL
            "🔢 Taluppfattning",
            "🧮 Algebra & Ekvationer",
            "📐 Geometri",
            "🎲 Sannolikhet & Statistik",
            "📈 Samband & Funktioner"
        ]
    )
    
    st.divider()
    st.caption("Tips: Välj 'Nationella Prov' för att blanda uppgifter och testa dig inför provet.")
    
    if st.button("Nollställ chatten"):
        st.session_state.messages = []
        st.rerun()

# --- 4. DYNAMISK PROMPT (Hjärnan anpassar sig) ---

# Vi kollar vad eleven valde och ändrar instruktionen baserat på det
if "Nationella Prov" in selected_topic:
    # --- LÄGE 1: NP-SIMULATOR ---
    mission_instruction = """
    DU ÄR EN PROVLEDARE INFÖR NATIONELLA PROVEN.
    1. Ditt mål är att simulera ett riktigt prov.
    2. Blanda uppgifter från alla områden (Geometri, Algebra, Sannolikhet etc.).
    3. Härma stilen och språkbruket från de gamla proven EXAKT.
    4. Börja med en E-uppgift, men om eleven svarar rätt, gå snabbt mot C och A-nivå (problemlösning).
    """
    welcome_text = "Hej! Nu kör vi NP-träning. Jag kommer blanda uppgifter från alla områden, precis som på riktigt. Är du redo för första frågan?"

else:
    # --- LÄGE 2: ÄMNES-TUTOR ---
    mission_instruction = f"""
    DU ÄR EN PEDAGOGISK PRIVATLÄRARE I: {selected_topic.upper()}.
    1. Ditt mål är att lära eleven förstå just detta område på djupet.
    2. Håll dig enbart till ämnet "{selected_topic}".
    3. Var extra tålmodig och förklara begrepp om eleven fastnar.
    """
    welcome_text = f"Hej! Då fokuserar vi på **{selected_topic}**. Vad vill du börja med? Eller ska jag ge dig en startuppgift?"

# Den kompletta prompten
master_prompt = f"""
DU ÄR MATTECOACHEN.
{mission_instruction}

DIN KUNSKAPSBAS (Använd alltid denna fakta):
{pdf_text}

GENERELLA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven.
2. Nivåer:
   - E: Procedur/Begrepp.
   - C: Flera steg.
   - A: Resonemang/Generalisering.
3. Om eleven svarar RÄTT -> Ge beröm och öka nivån.
4. Om eleven svarar FEL -> Förklara pedagogiskt och sänk nivån.

TON: Peppande, tydlig och hjälpsam.
"""

# --- 5. STARTA MODELLEN ---
genai.configure(api_key=api_key)
model = genai.GenerativeModel(
    'models/gemini-2.5-flash',
    system_instruction=master_prompt
)

# --- 6. CHATTEN ---
st.title(f"🎓 {selected_topic}")

if "messages" not in st.session_state:
    st.session_state.messages = []
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
            
            # Vi påminner den om vad som är valt
            context_reminder = f"[SYSTEM: Eleven har valt läget: {selected_topic}. Följ instruktionen för detta läge.]"
            
            response = chat.send_message(context_reminder + "\n\nSVAR: " + prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Ett fel uppstod: {e}")
