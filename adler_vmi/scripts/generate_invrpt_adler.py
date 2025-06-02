import os
import pandas as pd
from datetime import datetime, timedelta
import glob

# Répertoires
DATA_DIR = os.path.expanduser("~/edi/data")
OUT_DIR = os.path.expanduser("~/edi/outgoing")
os.makedirs(OUT_DIR, exist_ok=True)
FEED_KEY = "WHYQI"

# Colonnes attendues par Amazon
AMAZON_COLUMNS = [
    "ISBN",
    "EAN",
    "VENDOR_STOCK_ID",
    "TITLE",
    "QTY_ON_HAND",
    "LIST_PRICE_EXCL_TAX",
    "LIST_PRICE_INCL_TAX",
    "COST_PRICE",
    "DISCOUNT",
    "ISO_CURRENCY_CODE",
]

def cleanup_old_retail_files():
    """Supprime les fichiers RETAIL_FEED_*.TXT vieux de plus de 7 jours."""
    files = glob.glob(os.path.join(OUT_DIR, "RETAIL_FEED_*.TXT"))
    threshold = datetime.now() - timedelta(days=7)

    for file_path in files:
        filename = os.path.basename(file_path)
        try:
            # Extraire la date du nom : RETAIL_FEED_<CODE>_<YYYYMMDD>_00.TXT
            date_str = filename.split("_")[-2]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < threshold:
                os.remove(file_path)
                print(f"🗑️ Supprimé : {filename}")
        except Exception as e:
            print(f"⚠️ Erreur de parsing sur {filename} : {e}")

def build_costinv(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        ean = str(row.get("ean_pcs", "")).strip()
        title = str(row.get("product_name", "")).strip()
        qty = str(row.get("available_in_warehouse_pcs", "0")).replace(",", ".").strip()

        try:
            qty_int = int(float(qty))
        except:
            qty_int = 0

        rows.append({
            "ISBN": "",
            "EAN": ean,
            "VENDOR_STOCK_ID": "",
            "TITLE": title,
            "QTY_ON_HAND": qty_int,
            "LIST_PRICE_EXCL_TAX": "",
            "LIST_PRICE_INCL_TAX": "",
            "COST_PRICE": "",
            "DISCOUNT": "",
            "ISO_CURRENCY_CODE": "EUR",
        })

    return pd.DataFrame(rows, columns=AMAZON_COLUMNS)

def main():
    # Nettoyage des anciens fichiers
    cleanup_old_retail_files()

    # Récupérer le dernier fichier stock CSV
    files = sorted([f for f in os.listdir(DATA_DIR) if f.startswith("adler_stock_")])
    if not files:
        raise FileNotFoundError("Aucun fichier stock Adler trouvé.")
    latest_csv = os.path.join(DATA_DIR, files[-1])

    df = pd.read_csv(latest_csv, sep=";")
    df.columns = df.columns.str.strip().str.lower().str.replace("\ufeff", "")

    flat_df = build_costinv(df)

    today = datetime.today().strftime("%Y%m%d")
    filename = f"RETAIL_FEED_{FEED_KEY}_{today}_00.TXT"
    out_path = os.path.join(OUT_DIR, filename)

    flat_df.to_csv(out_path, sep="|", index=False, header=True)
    print(f"✅ Fichier Amazon généré : {out_path}")

if __name__ == "__main__":
    main()

