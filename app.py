import streamlit as st
import os
import time
import json
from datetime import datetime
import random

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Quiz dell'amore ❤️",
    page_icon="💌",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS DA FILE ESTERNO ---
def local_css():
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        css = ""

    # Inject CSS separately
    st.markdown("<style>" + css + "</style>", unsafe_allow_html=True)

    # Floating hearts — wrapped in a fixed container so they don't affect page flow
    st.markdown("""
        <div style="position:fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:-1; overflow:hidden;">
            <div class="heart-bg"></div>
            <div class="heart-bg"></div>
            <div class="heart-bg"></div>
            <div class="heart-bg"></div>
            <div class="heart-bg"></div>
            <div class="heart-bg"></div>
        </div>
    """, unsafe_allow_html=True)

local_css()

# --- FUNZIONE PER MOSTRARE FOTO RICORDO ---
def show_memory_photo(photo_filename, caption_text):
    """Mostra una foto ricordo con animazione dopo risposta corretta"""
    st.markdown("<div class='memory-photo fade-in'>", unsafe_allow_html=True)
    
    if os.path.exists(photo_filename):
        st.image(photo_filename, caption=caption_text, use_container_width=True)
    else:
        st.warning(f"📷 Carica la foto: `{photo_filename}`")
        st.info(f"💡 Questa è la foto che apparirà per: {caption_text}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- FUNZIONE TYPEWRITER ---
def typewriter_clean(text: str, speed: float = 0.04):
    placeholder = st.empty()
    displayed_text = ""
    
    style = """
        font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 1.15rem;
        color: #2d3436;
        line-height: 1.6;
        white-space: pre-wrap; 
    """
    
    for char in text:
        displayed_text += char
        placeholder.markdown(f"<div style='{style}'>{displayed_text}</div>", unsafe_allow_html=True)
        time.sleep(speed)
    
    return placeholder

# --- CARICAMENTO IMMAGINI CON FALLBACK ---
def safe_image(url_or_path, caption, **kwargs):
    """Mostra un'immagine con fallback graceful in caso di errore"""
    try:
        st.image(url_or_path, caption=caption, **kwargs)
    except Exception:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #ffecd2, #fcb69f); 
                        padding: 40px 20px; border-radius: 15px; text-align: center;
                        color: #c0392b; font-weight: 600;">
                🖼️ {caption}<br>
                <span style="font-size: 0.8rem; color: #999;">(Immagine non disponibile)</span>
            </div>
        """, unsafe_allow_html=True)

# --- PERSISTENZA STATO (JSON) ---
STATE_FILE = os.path.join(os.path.dirname(__file__), "quiz_state.json")

def save_state():
    """Salva lo stato corrente su file JSON"""
    state_to_save = {
        "step": st.session_state.get("step", 0),
        "attempts": st.session_state.get("attempts", {}),
        "hints_used": st.session_state.get("hints_used", 0),
        "perfect_score": st.session_state.get("perfect_score", True),
        "show_photo": st.session_state.get("show_photo", {}),
        "hints_shown": {k: v for k, v in st.session_state.items() if k.startswith("hint_shown_")},
        "start_time": st.session_state.get("start_time", datetime.now()).isoformat(),
    }
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_state():
    """Carica lo stato da file JSON se esiste"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            st.session_state.step = saved.get("step", 0)
            st.session_state.attempts = saved.get("attempts", {})
            st.session_state.hints_used = saved.get("hints_used", 0)
            st.session_state.perfect_score = saved.get("perfect_score", True)
            st.session_state.show_photo = saved.get("show_photo", {})
            st.session_state.start_time = datetime.fromisoformat(saved.get("start_time", datetime.now().isoformat()))
            for k, v in saved.get("hints_shown", {}).items():
                st.session_state[k] = v
            return True
        except Exception:
            return False
    return False

def clear_saved_state():
    """Cancella il file di stato salvato"""
    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except Exception:
            pass

# --- GESTIONE STATO ---
if 'initialized' not in st.session_state:
    clear_saved_state()  # Always start fresh on new run
    st.session_state.step = 0  # Step 0 = Welcome screen
    st.session_state.attempts = {}
    st.session_state.start_time = datetime.now()
    st.session_state.hints_used = 0
    st.session_state.perfect_score = True
    st.session_state.show_photo = {}
    st.session_state.initialized = True

# Ensure all keys exist (in case loaded state is from an older version)
if 'step' not in st.session_state:
    st.session_state.step = 0
if 'attempts' not in st.session_state:
    st.session_state.attempts = {}
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()
if 'hints_used' not in st.session_state:
    st.session_state.hints_used = 0
if 'perfect_score' not in st.session_state:
    st.session_state.perfect_score = True
if 'show_photo' not in st.session_state:
    st.session_state.show_photo = {}

def go_next():
    st.session_state.step += 1
    save_state()
    time.sleep(0.3)
    st.rerun()

def track_attempt(step_name, correct=False):
    if step_name not in st.session_state.attempts:
        st.session_state.attempts[step_name] = 0
    if not correct:
        st.session_state.attempts[step_name] += 1
        st.session_state.perfect_score = False
    save_state()

def show_hint(hint_text, step_key):
    """Mostra un aiutino — incrementa il contatore solo una volta per step"""
    if st.button("💡 Aiutino?", key=f"hint_btn_{step_key}"):
        flag = f"hint_shown_{step_key}"
        if flag not in st.session_state:
            st.session_state.hints_used += 1
            st.session_state[flag] = True
            save_state()
        st.markdown(f"<div class='hint-box'>💭 {hint_text}</div>", unsafe_allow_html=True)

# --- BARRA PROGRESSO ---
total_steps = 9  # Steps 1-9, step 0 is welcome, step 10 is finale
if st.session_state.step > 0 and st.session_state.step <= total_steps:
    progress = st.session_state.step / total_steps
    col_prog1, col_prog2 = st.columns([4, 1])
    with col_prog1:
        st.progress(progress)
    with col_prog2:
        st.markdown(f"<div style='text-align: right; color: #666;'>{st.session_state.step}/{total_steps}</div>", unsafe_allow_html=True)

# =============================================================================
# STEP 0: WELCOME SCREEN
# =============================================================================
if st.session_state.step == 0:
    st.markdown("")
    st.markdown("")
    st.markdown("<div class='welcome-heart'>💕</div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-title'>Love Quiz</div>", unsafe_allow_html=True)
    st.markdown("<div class='welcome-subtitle'>Un quiz speciale, fatto con il cuore, solo per te.</div>", unsafe_allow_html=True)
    
    st.markdown("")
    st.markdown("")
    
    col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
    with col_w2:
        st.markdown("""
            <div style="text-align: center; color: #576574; font-size: 1rem; 
                        background: rgba(255, 159, 243, 0.1); border-radius: 15px; 
                        padding: 20px; margin-bottom: 20px;">
                Rispondi alle domande dischetto...<br>
                Ci saranno <b>9 sfide</b> da superare! 🌹
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("❤️ Cominciamo botolina!", key="start_quiz", use_container_width=True):
            st.session_state.start_time = datetime.now()
            go_next()

# =============================================================================
# STEP 1: CITTÀ - Dove tutto è cominciato
# =============================================================================
elif st.session_state.step == 1:
    st.title("🏙️ La città dove tutto è cominciato")
    st.write("**Partiamo dalle domande semplici, dove è cominciato tutto?**")
    
    show_hint("Legame particolare con Chieti... 💕", "step1")
    
    col1, col2 = st.columns(2)
    
    # MODIFICA QUESTE CITTÀ CON LE TUE
    citta_options = {
        "Atina": "https://www.lazionascosto.it/wp-content/uploads/2024/11/atina-med.jpg",
        "Vasto": "https://s1.immobiliare.it/news/app/uploads/2024/11/Vasto-dove-si-trova-e-cosa-vedere-590x393-jpeg.webp",
        "Pescara": "https://italien.expert/wp-content/uploads/2024/09/Pescara-Abruzzen-Italien-4.jpg",
        "Chieti": "https://images.unsplash.com/photo-1604616856815-3426f08a70c5?q=80&w=870&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    }
    
    # MODIFICA QUI LA CITTÀ CORRETTA
    citta_corretta = "Pescara"
    
    cities = list(citta_options.items())
    
    with col1:
        for i in range(0, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city1_{i}"):
                if city_name == citta_corretta:
                    track_attempt("step1", correct=True)
                    st.toast(f"Fregt se è giusta! {citta_corretta}!", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    go_next()
                else:
                    track_attempt("step1", correct=False)
                    st.toast("Nope!", icon="❌")
    
    with col2:
        for i in range(1, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city1_{i}"):
                if city_name == citta_corretta:
                    track_attempt("step1", correct=True)
                    st.toast(f"Esatto! {citta_corretta}! ❤️", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    go_next()
                else:
                    track_attempt("step1", correct=False)
                    st.toast("Non è questa!", icon="❌")

# =============================================================================
# STEP 2: CITTÀ - Primo weekend
# =============================================================================
elif st.session_state.step == 2:
    st.title("✈️ Il nostro primo viaggio insieme")
    st.write("**Cosa mi è piaciuto di più del nostro viaggio a Valencia?**")
    
    show_hint("Tips...", "step2")
    
    col1, col2 = st.columns(2)
    
    # MODIFICA QUESTE CITTÀ
    citta_options = {
        "Cibo": "https://www.lovevalencia.com/wp-content/uploads/2012/11/Mercado_Central-p-61.jpg",
        "Oceanografico": "https://familygo.b-cdn.net/wp-content/uploads/2023/10/oceanografico-valencia-tunnel2-foto-manuela-rosellini.jpg",
        "Mare": "https://img.nh-hotels.net/1zb3d/RjYyZ/original/Valencia_promenade_Malvarrosa.jpg",
        "La stanza d'hotel": "https://lh3.googleusercontent.com/p/AF1QipN1gGrz9sBhbUYMgtCU5mZnvsR5uVCKImHEW4O1=s220-w165-h220-n-k-no"
    }
    
    # MODIFICA QUI LA CITTÀ CORRETTA
    citta_corretta = "Oceanografico"
    
    cities = list(citta_options.items())
    
    with col1:
        for i in range(0, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city2_{i}"):
                if city_name == citta_corretta:
                    st.session_state.show_photo['step2'] = True
                    track_attempt("step2", correct=True)
                    st.toast(f"Sì! {citta_corretta}! ", icon="✅")
                    st.balloons()
                    time.sleep(1)
                else:
                    track_attempt("step2", correct=False)
                    st.toast("Riprova!", icon="❌")
    
    with col2:
        for i in range(1, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city2_{i}"):
                if city_name == citta_corretta:
                    st.session_state.show_photo['step2'] = True
                    track_attempt("step2", correct=True)
                    st.toast(f"Sì! {citta_corretta}! ", icon="✅")
                    st.balloons()
                    time.sleep(1)
                else:
                    track_attempt("step2", correct=False)
                    st.toast("Riprova!", icon="❌")
    
    # Mostra foto ricordo
    if st.session_state.show_photo.get('step2', False):
        st.write("---")
        st.markdown("### Fochette indimenticabili...")
        show_memory_photo("foto_step_2.jpeg", "Il nostro primo viaggio")
        
        if st.button("➡️ Continua", key="next_step2"):
            go_next()

# =============================================================================
# STEP 3: CITTÀ - Città dei sogni
# =============================================================================
elif st.session_state.step == 3:
    st.title("Città dove vorremmo vivere insieme")
    st.write("**Seleziona la città dove vorremmo vivere insieme**")
    
    show_hint("Non Padova...", "step3")
    
    col1, col2 = st.columns(2)
    
    # MODIFICA QUESTE CITTÀ
    citta_options = {
        "Padova": "https://vadointheratrip.com/wp-content/uploads/2021/01/palazzo-della-ragione-piazza-delle-erbe-Padova-1140x660.jpg",
        "Frosinone": "https://www.italia.it/content/dam/tdh/it/destinations/lazio/frosinone/media/google/image3.jpeg",
        "Los Angeles": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/69/Los_Angeles_with_Mount_Baldy.jpg/330px-Los_Angeles_with_Mount_Baldy.jpg",
        "Pescara": "https://images.winalist.com/blog/wp-content/uploads/2025/06/02151452/adobestock-471387314.jpeg"
    }
    
    # MODIFICA QUI LA CITTÀ CORRETTA
    citta_corretta = "Pescara"
    
    cities = list(citta_options.items())
    
    with col1:
        for i in range(0, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city3_{i}"):
                if city_name == citta_corretta:
                    track_attempt("step3", correct=True)
                    st.toast(f"Esatto! {citta_corretta}! 🌴", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    go_next()
                else:
                    track_attempt("step3", correct=False)
                    st.toast("Non quella!", icon="❌")
    
    with col2:
        for i in range(1, len(cities), 2):
            city_name, city_img = cities[i]
            safe_image(city_img, city_name, use_container_width=True)
            if st.button(f"Scegli {city_name}", key=f"city3_{i}"):
                if city_name == citta_corretta:
                    track_attempt("step3", correct=True)
                    st.toast(f"Esatto! {citta_corretta}! 🌴", icon="✅")
                    st.balloons()
                    time.sleep(1)
                    go_next()
                else:
                    track_attempt("step3", correct=False)
                    st.toast("Non quella!", icon="❌")

# =============================================================================
# STEP 4: Cani
# =============================================================================
elif st.session_state.step == 4:
    st.title("Devozione e cani 🐶")
    st.write("In termini di devozione, quale di questi è il doggo più devoto?")
    
    show_hint("Poldo... 🦴", "step4")
    
    col1, col2 = st.columns(2)
    img1 = "https://images.unsplash.com/photo-1517849845537-4d257902454a?w=300"
    img2 = "https://www.ioeilmioanimale.com/wp-content/uploads/2015/07/bovaro-bernese-domande.jpg"
    img3 = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/11.10.2015_Samoyed_%28cropped%29.jpg/1280px-11.10.2015_Samoyed_%28cropped%29.jpg"
    img4 = "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=300"

    with col1:
        safe_image(img1, "Bulldog", use_container_width=True)
        if st.button("Scegli Bulldog", key="dog1"): 
            track_attempt("step4", correct=False)
            st.toast("Assolutamente no!", icon="❌")
            
        safe_image(img3, "Succhetto", use_container_width=True)
        if st.button("Scegli Succhetto", key="dog3"): 
            track_attempt("step4", correct=False)
            st.toast("No! Ma vicino!", icon="❌")

    with col2:
        safe_image(img2, "Poldo", use_container_width=True)
        if st.button("Scegli Poldo", key="dog2"):
            track_attempt("step4", correct=True)
            st.toast("La devozione fatta cane!", icon="✅")
            st.balloons()
            time.sleep(1)
            go_next()
            
        safe_image(img4, "Beagle", use_container_width=True)
        if st.button("Scegli Beagle", key="dog4"): 
            track_attempt("step4", correct=False)
            st.toast("Troppo casino!", icon="❌")
    
# =============================================================================
# STEP 5: Slider
# =============================================================================
elif st.session_state.step == 5:
    st.title("Da 0 a 100 quante coccole mi farai appena ci rivedremo?")
    st.write("Attendo con impazienza...")
    
    valore = st.slider("Livello:", 0, 100, 50, key="love_slider")
    
    if valore < 50:
        emoji = "😢"
        msg = "Non mi ami più?!"
    elif valore < 80:
        emoji = "🤔"
        msg = "Mmm... si può fare di più!"
    elif valore < 100:
        emoji = "😊"
        msg = "Quasi perfetto..."
    else:
        emoji = "😍"
        msg = "L'amore regna!"
    
    st.markdown(f"<div style='text-align: center; font-size: 2rem;'>{emoji} {msg}</div>", unsafe_allow_html=True)
    
    if st.button("Conferma", key="step5_btn"):
        if valore == 100:
            track_attempt("step5", correct=True)
            st.toast("Risposta corretta! ❤️", icon="✅")
            st.balloons()
            time.sleep(1)
            go_next()
        else:
            track_attempt("step5", correct=False)
            st.toast("Solo?? Metti 100!", icon="❌")

# =============================================================================
# STEP 6: Radio Button
# =============================================================================
elif st.session_state.step == 6:
    st.title("Titolo nobiliare")
    st.write("Qual è il mio titolo nobiliare preferito?")
    
    show_hint("Non è dottore bis!", "step6")
    
    opzioni = ["Sir botulus", "Stupido botolo", "Botolo", "Dottore bis"]
    scelta = st.radio("Scegli:", opzioni, index=None, key="song_radio")
    
    if st.button("Verifica", key="step6_btn"):
        if scelta == "Botolo":
            st.session_state.show_photo['step6'] = True
            track_attempt("step6", correct=True)
            st.toast("L'unico e inimitabile!", icon="✅")
            st.balloons()
            time.sleep(1)
        elif scelta:
            track_attempt("step6", correct=False)
            st.toast("No!", icon="❌")
    
    # Mostra foto ricordo
    if st.session_state.show_photo.get('step6', False):
        st.write("---")
        st.markdown("### 💕 L'autore...")
        show_memory_photo("foto_step6.jpeg", "Me")
        
        if st.button("➡️ Continua", key="next_step6"):
            go_next()

# =============================================================================
# STEP 7: Ricordi
# =============================================================================
elif st.session_state.step == 7:
    st.title("Completa la frase")
    st.write("Non lungo che tocchi, non largo che tappi...?")
    
    show_hint("Gennari docet...", "step7")
    
    opzioni = [
        "ma giusto che passi!",
        "ma stretto che abbracci!",
        "ma dritto che serva!",
        "ma duro che duri!"
    ]
    
    scelta = st.radio("Le mie parole:", opzioni, index=None, key="memory_radio")
    
    if st.button("Conferma", key="step7_btn"):
        if scelta == "ma duro che duri!":
            track_attempt("step7", correct=True)
            st.toast("Gennari sarebbe fiero! 🥰", icon="✅")
            st.balloons()
            time.sleep(1)
            go_next()
        elif scelta:
            track_attempt("step7", correct=False)
            st.toast("Poche idee, ma confuse!", icon="❌")
    
# =============================================================================
# STEP 8: Password
# =============================================================================
elif st.session_state.step == 8:
    st.title("Password 🔐")
    st.write("Qual è il mio soprannome preferito per te?")
    
    show_hint("Semplice e dolce", "step8")
    
    pw = st.text_input("Password:", type="password", key="password_input")
    
    if st.button("Sblocca", key="step8_btn"):
        if pw.lower().strip() in ["amore", "tips", "botola", "disco"]:
            st.session_state.show_photo['step8'] = True
            track_attempt("step8", correct=True)
            st.balloons()
            time.sleep(1)
        else:
            track_attempt("step8", correct=False)
            st.toast("Accesso Negato!", icon="❌")
    
    # Mostra foto ricordo
    if st.session_state.show_photo.get('step8', False):
        st.write("---")
        st.markdown("### 💕 La mia persona speciale...")
        show_memory_photo("foto_step8.jpeg", "Mio amori")
        
        if st.button("➡️ Al Finale! 🎉", key="next_step8"):
            go_next()

# =============================================================================
# STEP 9: Dedica della canzone
# =============================================================================
elif st.session_state.step == 9:
    st.title("La canzone del disco")
    st.write("**Quale canzone è dedicata a te?**")
    
    show_hint("La sua voce ha ispirato milioni di persone... 🎤", "step9")
    
    opzioni = [
        "Sono solo un botolino - Il botolo",
        "Piccola tippete dove sei andata - Il botolo",
        "Poldo il bovaro - Il botolo",
        "L'emozione non ha voce - Celentano feat Paolo e me"
    ]
    
    # MODIFICA QUI LA CANZONE CORRETTA
    canzone_corretta = "Piccola tippete dove sei andata - Il botolo"
    
    scelta = st.radio("La mia dedica:", opzioni, index=None, key="song_dedica_radio")
    
    if st.button("Conferma", key="step9_btn"):
        if scelta == canzone_corretta:
            st.session_state.show_photo['step9'] = True
            track_attempt("step9", correct=True)
            st.toast("Esatto! 🎶", icon="✅")
            st.balloons()
            time.sleep(1)
        elif scelta:
            track_attempt("step9", correct=False)
            st.toast("Non è questa!", icon="❌")
    
    # Mostra foto ricordo
    if st.session_state.show_photo.get('step9', False):
        st.write("---")
        st.markdown("### 💕 La canzone per quando sei via...")
        show_memory_photo("foto_step9.jpeg", "NOI!")
        
        if st.button("➡️ Al Finale! 🎉", key="next_step9"):
            go_next()

# =============================================================================
# FINALE
# =============================================================================
elif st.session_state.step == 10:
    elapsed_time = datetime.now() - st.session_state.start_time
    minutes = int(elapsed_time.total_seconds() / 60)
    seconds = int(elapsed_time.total_seconds() % 60)
    total_attempts = sum(st.session_state.attempts.values())
    
    st.markdown("<h1 style='text-align: center; color: #c0392b; margin-bottom: 30px;'>Buon San Valentino! 🌹</h1>", unsafe_allow_html=True)
    
    # --- Animated Stat Reveal ---
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    with col_stat1:
        st.markdown(f"<div class='counter-badge stat-reveal stat-reveal-1'>⏱️ {minutes}m {seconds}s</div>", unsafe_allow_html=True)
    with col_stat2:
        if st.session_state.perfect_score:
            st.markdown("<div class='counter-badge stat-reveal stat-reveal-2'>🏆 Punteggio Perfetto!</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='counter-badge stat-reveal stat-reveal-2'>❌ {total_attempts} errori</div>", unsafe_allow_html=True)
    with col_stat3:
        st.markdown(f"<div class='counter-badge stat-reveal stat-reveal-3'>💡 {st.session_state.hints_used} aiuti</div>", unsafe_allow_html=True)
    
    st.write("")
    
    c1, c2 = st.columns([1, 1.3])
    
    with c1:
        if os.path.exists("vostra_foto.jpeg"):
            st.image("vostra_foto.jpeg", caption="Noi ❤️", use_container_width=True)
        else:
            st.markdown("""
                <div style="background: linear-gradient(135deg, #ffecd2, #fcb69f); 
                            padding: 40px; border-radius: 15px; text-align: center;">
                    📷<br>Qui apparirà la nostra foto<br>(Carica 'vostra_foto.jpeg')
                </div>
            """, unsafe_allow_html=True)
            
    with c2:
        st.markdown("<h3 style='color: #2d3436; margin-top: 0;'>Per l'amore mio...</h3>", unsafe_allow_html=True)
        
        dedica = """Ciao, volevo farti un piccolo regalo che fosse diverso dai soliti. So che non è molto ma mi sono divertito tanto a 
        creare questo gioco. Ti ho pensato tanto in questi giorni e vorrei solo stare con te adesso. Buon San Valentino amore! 
        Ti amo."""
        
        # Typewriter plays only once; on rerun, show plain text
        if not st.session_state.get("dedica_shown"):
            typewriter_clean(dedica, speed=0.05)
            st.session_state.dedica_shown = True
            save_state()
        else:
            style = """
                font-family: 'Inter', 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 1.15rem;
                color: #2d3436;
                line-height: 1.6;
                white-space: pre-wrap;
            """
            st.markdown(f"<div style='{style}'>{dedica}</div>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        if os.path.exists("canzone.mp3"):
            st.audio("canzone.mp3", format="audio/mp3")
    
    st.write("")
    st.write("")
    
    if st.session_state.perfect_score:
        st.success("🏆 Complimenti! Sei il dischetto numero 1! ❤️")
    elif total_attempts <= 3:
        st.info("😊 Ottimo lavoro! Giusto qualche errore")
    else:
        st.warning("Dobbiamo passare più tempo insieme! Ma ti amo lo stesso! 💕")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🔄 Ricomincia", use_container_width=True):
            clear_saved_state()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    with col_btn2:
        if st.button("💾 Salva Screenshot", use_container_width=True):
            st.toast("📸 Premi CTRL+P per stampare questa pagina come PDF!", icon="💡")
    
    st.write("")
    with st.expander("🎁 Clicca qui per un messaggio segreto..."):
        secret_messages = [
            "Preparati a ricevere tanto amore una volta che ci vediamo..."
        ]
        st.write(random.choice(secret_messages))