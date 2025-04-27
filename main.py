from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from supabase import create_client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "clave_super_segura_2025")

# ——— Supabase ———
SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ——— Carpeta de salida para los PDFs ———
OUTPUT_DIR = os.path.join("static", "pdfs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/inicio', methods=['POST'])
def inicio():
    usuario = request.form.get('usuario')
    contrasena = request.form.get('contrasena')
    if usuario == 'admin' and contrasena == 'admin123':
        session['usuario'] = usuario
        return redirect(url_for('panel_guerrero'))
    return render_template('login.html', error='Credenciales incorrectas')

@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    resp = supabase.table('permisos').select('*').execute()
    permisos = resp.data if hasattr(resp, 'data') else resp
    return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # — Recoger datos del formulario —
        marca         = request.form['marca']
        linea         = request.form['linea']
        anio          = request.form['anio']
        color         = request.form['color']
        serie         = request.form['serie']
        motor         = request.form['motor']
        contribuyente = request.form['contribuyente']
        tipo_vehiculo = request.form['tipo_vehiculo']

        fecha_expedicion  = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        folio             = f"DB{datetime.now().strftime('%d%H%M%S')}"

        # — Insertar en Supabase —
        supabase.table('permisos').insert({
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "anio": anio,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "tipo_vehiculo": tipo_vehiculo,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }).execute()

        # — Generar PDF —
        plantilla = fitz.open("static/pdf/Guerrero.pdf")
        page = plantilla[0]
        x, y = 100, 100
        for label, value in [
            ("FOLIO", folio),
            ("MARCA", marca),
            ("LINEA", linea),
            ("AÑO", anio),
            ("COLOR", color),
            ("SERIE", serie),
            ("MOTOR", motor),
            ("CONTRIBUYENTE", contribuyente),
            ("TIPO", tipo_vehiculo),
            ("EXPEDICIÓN", fecha_expedicion),
            ("VENCIMIENTO", fecha_vencimiento)
        ]:
            page.insert_text((x, y), f"{label}: {value}", fontsize=12)
            y += 20

        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        plantilla.save(pdf_path)
        return send_file(pdf_path, as_attachment=True)

    return render_template('formulario_guerrero.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
