import streamlit as st
import google.generativeai as genai
import os
import re
import matplotlib.pyplot as plt
import numpy as np
from pypdf import PdfReader

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Mattecoachen", page_icon="🎓")

try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("Ingen API-nyckel hittad. Lägg in den i Streamlit Secrets!")
    st.stop()

# --- 2. FUNKTIONER FÖR TEXT & GRAFER ---

def clean_text(text):
    # Tar bort källhänvisningar [cite:...]
    text = re.sub(r'\[cite:.*?\]', '', text)
    # Tar bort graf-kommandot så det inte syns i texten
    text = re.sub(r'\[GRAPH:.*?\]', '', text)
    return text

def extract_graph_command(text):
    # Letar efter kommandon som [GRAPH: y=2x+1]
    match = re.search(r'\[GRAPH: (.*?)\]', text)
    if match:
        return match.group(1)
    return None

def plot_function(equation):
    # En enkel grafritare
    try:
        x = np.linspace(-10, 10, 400)
        # Snygga till ekvationen för Python (t.ex. 2x -> 2*x)
        eq_clean = equation.replace("y=", "").replace(" ", "").replace("^", "**")
        eq_clean = re.sub(r'(\d)x', r'\1*x', eq_clean)
        
        y = eval(eq_clean)
        
        fig, ax = plt.subplots()
        ax.plot(x, y, label=f"y={eq_clean.replace('*', '')}")
        ax.axhline(0, color='black', linewidth=1)
        ax.axvline(0, color='black', linewidth=1)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.set_xlabel("x")
        ax.set_ylabel("y")
        ax.legend()
        return fig
    except:
        return None

# --- 3. LÄS PDF (FÖR AI-MINNET) ---
def get_pdf_text_smart():
    text_content = ""
    if not os.path.exists('.'): return ""
    
    # Läs alla PDF:er utom formelbladet till minnet
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

pdf_text = get_pdf_text_smart()

# --- 4. MENY ---
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
    
    # --- FORMELBLAD (VISAR BILDER) ---
    st.subheader("🧮 Hjälpmedel")
    
    with st.expander("📄 Visa Formelblad"):
        if os.path.exists("formelblad_sida1.png"):
            st.image("formelblad_sida1.png", caption="Sida 1", use_container_width=True)
        if os.path.exists("formelblad_sida2.png"):
            st.image("formelblad_sida2.png", caption="Sida 2", use_container_width=True)
            
        # Reservlösning
        if os.path.exists("formelblad.png") and not os.path.exists("formelblad_sida1.png"):
             st.image("formelblad.png", use_container_width=True)
             
        if not any(f.endswith('.png') for f in os.listdir('.')):
            st.info("Inga bilder uppladdade än.")

    st.divider()
    if st.button("Nollställ chatten"):
        st.session_state.messages = []
        st.rerun()

# --- 5. LOGIK: KOLLA OM ELEVEN BYTT ÄMNE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "last_topic" not in st.session_state:
    st.session_state.last_topic = selected_topic

if st.session_state.last_topic != selected_topic:
    st.session_state.messages = []
    st.session_state.last_topic = selected_topic

# --- 6. DYNAMISK PROMPT (Hjärnan) ---
if "Nationella Prov" in selected_topic:
    mission_instruction = """
    DU ÄR EN PROVLEDARE INFÖR NATIONELLA PROVEN.
    1. Simulera ett riktigt prov. Blanda områden.
    2. Härma stilen från de gamla proven.
    """
    welcome_text = "🏆 **NP-LÄGE:** Nu kör vi! Jag kommer blanda uppgifter. Är du redo?"
else:
    mission_instruction = f"""
    DU ÄR EN PEDAGOGISK PRIVATLÄRARE I: {selected_topic.upper()}.
    1. Håll dig till ämnet "{selected_topic}".
    2. Var extra tålmodig.
    """
    welcome_text = f"📘 **FOKUS: {selected_topic.upper()}**\n\nHej! Jag är redo. Vad vill du börja med?"

master_prompt = f"""
DU ÄR "MATTECOACHEN".
Du är en pedagogisk mattelärare för årskurs 9.

DIN KUNSKAPSBAS (Från filer):
{pdf_text}

REGLER:
1. Ge aldrig svaret direkt. Lotsa eleven.
2. Svarar eleven RÄTT -> Ge beröm + En lite svårare fråga.
3. Svarar eleven FEL -> Förklara pedagogiskt + En liknande fråga.
4. SKAPA NYA UPPGIFTER: Hitta på nya tal men behåll "NP-stilen". Säg "Här är en uppgift i NP-stil".

GRAFER:
Om du ska visa en linjär funktion (y=kx+m), skriv kommandot:
[GRAPH: y=2x+1]
(Byt ut siffrorna. Endast linjära funktioner).

VIKTIGT OM RIT-UPPGIFTER:
- Be INTE eleven att rita något om det inte är absolut nödvändigt.
- Be istället eleven beskriva eller beräkna egenskaperna.

TON: Peppande, tydlig och hjälpsam.
"""

# --- 7. STARTA MODELLEN ---
genai.configure(api_key=api_key)
# Vi använder Gemini 2.5 Flash
model = genai.GenerativeModel('models/gemini-2.5-flash', system_instruction=master_prompt)

# --- 8. CHATT-GRÄNSSNITTET ---
st.title(f"🎓 {selected_topic}")

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": welcome_text})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Skriv här..."):
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
            
            context_reminder = f"[SYSTEM: Eleven är i läget '{selected_topic}'.]"
            
            response = chat.send_message(context_reminder + "\n\nSVAR: " + prompt)
            
            # 1. Kolla om AI vill rita en graf
            graph_cmd = extract_graph_command(response.text)
            
            # 2. Tvätta texten
            final_text = clean_text(response.text)
            st.markdown(final_text)
            
            # 3. Rita grafen om beordrad
            if graph_cmd:
                fig = plot_function(graph_cmd)
                if fig:
                    st.pyplot(fig)
            
            st.session_state.messages.append({"role": "assistant", "content": final_text})
            
        except Exception as e:
            st.error(f"Ett fel uppstod. Försök igen! (Felkod: {e})")
