#!/usr/bin/env python3

import subprocess
from datetime import datetime

scripts = [
    "fetch_adler_stock.py",
    "generate_invrpt_adler.py",
    "duplicate_invrpt_multi_country.py",  # désactivé temporairement
    "send_adler_to_amazon_sftp.py"
]

for script in scripts:
    print(f"\n🚀 Exécution : {script}")
    result = subprocess.run(
        ["/home/ubuntu/edi/venv/bin/python", f"/home/ubuntu/edi/scripts/{script}"],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ Erreur dans {script} :\n{result.stderr}")
        break
else:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n✅ Pipeline terminé avec succès à {now}")

