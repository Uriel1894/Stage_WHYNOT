import os
import shutil
from datetime import datetime

# Répertoire des fichiers Amazon générés
OUT_DIR = os.path.expanduser("~/edi/outgoing")

# Mapping des Vendor Codes par pays
VENDOR_CODES = {
    "FR": "WHYQI",
    "DE": "WHZA1",
    "ES": "WHZ9J",
    "IT": "WHZ9I",
    "SE": "WHZA0",
    "NL": "WHZ9N",
    "BE": "WHZB4",
    "PL": "WHZ9Y"
}

def duplicate_retail_feed_for_all_countries():
    today = datetime.today().strftime("%Y%m%d")
    origin_vendor_code = "WHYQI"
    origin_filename = f"RETAIL_FEED_{origin_vendor_code}_{today}_00.TXT"
    origin_path = os.path.join(OUT_DIR, origin_filename)

    if not os.path.exists(origin_path):
        print(f"❌ Fichier source introuvable : {origin_filename}")
        return

    for country, vendor_code in VENDOR_CODES.items():
        if vendor_code == origin_vendor_code:
            continue  # ne pas dupliquer le fichier FR déjà généré
        target_filename = f"RETAIL_FEED_{vendor_code}_{today}_00.TXT"
        target_path = os.path.join(OUT_DIR, target_filename)

        try:
            shutil.copyfile(origin_path, target_path)
            print(f"✅ Fichier dupliqué pour {country} → {target_filename}")
        except Exception as e:
            print(f"⚠️ Erreur lors de la copie pour {vendor_code} : {e}")

if __name__ == "__main__":
    duplicate_retail_feed_for_all_countries()

