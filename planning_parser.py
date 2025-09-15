import re
import pdfplumber
import json
import os
from datetime import datetime
import requests
import sys # Ajout pour une sortie propre en cas d'erreur

# --- Configuration du lien Google Drive et des horaires ---
# REMPLACEZ VOTRE_ID_DE_FICHIER par l'ID de votre fichier Google Drive
PDF_URL = "https://drive.google.com/uc?export=download&id=1w3ehgxdIgHCKrQpFG67qSgyUqqvBddGI"
PDF_FILE = "iFP.planning.pdf"

horaires = {
    "A4": ["11:00", "13:00", "15:00", "18:00"],
    "A5": ["11:30", "13:30", "15:30", "18:30"],
    "A6": ["12:00", "14:00", "16:00", "19:00", "21:00"],
    "A7": ["12:30", "14:30", "16:30", "19:30", "21:30"],
    "A8": ["17:00", "20:00", "22:00"],
    "A9": ["17:30", "20:30", "22:30"],
    "B4": ["10:00", "12:00", "14:00", "17:00"],
    "B5": ["10:30", "12:30", "14:30", "17:30"],
    "B6": ["11:00", "13:00", "15:00", "18:00", "20:00"],
    "B7": ["11:30", "13:30", "15:30", "18:30", "20:30"],
    "B8": ["16:00", "19:00", "21:00"],
    "B9": ["16:30", "19:30", "21:30"]
}

date_re = re.compile(r'(\d{1,2})-(sept|oct)\.')

# --- Fonctions d'extraction de données ---
def extract_dates_from_row(row):
    """Extrait les dates d'une ligne de tableau."""
    dates = []
    for cell in row:
        if cell and date_re.match(cell.strip()):
            dates.append(cell.strip())
    return dates

# --- Téléchargement du fichier PDF depuis Google Drive ---
print(f"Téléchargement du fichier depuis l'URL : {PDF_URL}")
try:
    response = requests.get(PDF_URL, timeout=30)
    response.raise_for_status() # Lève une exception pour les codes d'état d'erreur HTTP
    with open(PDF_FILE, "wb") as f:
        f.write(response.content)
    print("Fichier PDF téléchargé avec succès !")
except requests.exceptions.RequestException as e:
    print(f"Erreur lors du téléchargement: {e}", file=sys.stderr)
    sys.exit(1)

# --- Traitement du PDF et génération du planning JSON ---
planning = []
try:
    with pdfplumber.open(PDF_FILE) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                header_idx = None
                for i, row in enumerate(table):
                    if any(cell and date_re.search(cell) for cell in row):
                        header_idx = i
                        break
                if header_idx is None:
                    continue

                dates = extract_dates_from_row(table[header_idx])
                
                days = []
                if header_idx + 1 < len(table):
                    for cell in table[header_idx + 1]:
                        if cell:
                            days += re.findall(r'\b(lun|mar|mer|jeu|ven|sam|dim)\b', cell)
                
                for row in table[header_idx + 2:]:
                    if row and row[0] and row[0].strip() == "CJt":
                        codes = row[1:1 + len(dates)]
                        for idx, date_str in enumerate(dates):
                            code = codes[idx].strip() if idx < len(codes) and codes[idx] else ""
                            if code in horaires:
                                jour, mois_str = date_re.match(date_str).groups()
                                mois = 9 if mois_str == "sept" else 10
                                date_iso = datetime(datetime.now().year, mois, int(jour)).strftime("%Y-%m-%d")
                                planning.append({
                                    "date": date_iso,
                                    "day": days[idx] if idx < len(days) else "",
                                    "code": code,
                                    "time_slots": horaires[code]
                                })
                        break
except Exception as e:
    print(f"Erreur lors du traitement du PDF : {e}", file=sys.stderr)
    sys.exit(1)
finally:
    # --- Nettoyage du fichier PDF téléchargé ---
    if os.path.exists(PDF_FILE):
        os.remove(PDF_FILE)

# --- Sauvegarde du JSON ---
try:
    with open("planning.json", "w") as f:
        json.dump(planning, f, indent=2)
    print("planning.json généré avec succès !")
except Exception as e:
    print(f"Erreur lors de la sauvegarde du fichier JSON : {e}", file=sys.stderr)
    sys.exit(1)