from flask import Flask, request, redirect, url_for, session, render_template, send_file, flash
import os
import pandas as pd
import paramiko
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import json
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
app.permanent_session_lifetime = timedelta(minutes=30)

UPLOAD_FOLDER = 'uploads/fornor'
RETAIL_FOLDER = 'outgoing/fornor'
USERS_FILE = 'users.json'
LOG_FILE = "logs/fornor_uploads.json"

FEED_KEYS_FORNOR = {
    "FR": "WHYQI",
    "DE": "WHZA1",
    "ES": "WHZ9J",
    "IT": "WHZ9I",
    "SE": "WHZA0",
    "NL": "WHZ9N",
    "BE": "WHZB4",
    "PL": "WHZ9Y"
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

users = load_users()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Les mots de passe ne correspondent pas.", 400

        if username in users:
            return "Ce nom d'utilisateur existe déjà.", 400

        users[username] = {
            'email': email,
            'password': generate_password_hash(password)
        }
        save_users(users)
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()
        user = users.get(username)

        if user and check_password_hash(user['password'], password):
            session.permanent = True
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('upload_fornor'))

        return render_template("login_error.html"), 401

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def cleanup_old_csv_files():
    now = datetime.now()
    for folder, ext in [(UPLOAD_FOLDER, ".csv"), (RETAIL_FOLDER, ".TXT")]:
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            if os.path.isfile(file_path) and file.endswith(ext):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (now - file_mtime).days > 7:
                    os.remove(file_path)

def get_uploaded_files():
    file_list = []
    for file in os.listdir(UPLOAD_FOLDER):
        if file.endswith(".csv"):
            full_path = os.path.join(UPLOAD_FOLDER, file)
            mod_time = os.path.getmtime(full_path)
            formatted_time = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d %H:%M")
            file_list.append((file, formatted_time))
    return sorted(file_list, key=lambda x: x[1], reverse=True)

def log_upload_status(filename, status, message=""):
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, 'r') as f:
                logs = json.load(f)
        except json.JSONDecodeError:
            logs = []

    logs.append({
        "file": filename,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "message": message
    })

    with open(LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=4)

def send_file_to_amazon(filepath):
    filename = os.path.basename(filepath)
    try:
        key = paramiko.RSAKey.from_private_key_file(os.path.expanduser("~/.ssh/amazon_send_key_new"))
        transport = paramiko.Transport(("eu-sftp.amazonsedi.com", 22))
        transport.connect(username="3TWLLYQQ0WSGN", pkey=key)

        sftp = paramiko.SFTPClient.from_transport(transport)
        remote_path = f"upload/{filename}"
        sftp.put(filepath, remote_path)
        print(f"✅ Fichier {filename} envoyé vers {remote_path}")
        log_upload_status(filename, "succès")
    except Exception as e:
        print(f"❌ Erreur SFTP : {e}")
        log_upload_status(filename, "échec", str(e))
    finally:
        try:
            sftp.close()
            transport.close()
        except:
            pass

@app.route('/', methods=['GET', 'POST'])
def upload_fornor():
    if not session.get('logged_in'):
        flash("Votre session a expiré. Veuillez vous reconnecter.")
        return redirect(url_for('login'))

    cleanup_old_csv_files()

    if request.method == 'POST':
        try:
            file = request.files['file']
            if file and file.filename.endswith('.csv'):
                csv_path = os.path.join(UPLOAD_FOLDER, file.filename)
                file.save(csv_path)

                try:
                    df = pd.read_csv(csv_path, encoding='utf-8', sep=None, engine='python', on_bad_lines='skip')
                except UnicodeDecodeError:
                    df = pd.read_csv(csv_path, encoding='latin1', sep=None, engine='python', on_bad_lines='skip')

                df.rename(columns={
                    'code barre': 'EAN',
                    'Stock disponible': 'STOCK',
                    'Article': 'REF.FOURNISSEUR'
                }, inplace=True)

                required_columns = {'EAN', 'STOCK', 'REF.FOURNISSEUR'}
                if not required_columns.issubset(df.columns):
                    return f"Erreur : colonnes manquantes après renommage. Colonnes attendues : {required_columns}", 400

                df_retail = pd.DataFrame()
                df_retail['EAN'] = df['EAN'].astype(str).str.strip()
                df_retail['QTY_ON_HAND'] = df['STOCK'].astype(str).str.strip()
                df_retail['VENDOR_STOCK_ID'] = df['REF.FOURNISSEUR'].astype(str).str.strip()
                df_retail['LIST_PRICE_EXCL_TAX'] = ""
                df_retail['COST_PRICE'] = ""
                df_retail['ISO_CURRENCY_CODE'] = "EUR"

                today = datetime.today().strftime("%Y%m%d")
                brand_name = os.environ.get("BRAND_NAME", "FORNOR")

                for country, feed_key in FEED_KEYS_FORNOR.items():
                    filename = f"RETAIL_FEED_{feed_key}_{today}_00.TXT"
                    filepath = os.path.join(RETAIL_FOLDER, filename)
                    df_retail.to_csv(filepath, sep='|', index=False)
                    send_file_to_amazon(filepath)

                return render_template("upload_complete.html", file_generated=f"RETAIL_FEED_{list(FEED_KEYS_FORNOR.values())[0]}_{today}_00.TXT")

            else:
                return "Erreur : fichier invalide ou extension incorrecte (.csv requis)", 400
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"Erreur interne : {str(e)}", 500

    return render_template("upload_fornor.html", file_list=get_uploaded_files())

@app.route('/download/<filename>')
def download_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return send_file(os.path.join(RETAIL_FOLDER, filename), as_attachment=True)

@app.route('/historique')
def historique():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    try:
        with open(LOG_FILE, 'r') as f:
            uploads = json.load(f)
    except:
        uploads = []

    return render_template("historique.html", uploads=uploads)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)

