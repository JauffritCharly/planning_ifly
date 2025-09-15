import re
import pdfplumber
import json
import os
from datetime import datetime

# --- Configuration des horaires ---
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

PDF_FILE = "iFP.planning.pdf"
date_re = re.compile(r'(\d{1,2})-(sept|oct)\.')

def extract_dates_from_row(row):
    dates = []
    for cell in row:
        if not cell:
            continue
        for tok in re.split(r'\s+', cell.strip()):
            if date_re.match(tok):
                dates.append(tok)
    return dates

planning = []

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

# --- Suppression de l'ancien planning.json ---
if os.path.exists("planning.json"):
    os.remove("planning.json")

# --- Sauvegarde JSON ---
with open("planning.json", "w") as f:
    json.dump(planning, f, indent=2)

print("planning.json généré avec succès !")