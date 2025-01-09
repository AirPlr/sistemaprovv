
import json
import shutil
import os

def crea_backup(filename):
    """Crea un backup del file."""
    backup_filename = f"{filename}.bak"
    if os.path.exists(filename):
        shutil.copy(filename, backup_filename)
    return backup_filename

def ripristina_backup(filename):
    """Ripristina il file dal backup."""
    backup_filename = f"{filename}.bak"
    if os.path.exists(backup_filename):
        shutil.copy(backup_filename, filename)
        print(f"Ripristinato il file {filename} dal backup.")
    else:
        print(f"Errore: Nessun backup trovato per {filename}.")

def crea_utente(nome, cf_piva, ruolo, utenti_filename="utenti.json"):
    """Crea un nuovo utente nel file utenti.json."""
    try:
        with open(utenti_filename, 'r') as file:
            utenti = json.load(file)
    except FileNotFoundError:
        utenti = []

    # Controlla se esiste già un utente con lo stesso cf_piva
    if any(utente['cf_piva'] == cf_piva for utente in utenti):
        print(f"Un utente con CF/PIVA {cf_piva} esiste già. Non è possibile creare l'utente.")
        return

    # Genera l'ID automaticamente
    if utenti:
        ids = [utente['id'] for utente in utenti]
        nuovo_id = max(ids) + 1
    else:
        nuovo_id = 1

    utente = {
        "id": nuovo_id,
        "nome": nome,
        "cf_piva": cf_piva,
        "ruolo": ruolo
    }

    utenti.append(utente)

    with open(utenti_filename, 'w') as file:
        json.dump(utenti, file, indent=4)

    print(f"Utente {nome} creato con successo!")

def paga(id=None, utenti_filename="utenti.json", paga_filename="paga.json"):
    """Aggiorna o mostra la lista paga."""
    try:
        with open(paga_filename, 'r') as file:
            paga = json.load(file)
    except FileNotFoundError:
        paga = []

    if id is None:
        try:
            with open(utenti_filename, 'r') as fileutenti:
                utenti = json.load(fileutenti)
                ids = [utente["id"] for utente in utenti]
                for user_id in ids:
                    if not any(p['id'] == user_id for p in paga):
                        paga.append({"id": user_id, "paga": 0})
        except FileNotFoundError:
            print(f"Errore: Il file {utenti_filename} non esiste.")
            return

        with open(paga_filename, 'w') as file:
            json.dump(paga, file, indent=4)
        print("Lista paga aggiornata con nuovi utenti.")
    else:
        for p in paga:
            if p['id'] == id:
                print(p)

def rimuovi_utente(id, utenti_filename="utenti.json", paga_filename="paga.json"):
    """Rimuove un utente da utenti.json e paga.json."""
    # Crea backup dei file
    crea_backup(utenti_filename)
    crea_backup(paga_filename)

    try:
        # Leggi il file utenti
        with open(utenti_filename, 'r') as file:
            utenti = json.load(file)
    except FileNotFoundError:
        print(f"Errore: Il file {utenti_filename} non esiste.")
        return

    # Controlla se l'utente esiste
    utente_da_rimuovere = next((utente for utente in utenti if utente['id'] == id), None)
    if not utente_da_rimuovere:
        print(f"Nessun utente con ID {id} trovato.")
        return

    # Rimuovi l'utente dalla lista
    utenti = [utente for utente in utenti if utente['id'] != id]

    # Aggiorna il file utenti.json
    with open(utenti_filename, 'w') as file:
        json.dump(utenti, file, indent=4)

    print(f"Utente con ID {id} rimosso dal file {utenti_filename}.")

    try:
        # Leggi il file paga
        with open(paga_filename, 'r') as file:
            paga = json.load(file)
    except FileNotFoundError:
        paga = []

    # Rimuovi l'utente anche dal file paga, se presente
    paga = [p for p in paga if p['id'] != id]

    # Aggiorna il file paga.json
    with open(paga_filename, 'w') as file:
        json.dump(paga, file, indent=4)

    print(f"Utente con ID {id} rimosso dal file {paga_filename}.")

def undo_modifica(utenti_filename="utenti.json", paga_filename="paga.json"):
    """Ripristina entrambi i file dal backup."""
    ripristina_backup(utenti_filename)
    ripristina_backup(paga_filename)

        