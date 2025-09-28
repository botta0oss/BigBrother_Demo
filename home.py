import streamlit as st
import json
from pathlib import Path

st.set_page_config(
    page_title="Selezione demo",
    layout="centered"
)

# funzione per trovare il json dei path
@st.cache_data
def find_analysis_configs(root_path='data'):
    configs = {}
    root = Path(root_path)
    if not root.is_dir():
        return configs
    
    for dir_path in root.iterdir():
        if dir_path.is_dir():
            json_path = dir_path / f"{dir_path.name}.json"
            if json_path.is_file():
                configs[dir_path.name] = str(json_path.as_posix())
    return configs

# --- Interfaccia Utente (simile alla tua) ---
st.title("Benvenuto nella demo")
st.markdown(
    """
    Seleziona una chat dal menu a tendina per iniziare.
    Una volta scelta, vai alla pagina **Dashboard** dal menu laterale per visualizzare l'analisi dettagliata.
    """
)

analysis_options = find_analysis_configs()

if not analysis_options:
    st.error("Nessuna configurazione di analisi trovata nella cartella 'data'.")
    st.info("Assicurati che ogni sottocartella in 'data' contenga un file .json con lo stesso nome della cartella (es. 'data/TestBullismo/TestBullismo.json').")
else:
    option_keys = [None] + list(analysis_options.keys())

    selected_analysis_key = st.selectbox(
        "Scegli la chat da analizzare:",
        options=option_keys,
        format_func=lambda x: "Nessuna" if x is None else x.replace('_', ' ').title()
    )


    if selected_analysis_key:
        # salva il path del file JSON
        st.session_state['config_path'] = analysis_options[selected_analysis_key]
        
        # carica il nome della chat dal json per un feedback migliore
        with open(analysis_options[selected_analysis_key], 'r') as f:
            config_data = json.load(f)
            chat_name = config_data.get("nome_chat", selected_analysis_key)
        
        st.success(f"Hai selezionato l'analisi: **{chat_name}**. Ora puoi procedere alla pagina **Dashboard**.")
    else:
        # pulisci stato se si cambia selezione
        if 'config_path' in st.session_state:
            del st.session_state['config_path']
        st.warning("Per favore, seleziona un'analisi per continuare.")

st.markdown("---")