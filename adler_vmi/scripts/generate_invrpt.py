#!/usr/bin/env python3
import os
import pandas as pd
from datetime import datetime

def build_invrpt(df: pd.DataFrame) -> str:
    # En-tête UNH
    now = datetime.utcnow()
    segments = [
        f"UNH+1+INVRPT:D:96A:UN'",
        f" BGM+35+{now:%Y%m%d%H%M}'",
        f" DTM+137:{now:%Y%m%d}:102'"
    ]
    # Boucle LIN/QTY par SKU
    for idx, row in df.iterrows():
        segments.append(f"LIN+{idx+1}++{row['sku']}:SRV'")
        segments.append(f" QTY+145:{int(row['quantity'])}'")
    # Fin du message  
    segments.append(f" UNS+S'")
    segments.append(f" UNT+{len(segments)}+1'")
    return "\n".join(segments)

if __name__ == "__main__":
    df = pd.read_csv(os.path.expanduser("~/edi/data/stock.csv"))
    edi = build_invrpt(df)
    out_name = os.path.expanduser(
        f"~/edi/outgoing/WHYQI_INVRPT_{datetime.utcnow():%Y%m%d}.edi"
    )
    with open(out_name, "w") as f:
        f.write(edi)
    print(f"Fichier EDI généré → {out_name}")
