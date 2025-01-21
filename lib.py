import json
import shutil
import os
import tkinter as tk
from tkinter import messagebox, ttk
import fpdf as FPDF
from datetime import datetime, timedelta
import customtkinter as ctk



def save_settings(base_imponibile, imposta):
    with open("settings.json", 'w') as settings_file:
        json.dump({"base_imponibile": base_imponibile, "imposta": imposta}, settings_file, indent=4)
    
    
    
def load_settings():
    try:
        with open("settings.json", 'r') as settings_file:
            settings = json.load(settings_file)
            base_imponibile = settings["base_imponibile"]
            imposta = settings["imposta"]
    except FileNotFoundError:
        base_imponibile = 0.78
        imposta = 0.23
    return base_imponibile, imposta


base_imponibile, imposta = load_settings()

def mese_precedente_tradotto(today):
    mesi=["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno","Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    if today.month==1:
        return mesi[11]+' '+str(today.year-1)
    else:
        return mesi[today.month-2]+' '+str(today.year)

# Funzioni di utilità
def crea_backup(filename):
    """Crea un backup del file."""
    backup_filename = f"{filename}.bak"
    if os.path.exists(filename):
        shutil.copy(filename, backup_filename)
    return backup_filename


def return_paga_lorda(id):
    with open("paga.json", 'r') as paga_file:
        paga = json.load(paga_file)
    with open("utenti.json", 'r') as utenti_file:
        utenti = json.load(utenti_file)
    for utente in utenti:
        if utente['id'] == id:
            paga_utente = next((p['paga'] for p in paga if p['id'] == utente['id']), 0)
    return (paga_utente + paga_utente * base_imponibile * imposta)


def ripristina_backup(filename):
    """Ripristina il file dal backup."""
    backup_filename = f"{filename}.bak"
    if os.path.exists(backup_filename):
        shutil.copy(backup_filename, filename)
        print(f"Ripristinato il file {filename} dal backup.")
    else:
        print(f"Errore: Nessun backup trovato per {filename}.")

# Assicura che i file esistano
def ensure_file_exists(filename, default_data):
    if not os.path.exists(filename):
        with open(filename, 'w') as file:
            json.dump(default_data, file, indent=4)

ensure_file_exists("utenti.json", [])
ensure_file_exists("paga.json", [])

# Gestione utenti
def crea_utente(nome, cf_piva, ruolo, indirizzo, utenti_filename="utenti.json"):
    """Crea un nuovo utente nel file utenti.json."""
    try:
        with open(utenti_filename, 'r') as file:
            utenti = json.load(file)
    except FileNotFoundError:
        utenti = []

    if any(utente['cf_piva'] == cf_piva for utente in utenti):
        print(f"Un utente con CF/PIVA {cf_piva} esiste già. Non è possibile creare l'utente.")
        return False

    nuovo_id = max((utente['id'] for utente in utenti), default=0) + 1
    utente = {
        "id": nuovo_id,
        "nome": nome,
        "cf_piva": cf_piva,
        "indirizzo": indirizzo,
        "ruolo": ruolo,
    }
    utenti.append(utente)

    with open(utenti_filename, 'w') as file:
        json.dump(utenti, file, indent=4)

    print(f"Utente {nome} creato con successo!")
    return True

def aggiorna_paga(utenti_filename="utenti.json", paga_filename="paga.json"):
    """Aggiorna o crea il file della lista paga."""
    try:
        with open(utenti_filename, 'r') as utenti_file:
            utenti = json.load(utenti_file)
    except FileNotFoundError:
        print(f"Errore: Il file {utenti_filename} non esiste.")
        return False

    try:
        with open(paga_filename, 'r') as paga_file:
            paga = json.load(paga_file)
    except FileNotFoundError:
        paga = []

    for utente in utenti:
        if not any(p['id'] == utente['id'] for p in paga):
            paga.append({"id": utente['id'], "paga": 0})

    with open(paga_filename, 'w') as paga_file:
        json.dump(paga, paga_file, indent=4)

    print("Lista paga aggiornata con successo.")
    return True

def rimuovi_utente(user_id, utenti_filename="utenti.json", paga_filename="paga.json"):
    """Rimuove un utente dai file utenti.json e paga.json."""
    crea_backup(utenti_filename)
    crea_backup(paga_filename)

    try:
        with open(utenti_filename, 'r') as utenti_file:
            utenti = json.load(utenti_file)
    except FileNotFoundError:
        print(f"Errore: Il file {utenti_filename} non esiste.")
        return False

    utenti = [utente for utente in utenti if utente['id'] != user_id]
    with open(utenti_filename, 'w') as utenti_file:
        json.dump(utenti, utenti_file, indent=4)

    try:
        with open(paga_filename, 'r') as paga_file:
            paga = json.load(paga_file)
    except FileNotFoundError:
        paga = []

    paga = [p for p in paga if p['id'] != user_id]
    with open(paga_filename, 'w') as paga_file:
        json.dump(paga, paga_file, indent=4)

    print(f"Utente con ID {user_id} rimosso.")
    return True

# Gestione vendite
def registra_vendita(ids, prezzo, provv, utenti_filename="utenti.json", paga_filename="paga.json", vendite_filename="vendite.json"):
    """Registra una vendita e aggiorna la paga degli utenti coinvolti."""
    try:
        with open(vendite_filename, 'r') as vendite_file:
            vendite = json.load(vendite_file)
    except FileNotFoundError:
        vendite = []

    vendita = {"ids": ids, "prezzo": prezzo, "provvigione": provv}
    vendite.append(vendita)

    with open(vendite_filename, 'w') as vendite_file:
        json.dump(vendite, vendite_file, indent=4)

    try:
        with open(utenti_filename, 'r') as utenti_file:
            utenti = json.load(utenti_file)

        with open(paga_filename, 'r') as paga_file:
            paga = json.load(paga_file)
    except FileNotFoundError:
        print("Errore: File utenti.json o paga.json non trovato.")
        return False

    found = False
    
    for utente_id in ids:
        print(f"Aggiornamento paga per utente con ID {utente_id}...")
        for utente in utenti:
            if utente['id'] == utente_id:
                print(f"Utente trovato: {utente['nome']}")
                for p in paga:
                    if p['id'] == utente_id:
                        p['paga'] += provv / len(ids)
                        print(f"Aggiornata paga di {utente['nome']} di {provv / len(ids)} euro.")
                        found=True
                if not found:
                    print("Utente non trovato nella lista paga.")
                    paga.append({"id": utente_id, "paga": provv / len(ids)})
    try:
        with open(paga_filename, 'w') as paga_file:
            json.dump(paga, paga_file, indent=4)
    except FileNotFoundError:
        print("Errore: File paga.json non trovato.")
        return False

    print("Vendita registrata e paga aggiornata.")
    return True

# Interfaccia grafica
import customtkinter as ctk
import tkinter.messagebox as messagebox
import json

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestione Aziendale")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.create_widgets()

    def create_widgets(self):
        # Frame for User Creation
        self.create_user_frame = ctk.CTkFrame(self.root)
        self.create_user_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(
            self.create_user_frame,
            text="Crea Nuovo Dealer",
            command=self.create_user_window
        ).pack(pady=10)

        # Frame for Sales Management
        self.sales_frame = ctk.CTkFrame(self.root)
        self.sales_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkButton(
            self.sales_frame,
            text="Registra Nuova Vendita",
            command=self.open_sales_window
        ).pack(pady=10)

        # Frame for Displaying Users
        self.users_frame = ctk.CTkFrame(self.root)
        self.users_frame.pack(pady=10, padx=10, fill="both", expand=True)

        ctk.CTkLabel(self.users_frame, text="Dealer e Paga:", font=("Arial", 18)).pack(pady=5)
        self.users_container = ctk.CTkFrame(self.users_frame)
        self.users_container.pack(fill="both", expand=True)

        ctk.CTkButton(
            self.users_frame,
            text="Aggiorna Lista",
            command=self.refresh_users
        ).pack(pady=5)
        
        ctk.CTkButton(
            self.users_frame,
            text="Impostazioni",
            command=self.open_settings_window
        ).pack(pady=5)

        self.refresh_users()

    def create_user(self):
        nome = self.name_entry.get()
        cf_piva = self.cf_piva_entry.get()
        ruolo = self.role_entry.get()
        indirizzo = self.indirizzo_entry.get()

        if not all([nome, cf_piva, ruolo, indirizzo]):
            messagebox.showerror("Errore", "Inserire tutti i campi.")
            return

        if crea_utente(nome, cf_piva, ruolo, indirizzo):
            messagebox.showinfo("Successo", f"Utente {nome} creato con successo!")
        else:
            messagebox.showerror("Errore", "Errore durante la creazione dell'utente.")

        self.refresh_users()

    def register_sale(self):
        try:
            ids = list(map(int, self.sales_ids_entry.get().split(',')))
            prezzo = float(self.sales_price_entry.get())
            provv = float(self.sales_provv_entry.get())

            if registra_vendita(ids, prezzo, provv):
                messagebox.showinfo("Successo", "Vendita registrata con successo!")
            else:
                messagebox.showerror("Errore", "Errore durante la registrazione della vendita.")
        except ValueError:
            messagebox.showerror("Errore", "Dati di input non validi.")

        self.refresh_users()

    def refresh_users(self):
        for widget in self.users_container.winfo_children():
            widget.destroy()

        try:
            with open("utenti.json", 'r') as utenti_file:
                utenti = json.load(utenti_file)

            with open("paga.json", 'r') as paga_file:
                try:
                    paga = json.load(paga_file)
                except json.JSONDecodeError:
                    paga = []

            for utente in utenti:
                paga_utente = next((p['paga'] for p in paga if p['id'] == utente['id']), 0)
                btn_text = f"ID: {utente['id']}, Nome: {utente['nome']}, Paga: {paga_utente:.2f}€"
                btn = ctk.CTkButton(
                    self.users_container,
                    text=btn_text,
                    command=lambda u=utente: self.open_payment_window(u)
                )
                btn.pack(fill="x", pady=5)
        except FileNotFoundError:
            ctk.CTkLabel(self.users_container, text="Nessun dato disponibile.").pack()

    def open_settings_window(self):
        settings_window = ctk.CTkToplevel(self.root)
        settings_window.title("Impostazioni")
        settings_window.geometry("400x200")

        ctk.CTkLabel(settings_window, text="Base Imponibile:").pack(pady=5)
        base_imponibile_entry = ctk.CTkEntry(settings_window)
        base_imponibile_entry.pack(pady=5)
        base_imponibile_entry.insert(0, base_imponibile)

        ctk.CTkLabel(settings_window, text="Imposta:").pack(pady=5)
        imposta_entry = ctk.CTkEntry(settings_window)
        imposta_entry.pack(pady=5)
        imposta_entry.insert(0, imposta)

        def save_new_settings():
            try:
                new_base_imponibile = float(base_imponibile_entry.get())
                new_imposta = float(imposta_entry.get())
                save_settings(new_base_imponibile, new_imposta)
                messagebox.showinfo("Successo", "Impostazioni salvate con successo.")
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("Errore", "Inserire un valore numerico valido.")

        ctk.CTkButton(settings_window, text="Salva", command=save_new_settings).pack(pady=10)
    
    def open_payment_window(self, utente):
        with open("paga.json", 'r') as paga_file:
            paga = json.load(paga_file)

        payment_window = ctk.CTkToplevel(self.root)
        payment_window.title(f"Quietanza - {utente['nome']}")
        payment_window.geometry("400x400")

        ctk.CTkLabel(payment_window, text=f"ID: {utente['id']}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"Nome: {utente['nome']}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"CF/PIVA: {utente['cf_piva']}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"Ruolo: {utente['ruolo']}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"Indirizzo: {utente['indirizzo']}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"Paga Netta: €{next((p['paga'] for p in paga if p['id'] == utente['id']), 0)}").pack(pady=5)
        ctk.CTkLabel(payment_window, text=f"Paga Lorda: €{return_paga_lorda(utente['id'])}").pack(pady=5)

        ctk.CTkCheckBox(payment_window, text="Salva in Public").pack(pady=5)
        ctk.CTkCheckBox(payment_window, text="Stampa").pack(pady=5)

        ctk.CTkButton(
            payment_window,
            text="Genera Quietanza in PDF",
            command=lambda: generate_pdf(utente, payment_window)
        ).pack(pady=10)

    def create_user_window(self):
        create_user_window = ctk.CTkToplevel(self.root)
        create_user_window.title("Crea Utente")
        create_user_window.geometry("400x300")

        ctk.CTkLabel(create_user_window, text="Nome:").grid(row=0, column=0, padx=10, pady=5)
        self.name_entry = ctk.CTkEntry(create_user_window)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        ctk.CTkLabel(create_user_window, text="CF/PIVA:").grid(row=1, column=0, padx=10, pady=5)
        self.cf_piva_entry = ctk.CTkEntry(create_user_window)
        self.cf_piva_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(create_user_window, text="Ruolo:").grid(row=2, column=0, padx=10, pady=5)
        self.role_entry = ctk.CTkEntry(create_user_window)
        self.role_entry.grid(row=2, column=1, padx=10, pady=5)

        ctk.CTkLabel(create_user_window, text="Indirizzo:").grid(row=3, column=0, padx=10, pady=5)
        self.indirizzo_entry = ctk.CTkEntry(create_user_window)
        self.indirizzo_entry.grid(row=3, column=1, padx=10, pady=5)

        ctk.CTkButton(
            create_user_window, text="Crea Utente", command=self.create_user
        ).grid(row=4, column=0, columnspan=2, pady=10)

    def open_sales_window(self):
        with open("utenti.json", 'r') as utenti_file:
            utenti = json.load(utenti_file)

        sales_window = ctk.CTkToplevel(self.root)
        sales_window.title("Nuova Vendita")
        sales_window.geometry("500x400")

        ctk.CTkLabel(sales_window, text="Seleziona Dealers:").grid(row=0, column=0, padx=10, pady=5)

        dealers_frame = ctk.CTkFrame(sales_window)
        dealers_frame.grid(row=0, column=1, padx=10, pady=5)

        self.dealer_vars = {}
        for utente in utenti:
            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(
                dealers_frame,
                text=f"{utente['nome']} (ID: {utente['id']})",
                variable=var
            )
            chk.pack(anchor='w')
            self.dealer_vars[utente['id']] = var

        ctk.CTkLabel(sales_window, text="Prezzo:").grid(row=1, column=0, padx=10, pady=5)
        price_entry = ctk.CTkEntry(sales_window)
        price_entry.grid(row=1, column=1, padx=10, pady=5)

        ctk.CTkLabel(sales_window, text="Provvigione:").grid(row=2, column=0, padx=10, pady=5)
        provv_entry = ctk.CTkEntry(sales_window)
        provv_entry.grid(row=2, column=1, padx=10, pady=5)

        def confirm_sale():
            try:
                ids = [id for id, var in self.dealer_vars.items() if var.get()]
                prezzo = float(price_entry.get())
                provv = float(provv_entry.get())

                if registra_vendita(ids, prezzo, provv):
                    messagebox.showinfo("Successo", "Vendita registrata con successo!")
                    sales_window.destroy()
                else:
                    messagebox.showerror("Errore", "Errore durante la registrazione della vendita.")
            except ValueError:
                messagebox.showerror("Errore", "Dati di input non validi.")

        ctk.CTkButton(sales_window, text="Conferma", command=confirm_sale).grid(row=3, column=1, pady=20)
        self.refresh_users()

# Replace `crea_utente`, `registra_vendita`, `return_paga_lorda`, and `generate_pdf` with appropriate function implementations.




    from datetime import datetime, timedelta
from fpdf import FPDF





def generate_pdf(utente, window):
    """Genera un PDF professionale per la quietanza di pagamento."""
    try:
        # Leggi il saldo corrente dell'utente
        with open("paga.json", 'r') as paga_file:
            paga = json.load(paga_file)
        paga_utente = next((p['paga'] for p in paga if p['id'] == utente['id']), 0)
        

        # Calcoli per la provvigione
        base_imponibile, imposta = load_settings()

        # Data di emissione e mese precedente
        oggi = datetime.today()
        mese_precedente=mese_precedente_tradotto(oggi)
        
        data_emissione = oggi.strftime("%d/%m/%Y")

        # Creazione del PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
        pdf.add_font('DejaVu', 'B', 'fonts/DejaVuSans-Bold.ttf', uni=True)
        pdf.set_font("DejaVu", size=12)
        larghezza_pagina = pdf.w
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Intestazione                 ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        
        pdf.set_xy(10, 10)
        pdf.cell(100, 10, txt=f"Nome: {utente['nome']}", ln=True)
        pdf.set_xy(10, 15)
        pdf.cell(100, 10, txt=f"CF/P.Iva: {utente['cf_piva']}", ln=True)

        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Destinatario                 ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        pdf.set_xy(110, 10)
        pdf.set_font("DejaVu", style="B", size=12)
        pdf.cell(0, 10, txt="Spett.le", ln=True)
        pdf.set_xy(110, 15)
        pdf.set_font("DejaVu", size=12)
        pdf.cell(0, 10, txt="PRESIDENT CUP S.r.l.", ln=True)
        pdf.set_xy(110, 20)
        pdf.cell(0, 10, txt="Via Tiburtina Valeria Km.112,500", ln=True)
        pdf.set_xy(110, 25)
        pdf.cell(0, 10, txt="67068 Scurcola Marsicana (AQ)", ln=True)
        pdf.set_xy(110, 30)
        pdf.cell(0, 10, txt="Partita Iva: 13629791008", ln=True)

        # Sezione centrale: Titolo Quietanza
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Titolo                       ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        pdf.set_xy(10, 50)
        pdf.set_font("DejaVu", style="BU", size=16)  # Bold e Underline
        pdf.cell(0, 10, txt="QUIETANZA", ln=True, align='C')

        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Informazioni                 ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        
        pdf.set_xy(10, 70)
        pdf.set_font("DejaVu", size=12)
        pdf.cell(100, 10, txt=f"Data di emissione: {data_emissione}", ln=True)
        pdf.cell(100, 10, txt=f"Provvigioni relative al mese di {mese_precedente} per vendite a domicilio (D.Lvo 114/98)", ln=True)


        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Dati Lordi                   ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''


        # Sezione informazioni a destra
        testo_provvigioni = f"Provvigioni Occasionali:            €{paga_utente + base_imponibile * imposta:.2f}"
        larghezza_testo_provvigioni = pdf.get_string_width(testo_provvigioni)
        x_provvigioni = larghezza_pagina - larghezza_testo_provvigioni - 15 # Margine di 10 punti dal bordo destro

        pdf.set_xy(x_provvigioni, 100)
        pdf.cell(0, 10, txt=testo_provvigioni, ln=True) # Non serve align='R'

        # Esempio per "Tot. Imponibile"
        testo_imponibile = f"Tot. Imponibile:            €{paga_utente + base_imponibile * imposta:.2f}"
        larghezza_testo_imponibile = pdf.get_string_width(testo_imponibile)
        x_imponibile = larghezza_pagina - larghezza_testo_imponibile - 15

        pdf.set_xy(x_imponibile, 110)
        pdf.cell(0, 10, txt=testo_imponibile, ln=True)

        # Esempio per "Totale"
        pdf.set_font("DejaVu", style="B", size=12)
        testo_totale = f"Totale:            €{paga_utente + base_imponibile * imposta:.2f}"
        larghezza_testo_totale = pdf.get_string_width(testo_totale)
        x_totale = larghezza_pagina - larghezza_testo_totale - 15

        pdf.set_xy(x_totale, 130)
        pdf.cell(0, 10, txt=testo_totale, ln=True)
        
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Ritenute                     ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        pdf.set_font("DejaVu", size=12)
        pdf.set_xy(10, 140)
        pdf.cell(100, 10, txt="Rit.Prev.C/Az: DA DEFINIRE IL CALCOLO", ln=True)
        
        
        
        pdf.set_xy(80, 150)
        pdf.cell(100, 10, txt="Rit. a titolo d'imposta definitiva art.25", ln=True)
        pdf.set_xy(80, 155)
        pdf.cell(100, 10, txt="bis. DPR 600/73 del 23% sul 78%:", ln=True)
        
        
        testo_ritenimp="€{:.2f}".format(base_imponibile * imposta)
        larghezza_testo_ritenimp = pdf.get_string_width(testo_ritenimp)
        x_ritenimp = larghezza_pagina - larghezza_testo_ritenimp - 15
        pdf.set_xy(x_ritenimp, 155)
        pdf.cell(0, 10, txt=testo_ritenimp, ln=True)
        
        
        pdf.set_xy(80, 165)
        pdf.cell(100, 10, txt="Rit. previdenziale INPS Legge 335/95 del", ln=True)
        pdf.set_xy(80, 170)
        pdf.cell(100, 10, txt="33,72% sul 78%, quota a carico 1/3:", ln=True)
        
        
        testo_riteprev="DA DEFINIRE"
        larghezza_testo_riteprev = pdf.get_string_width(testo_riteprev)
        x_riteprev = larghezza_pagina - larghezza_testo_riteprev - 15
        pdf.set_xy(x_riteprev, 170)
        pdf.cell(0, 10, txt=testo_riteprev, ln=True)
        
        
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Acconto                      ║     ---------------------
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        
        
        testo_acconto=f"Acconto: DA IMPLEMENTARE"
        larghezza_testo_acconto = pdf.get_string_width(testo_acconto)
        x_acconto = larghezza_pagina - larghezza_testo_acconto - 15
        pdf.set_xy(x_acconto, 180)
        pdf.cell(0, 10, txt=testo_acconto, ln=True)
        
    
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Saldo                        ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        pdf.set_font("DejaVu", style="B", size=12)
        testo_saldo=f"Saldo:            €{paga_utente} "
        larghezza_testo_saldo = pdf.get_string_width(testo_saldo)
        x_saldo = larghezza_pagina - larghezza_testo_saldo - 15
        pdf.set_xy(x_saldo, 190)
        pdf.cell(0, 10, txt=testo_saldo, ln=True)
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Esclusione INPS              ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        pdf.set_font("DejaVu", size=12)
        pdf.set_xy(10, 200)
        pdf.cell(100, 10, txt=f"Esclusione INPS maturata:     €{return_paga_lorda(utente['id'])}", ln=True)
        
        '''
        
        ╔═══════════════════════════════════════╗
        ║                                       ║
        ║          Firma e Note                 ║
        ║                                       ║
        ╚═══════════════════════════════════════╝
        
        '''
        
        pdf.set_xy(130, 220)
        pdf.cell(100, 10, txt="Firma per ricevuta", ln=True)
        pdf.set_xy(120, 230)
        pdf.cell(100, 10, txt="____________________________", ln=True)
        pdf.set_xy(40, 265)
        pdf.cell(100, 10, txt="Nota: Esclusione INPS fino a 6410,26 Euro di provvigioni lorde", ln=True)
        # Salva il PDF
        giorno = datetime.today().strftime("%d-%m-%Y")
        filename = f"Quietanze/quietanza_{utente['nome']}-{giorno}.pdf"
        pdf.output(filename)

        messagebox.showinfo("PDF Generato", f"Quietanza salvata come {filename}")
        window.destroy()
    except Exception as e:
        messagebox.showerror("Errore", f"Errore durante la generazione del PDF: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
