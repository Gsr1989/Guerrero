# src/main.py
from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from supabase import create_client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

# Lee estas variables de entorno en producción
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://axgqvhgtbzkraytzaomw.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "<TU_SERVICE_ROLE_KEY>")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/inicio', methods=['POST'])
def inicio():
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']

    if usuario == 'admin' and contrasena == 'admin123':
        session['usuario'] = usuario
        return redirect(url_for('panel_guerrero'))
    else:
        return render_template('login.html', error='Credenciales incorrectas')

@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    # Trae todos los permisos, ordenados por fecha de expedición descendente
    resp = supabase.table('permisos')\
        .select('*')\
        .order('fecha_expedicion', desc=True)\
        .execute()
    permisos = resp.data or []
    return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca']
        linea = request.form['linea']
        anio = request.form['anio']
        color = request.form['color']
        serie = request.form['serie']
        motor = request.form['motor']
        contribuyente = request.form['contribuyente']
        tipo_vehiculo = request.form['tipo_vehiculo']

        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        folio = f"DB{datetime.now().strftime('%d%H%M%S')}"

        # Inserta en Supabase
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

        # Genera el PDF sobre la plantilla
        plantilla = fitz.open("static/pdf/Guerrero.pdf")
        page = plantilla[0]
        datos = [
            ("FOLIO", folio),
            ("MARCA", marca),
            ("LÍNEA", linea),
            ("AÑO", anio),
            ("COLOR", color),
            ("SERIE", serie),
            ("MOTOR", motor),
            ("CONTRIBUYENTE", contribuyente),
            ("TIPO VEHÍCULO", tipo_vehiculo),
            ("EXPEDICIÓN", fecha_expedicion),
            ("VENCIMIENTO", fecha_vencimiento),
        ]
        y = 100
        for etiqueta, valor in datos:
            page.insert_text((100, y), f"{etiqueta}: {valor}", fontsize=12)
            y += 20

        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        plantilla.save(pdf_path)
        plantilla.close()

        return send_file(pdf_path, as_attachment=True)

    return render_template('formulario_guerrero.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
