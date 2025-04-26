from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from supabase import create_client, Client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://iuwsippnvyynxanvn.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

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
    if 'usuario' in session:
        return render_template('panel_guerrero.html')
    else:
        return redirect(url_for('login'))

@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
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

        # Insertar en Supabase
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

        # Generar PDF
        plantilla = fitz.open("static/pdf/Guerrero.pdf")
        page = plantilla[0]
        page.insert_text((100, 100), f"FOLIO: {folio}", fontsize=12)
        page.insert_text((100, 120), f"MARCA: {marca}", fontsize=12)
        page.insert_text((100, 140), f"LÍNEA: {linea}", fontsize=12)
        page.insert_text((100, 160), f"MODELO: {anio}", fontsize=12)
        page.insert_text((100, 180), f"COLOR: {color}", fontsize=12)
        page.insert_text((100, 200), f"SERIE: {serie}", fontsize=12)
        page.insert_text((100, 220), f"MOTOR: {motor}", fontsize=12)
        page.insert_text((100, 240), f"CONTRIBUYENTE: {contribuyente}", fontsize=12)
        page.insert_text((100, 260), f"TIPO: {tipo_vehiculo}", fontsize=12)
        page.insert_text((100, 280), f"EXPEDICIÓN: {fecha_expedicion}", fontsize=12)
        page.insert_text((100, 300), f"VENCIMIENTO: {fecha_vencimiento}", fontsize=12)

        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        plantilla.save(pdf_path)

        return send_file(pdf_path, as_attachment=True)

    return render_template('formulario_guerrero.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
