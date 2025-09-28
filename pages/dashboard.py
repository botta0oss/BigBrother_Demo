import streamlit as st
import pandas as pd
import json, re, os
import plotly.express as px
from pathlib import Path




# Funzione per caricare i dati 
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)

def run_dashboard(paths):
    
    nome_chat = paths['nome_chat']
    st.title(f"Report Analisi : {nome_chat}")
    st.sidebar.title("**Filtri**")

    
    with open("style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    


    
   
    
    df_database = load_csv(paths['database'])
    # completo il database con anche i cluster e i label per dopo 
    df_cluster_labels = load_csv(paths['cluster_label_csv']) 
    df_completo = pd.merge(df_database.copy(), df_cluster_labels, on='cluster', how='left')
    df_completo['cluster_label'].fillna('Rumore', inplace=True)

    df_messaggi_utenti = load_csv(paths['messaggi_utenti_csv'])
    df_messaggi_utenti["nome"].astype(str)


    
    total_messages = len(df_database)
    num_utenti = df_database['sender_id'].nunique()
    overall_sentiment_score = paths['polarizzazione'][0]
    overall_sentiment_label = paths['polarizzazione'][1]
    
    # Metriche generali
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        col1.metric("Totale Messaggi", total_messages)
        col2.metric("Numero di Utenti", num_utenti)
        col3.metric("Polarizzazione Generale", f"{overall_sentiment_label} ({overall_sentiment_score:.2f})")

    

    # Analisi Utenti 
    st.header("Utenti")
    with st.expander("Visualizza Elenco Completo degli Utenti"):
        df_utenti = df_database[['sender_id', 'nome', 'cognome','nome_vero']].drop_duplicates().reset_index(drop=True)
        df_utenti = df_utenti.rename(columns={
        'sender_id': 'ID Utente',
        'nome': 'Username',
        'nome vero': 'Nome',
        'cognome': 'Cognome'
        })
        st.dataframe(df_utenti, use_container_width=True)
        
    tab1, tab2, tab3, tab4= st.tabs(["Messaggi per Utente", "Sentimento medio per utente", "Emoji per utente", "Messaggi per utente nel corso della giornata"])

    with tab1:
        st.subheader("Messaggi inviati per Utente")
        fig_messaggi = px.bar(
            df_messaggi_utenti.sort_values('messaggi', ascending=False),
            x='nome',
            y='messaggi',
            title="Numero di Messaggi Inviati per Utente",
            labels={'nome': 'Utente', 'messaggi': 'Numero di Messaggi'}
            )
        fig_messaggi.update_xaxes(tickangle=90,type='category')
        st.plotly_chart(fig_messaggi,key="messagi_utente", use_container_width=True)

    with tab2:
        st.subheader("Sentimento medio per Utente")
        df_sentiment_utente = load_csv(paths['sentiment_per_utente_csv'])
        fig_sentiment = px.bar(
            df_sentiment_utente.sort_values('media_sentiment', ascending=False),
            x='utente',
            y='media_sentiment',
            title="Sentimento medio per Utente",
            labels={'utente': 'utente', 'sentimento': 'media sentiment'}
            )
        fig_sentiment.update_xaxes(tickangle=90,type='category')
        st.plotly_chart(fig_sentiment, key="sentimento_utente",use_container_width=True)

    with tab3:
        st.subheader("Emoji usate per Utente")
        df_emoji_utenti = load_csv(paths['emoji_per_utente_csv'])
        fig_emoji = px.bar(
            df_emoji_utenti.sort_values('num_emoji', ascending=False),
            x='sender_id',
            y='num_emoji',
            title="Uso di emoji per Utente",
            labels={'sender_id': 'sender_id', 'emoji': 'numero di emoji'}
            )
        fig_emoji.update_xaxes(tickangle=90,type='category')
        st.plotly_chart(fig_emoji, key="emoji_utente",use_container_width=True)
    with tab4:
        st.subheader("Heatmap attività degli utenti durante il giorno")
        df_database['ora'] = pd.to_datetime(df_database['date']).dt.hour
        heatmap_attività= df_database.pivot_table(index='sender_id', columns='ora', values='message_id', aggfunc='count').fillna(0)

        fig_heatmap = px.imshow(heatmap_attività, labels=dict(x="Ora del Giorno", y="Utente", color="N. Messaggi"),
                        title="Heatmap attività degli utenti durante il giorno")
        fig_heatmap.update_yaxes(type='category')
        st.plotly_chart(fig_heatmap, key= "heatmap_messaggi",use_container_width=False)


    # Analisi Temporale 
    st.subheader("Evoluzione del sentimento generale nel Tempo")
    df_database_temporale = load_csv(paths['avg_sentiment_per_periodo_csv'])
    
    fig_sentiment_temporale = px.line(
        df_database_temporale.sort_values('date', ascending=False),
        x = 'date',
        y = 'media_sentiment',
        title = "Sentimento medio nel tempo",
        labels={'date': 'date', 'media_sentiment': 'media sentimento'}
    )
    fig_sentiment_temporale.update_xaxes(tickangle=90)
    st.plotly_chart(fig_sentiment_temporale,key="sentiment_temporale", use_container_width=True)

    st.divider()

    #  Contenuto Messaggi 
    st.header("Analisi del Contenuto")
    
    st.subheader("Parole più comuni")
    df_parole = load_csv(paths['parole_csv'])
    top_n = st.slider('Seleziona il numero di parole da visualizzare', 5, 50, 25)
    
    fig_parole = px.bar(
        df_parole.head(top_n).sort_values('frequenza', ascending=False),
        x='parola',
        y='frequenza',
        title="Parole più comuni",
        labels={'parola': 'parola', 'frequenza': 'frequenza'}
    )
    fig_parole.update_xaxes(tickangle=90)
    st.plotly_chart(fig_parole, key="parole_comuni",use_container_width=True)
    st.divider()


    # ANALISI PER UTENTE
    st.header("Analisi Dettagliata per Utente")
    st.write("usare la sidebar per selezionare l'utente da visualizzare")
    utenti = df_database['sender_id'].unique()
    
    st.sidebar.subheader("Analisi dettagliata per utente")
    utente_selezionato = st.sidebar.selectbox("Seleziona un utente", utenti, help="Scegli un utente per esplorarne l'attività, il sentimento e le parole più usate.")
    st.sidebar.divider()
    df_utente = df_completo[df_completo['sender_id'] == utente_selezionato].copy()
    df_utente['date'] = pd.to_datetime(df_utente['date'])
    
    
    tab1, tab2, tab3 = st.tabs(["Parole più Usate", "Andamento del Sentimento", "Emoji più usate"])

    # parole più utilizzate per utente
    with tab1:
        st.subheader(f"Parole più utilizzate da utente {utente_selezionato} ")
        df_parole_utenti = load_csv(paths['parole_utenti_csv'])
        df_parole_selezionate = df_parole_utenti[df_parole_utenti['sender_id'] == utente_selezionato]
        if not df_parole_selezionate.empty:
            fig_words = px.bar(
                df_parole_selezionate.sort_values('frequenza', ascending=True), 
                x='frequenza',
                y='parola',
                orientation='h',
                title=f"Parole più comuni per {utente_selezionato}",
                labels={'parola': 'Parole', 'frequenza': 'Numero di utilizzi'}
            )
            st.plotly_chart(fig_words,key="parole_per_utente", use_container_width=True)
        else:
            st.info(f"Nessuna parola trovata per l'utente {utente_selezionato} nel file di analisi.")
    with tab2:     
        st.subheader(f"Evoluzione del sentiment nel tempo utente {utente_selezionato} ")
        
        if len(df_utente) < 2:
            st.warning("Non ci sono abbastanza messaggi per visualizzare un andamento nel tempo.")
        else:
            df_utente_ordinato = df_utente.sort_values('date')
            fig_sentiment = px.line(
                df_utente_ordinato,
                x='date',
                y='sentiment_map',
                title='Sentiment di ogni messaggio nel tempo',
                markers=True,
                labels={'date': 'Data', 'sentiment_map': 'Punteggio Sentiment'},
                hover_data={'messaggio_originale': True}
            )
            fig_sentiment.add_hline(y=0, line_dash="dash", line_color="grey")
            fig_sentiment.update_yaxes(
                tickvals=[-2, -1, 0, 1, 2],
                ticktext=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive']
            )
            st.plotly_chart(fig_sentiment,key="sentimento_utente_temporale", use_container_width=True)
            st.write("Ogni punto rappresenta un singolo messaggio. Passa il mouse sopra per leggerne il testo.")
    with tab3:
        st.subheader(f"Emoji più utilizzate da {utente_selezionato}")
        df_user_con_emoji = df_utente[df_utente['emoji'].notna() & (df_utente['emoji'] != '')].copy()   
        if df_user_con_emoji.empty:
            st.info(f"L'utente {utente_selezionato} non sembra aver utilizzato emoji.")
        else:
            lista_emoji = [emoji for emoji_string in df_user_con_emoji['emoji'] for emoji in emoji_string]
            from collections import Counter
            conteggio_emoji = Counter(lista_emoji)
            df_conteggio_emoji = pd.DataFrame(conteggio_emoji.items(), columns=['emoji', 'frequenza'])
            fig_emoji = px.bar(
                df_conteggio_emoji.sort_values('frequenza', ascending=True).tail(15), 
                x='frequenza',
                y='emoji',
                orientation='h',
                title="Le 15 emoji più frequenti"
            )
            st.plotly_chart(fig_emoji,key="emoji_frequenza", use_container_width=True)
            st.subheader("Contesto dei messaggi con emoji")
            st.dataframe(df_user_con_emoji[['date', 'messaggio_originale', 'emoji']], use_container_width=True)

    st.divider()



    # VISUALIZZAZIONE MESSAGGI
    st.header("Esplora i Messaggi")
    st.write("usare la sidebar per selezionare l'utente da visualizzare")
    
    # Filtri
    
    st.sidebar.subheader("Esplorazione Messaggi")
    utente_selezionato = st.sidebar.selectbox('Filtra per Utente (opzionale)', ['Tutti'] + list(utenti))
    
    sentimenti = df_database['label'].unique()
    selected_sentiment = st.sidebar.selectbox('Filtra per Sentimento (opzionale)', ['Tutti'] + list(sentimenti))
    st.sidebar.divider()

    # Applica filtri
    filtered_df = df_database.copy()
    if utente_selezionato != 'Tutti':
        filtered_df = filtered_df[filtered_df['sender_id'] == utente_selezionato]
    if selected_sentiment != 'Tutti':
        filtered_df = filtered_df[filtered_df['label'] == selected_sentiment]
    
    st.dataframe(filtered_df[['message_id','sender_id', 'messaggio_originale', 'date', 'label', 'score']].set_index('message_id').sort_index())

    # Ricerca per parole chiave
    st.subheader("Ricerca e Analisi per Parole Chiave")
    st.markdown("Inserisci una o più parole chiave (separate da virgola) per analizzare la loro frequenza, chi le usa e in quale contesto.")

    # input parole
    keyword_input = st.text_input(
    "Parole chiave",
    help="La ricerca non è case-sensitive (maiuscole/minuscole non contano). Separare i termini con una virgola."
    )

    # Procede solo se l'utente ha inserito qualcosa
    if keyword_input:
    
    # preprocessing delle parole
        keywords = [k.strip().lower() for k in keyword_input.split(',') if k.strip()]

        if not keywords:
            st.warning("Per favore, inserisci parole chiave valide.")
        else:
        # regex per trovare qualsiasi delle parole chiave
        # \b assicura che cerchiamo parole intere (es. "art" non matcha "party")
            keyword_regex = r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b'

        # filtro il DataFrame per trovare i messaggi che contengono almeno una keyword
        # 'case=False' case-insensitive
        # 'na=False' per gestire eventuali valori NaN 
            df_hits = df_database[df_database['messaggio_originale'].str.contains(keyword_regex, case=False, na=False)].copy()

            if df_hits.empty:
                st.info("Nessun messaggio trovato contenente le parole chiave specificate.")
            else:
                st.success(f"Trovati {len(df_hits)} messaggi contenenti le parole chiave.")

            # Visualizzazione
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Utilizzo per Utente")
                    user_counts = df_hits['sender_id'].value_counts()
            
                    fig_bar = px.bar(
                        user_counts, 
                        x=user_counts.index, 
                        y=user_counts.values,
                        labels={'x': 'Utente', 'y': 'Numero di Messaggi'},
                        title="Messaggi con parole chiave per utente"
                    )
                    fig_bar.update_layout(xaxis_title="Utente", yaxis_title="Conteggio Messaggi")
                    fig_bar.update_xaxes(type='category')
                    st.plotly_chart(fig_bar,key="parola_key_utente", use_container_width=True)

                # Frequenza
                with col2:
                    st.subheader("Timeline di Utilizzo")
             
                    df_hits['date'] = pd.to_datetime(df_hits['date'])
                
                # raggruppo per giorno e conta i messaggi
                    timeline_counts = df_hits.set_index('date').resample('D').size()

                    fig_line = px.line(
                        timeline_counts,
                        x=timeline_counts.index,
                        y=timeline_counts.values,
                        labels={'x': 'Data', 'y': 'Numero di Messaggi'},
                        title="Frequenza di utilizzo nel tempo"
                    )
                    fig_line.update_layout(xaxis_title="Data", yaxis_title="Conteggio Messaggi")
                    st.plotly_chart(fig_line,key="utilizzo_parole_temporalmente", use_container_width=True)


            # 5. Tabella con i Messaggi 
                st.subheader("Contesto dei Messaggi")
                st.markdown("Messaggi contenenti le parole chiave ricercate:")
            
            # versione ridotta della tabella con le colonne più importanti
                st.dataframe(df_hits[['date', 'sender_id', 'messaggio_originale']], use_container_width=True)
            
            # Funzione per evidenziare le parole chiave nel testo 
                def highlight_keywords(text, keywords):
                # Funzione per sostituire ogni keyword trovata con la sua versione evidenziata
                    def repl(match):
                        return f"**<font color='red'>{match.group(0)}</font>**"
                
                # regex per l'evidenziazione
                    keyword_regex_highlight = r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b'
                    highlighted_text = re.sub(keyword_regex_highlight, repl, text, flags=re.IGNORECASE)

                    return highlighted_text

                st.subheader("Messaggi con Evidenziazione")

            # appplico evidenziazzione e mostro i messaggi 
                for index, row in df_hits.iterrows():
                    with st.expander(f"{row['date']} - **{row['sender_id']}**"):
                        highlighted_message = highlight_keywords(row['messaggio_originale'], keywords)
                        st.markdown(highlighted_message, unsafe_allow_html=True)
    st.divider()
    
    # Visualizzazione Cluster
    st.header("Analisi per Cluster")
    cluster_id_to_label = df_completo[['cluster', 'cluster_label']].drop_duplicates()

    # Grafico a torta per vedere la dimensione dei cluster
    cluster_counts = df_completo['cluster_label'].value_counts() 
    fig_pie = px.pie(cluster_counts, 
                    values=cluster_counts.values, 
                    names=cluster_counts.index, 
                    title="Distribuzione Messaggi per Cluster")
    st.plotly_chart(fig_pie,key="cluster_pie",use_container_width=True)
    

    etichetta_sentiment = {
        -2 : 'Very Negative',
        -1 : 'Negative',
        0 : 'Neutral',
        1 : 'Positive',
        2 : 'Very Positive'
    }
    sentiment_cluster = df_completo.groupby('cluster')['sentiment_map'].mean().reset_index()
    sentiment_cluster = sentiment_cluster.rename(columns={'sentiment_map': 'sentiment_medio'})
    sentiment_cluster_con_label = pd.merge(sentiment_cluster, cluster_id_to_label, on='cluster', how='left')
    sentiment_cluster_con_label['sentiment_etichetta'] = sentiment_cluster_con_label['sentiment_medio'].round().astype(int).map(etichetta_sentiment)
    # Metriche per singolo cluster
    with st.container(border=True):
        # gestisco le metriche in tabbing in base a quanti cluster ci sono
        # utile per casi in cui ci sono tanti cluster diversi 
        labels = [w for index, w in sentiment_cluster_con_label['cluster_label'].items()]
        etichette = []
        for value in labels:
            etichette.append(str(value))
        st.write("**Sentimento Medio per Cluster**")
        tabs = st.tabs([i for i in etichette])
        for i, (index, row) in enumerate(sentiment_cluster_con_label.iterrows()):
            with tabs[i]:
                cluster_id = row['cluster']
                label = row['cluster_label']
                sentiment_medio = row['sentiment_medio']
                etichetta = row['sentiment_etichetta']
                st.metric(
                    label=f"**Sentimento Cluster: [ID: {cluster_id}] {label}** ",
                    value=f"{etichetta} {sentiment_medio:.2f}",
                    help=f"Sentimento medio calcolato per l'argomento '{label}'."
                    
                )

    # scatterplot dei cluster
    df_scatter = df_completo[['message_id', 'date', 'messaggio_originale', 'sender_id','plot_x', 'plot_y', 'cluster', 'cluster_label']].copy()
    fig_scatter = px.scatter(
                        df_scatter,
                        x='plot_x',
                        y='plot_y',
                        color='cluster_label',
                        hover_data=['messaggio_originale', 'sender_id', 'date'],
                        color_discrete_map={
                            "Rumore": 'lightgrey'
                        },
                    
                        labels={'x': 'umap_x', 'y': 'umap_y'},
                        title="Visualizzazione Cluster",

                    )
    st.plotly_chart(fig_scatter,key="cluster_scatter",use_container_width=True)
    

    # esploratore per cluster
    st.subheader("**Esploratore cluster**")
    cluster_label_list = sorted(df_completo['cluster_label'].unique())
    selected_cluster_label = st.selectbox('Seleziona un argomento da analizzare', cluster_label_list)
    df_cluster_filtered = df_completo[df_completo['cluster_label'] == selected_cluster_label]
    st.write(f"**Messaggi relativi a: {selected_cluster_label}**")
    st.dataframe(df_cluster_filtered[['message_id', 'sender_id', 'messaggio_originale', 'date', 'label', 'cluster_label']].set_index('message_id'))

    # Utente per cluster
    st.write(f"**Utenti più attivi in: {selected_cluster_label}**")
    user_in_cluster_counts = df_cluster_filtered['sender_id'].value_counts()
  
    fig_cluster = px.bar(
        user_in_cluster_counts.sort_values(ascending=False),
        x=user_in_cluster_counts.index,
        y=user_in_cluster_counts.values,
        title=f"Utenti più attivi in: {selected_cluster_label}",
        labels={'x': 'sender_id', 'y': 'Numero messaggi'}
    )
    fig_cluster.update_xaxes(tickangle=90, type = 'category')
    st.plotly_chart(fig_cluster,key="utenti_cluster", use_container_width=True)
    

    # attività cluster per tempo 
    st.write("**Andamento degli argomenti nel tempo**")
    df_completo['date'] = pd.to_datetime(df_completo['date'])
    attivita_nel_tempo = df_completo.groupby([df_completo['date'].dt.date, 'cluster_label']).size()
    attivita_pivot = attivita_nel_tempo.unstack(fill_value=0)
    st.line_chart(attivita_pivot)
    st.write("Conteggio messaggi per giorno e per argomento")
    st.dataframe(attivita_pivot)
    
    



st.set_page_config(layout="wide", page_title="Dashboard Analisi")
if 'config_path' not in st.session_state or st.session_state['config_path'] is None:
    st.warning("Per favore, torna alla pagina `Home` e seleziona un'analisi per iniziare.")
    st.stop()

config_path_str = st.session_state['config_path']
config_path = Path(config_path_str)

st.subheader("🔍 Informazioni di Debug")
st.info(f"Percorso ricevuto dalla Home page: `{config_path}`")
st.info(f"Directory di lavoro corrente (CWD): `{os.getcwd()}`")

# Costruiamo il percorso assoluto per essere sicuri
absolute_path = os.path.abspath(config_path)
st.info(f"Percorso assoluto che si sta tentando di aprire: `{absolute_path}`")
st.info(f"Il file a questo percorso esiste? -> **{os.path.exists(absolute_path)}**")
st.info(f"Percorso ricevuto: `{config_path_str}`")
st.info(f"Percorso assoluto: `{config_path.resolve()}`")
st.info(f"Il file esiste? -> **{config_path.is_file()}**")
# --- FINE CODICE DI DEBUG ---


try:
    # Questa parte ora sappiamo che funziona
    with config_path.open('r', encoding='utf-8') as f:
        paths = json.load(f)
    
    # ORA, prima di eseguire tutta la dashboard, verifichiamo che i path INTERNI al JSON esistano
    st.subheader("🔍 Verifica Percorsi Interni al JSON")
    all_paths_ok = True
    for key, path_str in paths.items():
        # Controlliamo solo i percorsi dei file (quelli che finiscono in .csv)
        if isinstance(path_str, str) and path_str.endswith('.csv'):
            path_obj = Path(path_str)
            if path_obj.is_file():
                st.success(f"✔️ OK: Il file '{key}' esiste al percorso: {path_str}")
            else:
                st.error(f"❌ ERRORE: Il file '{key}' NON è stato trovato al percorso: {path_str}")
                st.info(f"Percorso assoluto cercato: {path_obj.resolve()}")
                all_paths_ok = False
    
    if not all_paths_ok:
        st.error("Uno o più percorsi dei file CSV definiti nel JSON non sono corretti. Controlla la struttura delle cartelle e i nomi dei file (incluse maiuscole/minuscole).")
        st.stop() # Ferma l'esecuzione se anche solo un file manca

    st.success("Tutti i percorsi nel file JSON sono stati verificati con successo. Avvio la dashboard...")

    # Solo ora eseguiamo la dashboard
    run_dashboard(paths)

except Exception as e:
    st.error(f"Si è verificato un errore durante l'esecuzione della dashboard.")
    st.exception(e)