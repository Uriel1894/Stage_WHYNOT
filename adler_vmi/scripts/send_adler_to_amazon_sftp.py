import os
import glob
import paramiko
from datetime import datetime

# Configuration SFTP Amazon pour Adler
HOST = "eu-sftp.amazonsedi.com"
PORT = 22
USERNAME = "3TWLLYQQ0WSGN"  # User SFTP Adler
PRIVATE_KEY = os.path.expanduser("~/.ssh/amazon_send_key_new")
REMOTE_DIR = "upload"
LOCAL_DIR = os.path.expanduser("~/edi/outgoing")

def send_all_adler_files_today():
    today = datetime.today().strftime("%Y%m%d")

    # Recherche de tous les fichiers enfants WHZ* et aussi du parent WHYQI
    pattern_children = os.path.join(LOCAL_DIR, f"RETAIL_FEED_WHZ*_{today}_00.TXT")
    pattern_parent = os.path.join(LOCAL_DIR, f"RETAIL_FEED_WHYQI_{today}_00.TXT")

    files = sorted(glob.glob(pattern_children)) + glob.glob(pattern_parent)

    if not files:
        print("⚠️ Aucun fichier à envoyer pour aujourd'hui.")
        return

    # Connexion SFTP
    key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY)
    transport = paramiko.Transport((HOST, PORT))
    transport.connect(username=USERNAME, pkey=key)
    sftp = paramiko.SFTPClient.from_transport(transport)

    try:
        for file_path in files:
            filename = os.path.basename(file_path)
            remote_path = f"{REMOTE_DIR}/{filename}"
            print(f"📤 Envoi de {filename} vers {remote_path}")
            sftp.put(file_path, remote_path)
            print("✅ Fichier envoyé avec succès.")
    finally:
        sftp.close()
        transport.close()

if __name__ == "__main__":
    send_all_adler_files_today()

