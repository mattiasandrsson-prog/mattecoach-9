import streamlit as st
import google.generativeai as genai
import os
import re
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen", page_icon="🎓")

# --- DÖLJ REKLAM OCH MENYER (UPPDATERAD CSS) ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* Döljer 'Hosted with Streamlit' */
            .viewerBadge_container__1QSob {display: none;}
            .stAppDeployButton {display: none;}
            [data-testid="stDecoration"] {display: none;}
            [data-testid="stStatusWidget"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad. Lägg in den i Streamlit Secrets!")
    st.stop()

# --- 2. FUNKTION: STÄDA BORT KÄLLHÄNVISNINGAR ---
def clean_text(text):
    # Vi använder ett tryggt sätt att skriva regex för att undvika fel
    pattern = r"\[cite:.*?\]"
    return re.sub(pattern, "", text)

# --- 3. FUNKTION: LÄS PDF (FÖR AI-MINNET) ---
def get_pdf_text_smart():
    text_content = ""
    # Vi kollar bara i nuvarande mapp
    if not os.path.exists('.'): return ""
    
    # Hitta alla PDF-filer utom formelbladet
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and "formelblad" not in f]
    
    if not pdf_files: return ""
    
    for filename in pdf_files:
        try:
            reader = PdfReader(filename)
            text_content += f"\n--- KÄLLA: {filename} ---\n"
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        except: continue
    return text_content

# Läs in all text från PDF:erna när appen startar
pdf_text = get_pdf_text_smart()

# --- 4. SIDOMENY (Med Formelblad som BILDER) ---
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
    
    # --- FORMELBLAD ---
    st.subheader("🧮 Hjälpmedel")
    
    with st.expander("📄 Visa Formelblad"):
        # Kollar om bilderna finns (Sida 1)
        if os.path.exists("formelblad_sida1.png"):
            st.image("formelblad_sida1.png", caption="Sida 1", use_container_width=True)
        
        # Kollar om bilderna finns (Sida 2)
        if os.path.exists("formelblad_sida2.png"):
            st.image("formelblad_sida2.png", caption="Sida 2", use_container_width=True)
            
        # Reservlösning: Om du bara laddat upp en enda bild
        if os.path.exists("formelblad.png") and not os.path.exists("formelblad_sida1.png"):
             st.image("formelblad.png", use_container_width=True)
             
        # Om inga bilder finns
        if not any(f.endswith('.png') for f in os.listdir('.')):
            st.info("Ladda upp 'formelblad_sida1.png' på GitHub för att se det här!")

    st.divider()
    if st.button("Nollställ chatten"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGIK: KOLLA OM ELEVEN BYTT ÄMNE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_topic" not in st.session_state:
    st.session_state.last_topic = selected_topic

# Om eleven byter ämne i menyn -> Rensa historiken
if st.session_state.last_topic != selected_topic:
    st.session_state.messages = []
    st.session_state.last_topic = selected_topic

# --- 6. DYNAMISK PROMPT (Hjärnan) ---
if "Nationella Prov" in selected_topic:
    # LÄGE 1: NP-SIMULATOR
    mission_instruction = """
    DU ÄR EN PROVLEDARE INFÖR NATIONELLA PROVEN (ÅK 9).
    1. Ditt mål är att simulera ett riktigt prov.
    2. Blanda uppgifter från alla områden (Geometri, Algebra, Sannolikhet etc.).
    3. Härma stilen och språkbruket från de gamla proven EXAKT.
    """
    welcome_text = "🏆 **NP-LÄGE:** Nu kör vi! Jag kommer blanda uppgifter från alla områden. Är du redo?"

else:
    # LÄGE 2: ÄMNES-LÄRARE
    mission_instruction = f"""
    DU ÄR EN PEDAGOGISK PRIVATLÄRARE I: {selected_topic.upper()}.
    1. Håll dig strikt till ämnet "{selected_topic}".
    2. Var extra tålmodig och förklara begrepp djupt.
    3. Använd fakta från din bok om just detta område.
    """
    welcome_text = f"📘 **FOKUS: {selected_topic.upper()}**\n\nHej! Jag är redo. Vad vill du börja med?"

# Master Prompten som skickas till AI:n
master_prompt = f"""
DU ÄR "MATTECOACHEN" (Stavat med e).
Du är en pedagogisk mattelärare för årskurs 9.

DIN KUNSKAPSBAS (Från uppladdade filer):
{pdf_text}

GENERELLA REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven steg för steg.
2. Svarar eleven RÄTT -> Ge beröm + En lite svårare fråga.
3. Svarar eleven FEL -> Förklara pedagogiskt + En liknande fråga.
4. SKAPA NYA UPPGIFTER: Hitta på nya tal men behåll "NP-stilen". Säg "Här är en uppgift i NP-stil".

VIKTIGT OM RIT-UPPGIFTER:
Eftersom eleven inte kan rita i chatten:
- Be INTE eleven att rita något om det inte är absolut nödvändigt för förståelsen (t.ex. grafer).
- Om en uppgift normalt kräver ritning, be istället eleven att beskriva med ord eller beräkna egenskaperna direkt.
- Exempel: Istället för "Rita en rektangel med sidorna 5 och 10", säg "Tänk dig en rektangel med sidorna 5 och 10. Vad blir omkretsen?".

TON: Peppande, tydlig och hjälpsam.
"""

# --- 7. STARTA MODELLEN ---
genai.configure(api_key=api_key)
# Vi använder Gemini 2.5 Flash (Snabb & Smart)
model = genai.GenerativeModel('models/gemini-2.5-flash')

# --- 8. CHATT-GRÄNSSNITTET ---
st.title(f"🎓 {selected_topic}")

# Visa välkomstmeddelande om chatten är tom
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})

# Rita ut hela historiken
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Ta emot input från eleven
if prompt := st.chat_input("Skriv här..."):
    # 1. Visa elevens fråga
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Förbered historik för Google (Mappar om formatet)
    gemini_history = []
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # 3. Skicka till AI och visa svar
    with st.chat_message("assistant"):
        try:
            # Vi skickar historiken (minus sista frågan som skickas i send_message)
            history_minus_last = gemini_history[:-1]
            # Initiera chatten med systeminstruktioner
            chat = model.start_chat(history=history_minus_last)
            
            # Skicka en påminnelse om vilket ämne som gäller
            context_reminder = f"[SYSTEM: Eleven är i läget '{selected_topic}'. Håll dig till det.]"
            
            # Vi skickar systeminstruktioner i ett separat "System"-meddelande
            response = chat.send_message(
                str(master_prompt) + "\n\n" + context_reminder + "\n\nSVAR: " + prompt
            )
            
            # Tvätta bort [cite] taggar innan visning
            final_text = clean_text(response.text)
            
            st.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})
        except Exception as e:
            st.error(f"Ett fel uppstod. Försök igen! (Felkod: {e})")
