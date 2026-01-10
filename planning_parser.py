import re
import pdfplumber
import json
import os
from datetime import datetime
import requests
import sys

# --- Configuration du lien Google Drive et des horaires ---
PDF_URL = "https://drive.google.com/uc?export=download&id=1w3ehgxdIgHCKrQpFG67qSgyUqqvBddGI"
PDF_FILE = "iFP.planning.pdf"

horaires = {
    "A4" :["9:30","10:00", "12:00", "14:00", "16:00","17:00"],
    "A5": ["9:30","10:30","12:30", "16:30", "17:30"],
    "A6": ["10:00","11:00", "13:00", "17:00", "17:30"],
    "A7": ["10:30","11:30","13:30", "17:30", "19:30", "21:30","22:30"],
    "A8": ["14:00","14:30", "18:00", "20:00", "22:00", "23:00"],
    "A9": ["14:30","15:00", "18:30", "20:30","22:30", "23:30"],
    "A10":["15:00","15:30", "19:00", "21:00","23:00", "23:30"],
    "B4": ["8:30","9:00", "11:00", "13:00", "15:00","16:00"],
    "B5": ["8:30","9:30", "11:30", "15:30", "16:30"],
    "B6": ["9:00","10:00", "12:00", "16:00", "16:30"],
    "B7": ["9:30","10:30", "12:30", "16:30", "18:30", "20:30","21:30"],
    "B8": ["13:00","13:30", "17:00", "19:00","21:00", "22:00"],
    "B9": ["13:30","14:00", "17:30", "19:30","21:30", "22:30"],
    "B10":["14:00","14:30", "18:00", "20:00","22:00", "22:30"],
    "Z4": ["10:30","11:00", "13:00", "15:00", "18:00", "18:30"],
    "Z5": ["10:30", "11:30","13:30", "15:30", "18:30", "19:00"],
    "Z6": ["11:00", "12:00","14:00", "16:00", "19:00","21:00", "22:00"],
    "Z7": ["11:30","12:30", "14:30", "16:30", "19:30", "21:30", "22:30"],
    "Z8": ["16:00","17:00", "20:00", "22:00", "23:00"],
    "Z9": ["16:30","17:30", "20:30", "22:30", "23:00"]
}

mois_map = {"janv": 1, "févr": 2, "mars": 3, "avr": 4, "mai": 5, "juin": 6, "juil": 7, "août": 8, "sept": 9, "oct": 10, "nov": 11, "déc": 12}
date_re = re.compile(r'(\d{1,2})-(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.')

# --- Fonctions d'extraction de données ---
def extract_dates_from_page_text(page_text):
    """Extrait toutes les dates d'un texte de page."""
    return [match.group(0) for match in date_re.finditer(page_text)]

# --- Téléchargement du fichier PDF depuis Google Drive ---
print(f"Téléchargement du fichier depuis l'URL : {PDF_URL}")
try:
    response = requests.get(PDF_URL, timeout=30)
    response.raise_for_status()
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
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            dates = extract_dates_from_page_text(page_text)

            # Si aucune date n'est trouvée sur la page, on passe à la suivante
            if not dates:
                continue

            tables = page.extract_tables()
            for table in tables:
                cjt_row_data = None
                day_names = []
                for i, row in enumerate(table):
                    # Chercher la ligne des jours
                    if not day_names and any(re.findall(r'\b(lun|mar|mer|jeu|ven|sam|dim)\b', cell or '') for cell in row):
                        day_names = [re.findall(r'\b(lun|mar|mer|jeu|ven|sam|dim)\b', cell or '') for cell in row]
                        day_names = [item for sublist in day_names for item in sublist]
                    
                    # Chercher la ligne "CJt" et extraire les codes
                    if row and row[0] and row[0].strip() == "CJt":
                        cjt_row_data = row[1:1 + len(dates)]
                        break
                
                # Si la ligne "CJt" est trouvée, on traite les données
                if cjt_row_data:
                    for idx, date_str in enumerate(dates):
                        if idx >= len(cjt_row_data) or not cjt_row_data[idx]:
                            continue
                            
                        code = cjt_row_data[idx].strip()
                        if code in horaires:
                            jour, mois_str = date_re.match(date_str).groups()
                            mois = mois_map.get(mois_str, datetime.now().month)
                            date_iso = datetime(datetime.now().year, mois, int(jour)).strftime("%Y-%m-%d")
                            planning.append({
                                "date": date_iso,
                                "day": day_names[idx] if idx < len(day_names) else "",
                                "code": code,
                                "time_slots": horaires[code]
                            })
                    break # Une fois la ligne "CJt" trouvée, on passe au tableau suivant
except Exception as e:
    print(f"Erreur lors du traitement du PDF : {e}", file=sys.stderr)
    sys.exit(1)
finally:
    if os.path.exists(PDF_FILE):
        os.remove(PDF_FILE)

# --- Sauvegarde du JSON ---
try:
    with open("planning.json", "w") as f:
        json.dump(planning, f, indent=2)
    print(f"planning.json généré avec succès ! {len(planning)} entrées créées.")
except Exception as e:
    print(f"Erreur lors de la sauvegarde du fichier JSON : {e}", file=sys.stderr)
    sys.exit(1)