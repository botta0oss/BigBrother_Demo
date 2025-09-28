# debug_opener.py
import os
from pathlib import Path
import json

print("--- Inizio Test di Apertura File ---")

# Definiamo il percorso relativo ESATTAMENTE come farebbe il tuo script
relative_path_str = "data/test1/test1.json"
file_path = Path(relative_path_str)

print(f"Directory di lavoro corrente (CWD): {Path.cwd()}")
print(f"Percorso relativo che sto testando: {relative_path_str}")
print(f"Percorso assoluto calcolato: {file_path.resolve()}")

# Eseguiamo gli stessi controlli che abbiamo fatto in Streamlit
if file_path.is_file():
    print("\n[SUCCESSO] pathlib.is_file() dice che il file esiste.")
else:
    print("\n[FALLIMENTO] pathlib.is_file() dice che il file NON esiste. Fermati qui, il problema è il percorso.")
    exit() # Esce dallo script se il file non viene trovato

# Ora il test cruciale: tentiamo di aprire e leggere il file
try:
    print("Sto tentando di aprire il file...")
    
    # Leggiamo il contenuto del file byte per byte
    content_bytes = file_path.read_bytes()
    print("[SUCCESSO] Il file è stato letto in modalità binaria.")
    
    # Ora tentiamo di decodificarlo come testo UTF-8
    content_text = content_bytes.decode('utf-8')
    print("[SUCCESSO] Il contenuto è stato decodificato come testo UTF-8.")
    
    # Ora tentiamo di interpretarlo come JSON
    data = json.loads(content_text)
    print("[SUCCESSO] Il testo è stato interpretato come JSON valido.")
    
    print("\n--- TEST COMPLETATO CON SUCCESSO ---")
    print("Il file è stato aperto e letto correttamente al di fuori di Streamlit.")
    print("Contenuto del JSON:")
    print(data)

except FileNotFoundError:
    print("\n[ERRORE CRITICO] FileNotFoundError! Anche se is_file() era True. Problema di sistema/permessi molto profondo.")
except Exception as e:
    print(f"\n[ERRORE INASPETTATO] Si è verificato un errore durante la lettura del file.")
    print(f"Tipo di errore: {type(e).__name__}")
    print(f"Messaggio di errore: {e}")