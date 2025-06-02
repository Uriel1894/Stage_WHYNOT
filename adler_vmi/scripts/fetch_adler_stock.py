import os
import requests
from datetime import datetime, timedelta
import glob

# URL du stock Adler
CSV_URL = "https://www.adler.com.pl/index.php/GetCSV/warcsv2/136"

# Dossier de sortie
OUT_DIR = os.path.expanduser("~/edi/data")
os.makedirs(OUT_DIR, exist_ok=True)
today = datetime.utcnow().strftime("%Y%m%d")
OUT_CSV = os.path.join(OUT_DIR, f"adler_stock_{today}.csv")

def cleanup_old_stock_files():
    """Supprime les fichiers CSV de stock vieux de plus de 7 jours."""
    pattern = os.path.join(OUT_DIR, "adler_stock_*.csv")
    files = glob.glob(pattern)
    threshold = datetime.utcnow() - timedelta(days=7)

    for file_path in files:
        filename = os.path.basename(file_path)
        try:
            date_str = filename.split("_")[-1].replace(".csv", "")
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < threshold:
                os.remove(file_path)
                print(f"🗑️ Supprimé : {filename}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la lecture de la date dans {filename} : {e}")

def fetch_stock_csv():
    print(f"📥 Téléchargement du stock depuis {CSV_URL}")
    response = requests.get(CSV_URL)
    response.raise_for_status()

    with open(OUT_CSV, "wb") as f:
        f.write(response.content)
    print(f"✅ Stock Adler sauvegardé dans {OUT_CSV}")

if __name__ == "__main__":
    cleanup_old_stock_files()
    fetch_stock_csv()

