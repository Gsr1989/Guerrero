from flask import Flask, render_template, request, redirect, url_for, send_file, session
from supabase import create_client, Client
from datetime import datetime, timedelta
import qrcode
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- GENERADOR DE FOLIOS ---
def generar_folio():
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if not os.path.exists("folios.txt"):
        with open("folios.txt", "w") as f:
            f.write("BC0000")
    with open("folios.txt", "r") as f:
        ultimo = f.readlines()[-1].strip()
    letras_actuales = ultimo[:2]
    numero_actual = int(ultimo[2:])
    if numero_actual < 9999:
        nuevo_folio = f"{letras_actuales}{numero_actual + 1:04d}"
    else:
        l1 = letras.index(letras_actuales[0])
        l2 = letras.index(letras_actuales[1])
        if l2 < 25:
            l2 += 1
        else:
            l1 = (l1 + 1) % 26
            l2 = 0
        nuevo_folio = f"{letras[l1]}{letras[l2]}0001"
    with open("folios.txt", "a") as f:
        f.write("\n" + nuevo_folio)
    return nuevo_folio

# --- GENERADOR QR ---
def generar_qr(folio, datos):
    qr = qrcode.make(datos)
    qr_path = os.path.join("static", "qrs", f"{folio}.png")
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr.save(qr_path)
    return qr_path

# --- RUTAS ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['usuario'] == 'admin' and request.form['contrasena'] == 'admin123':
            session['usuario'] = 'admin'
            return redirect(url_for('panel'))
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    permisos = supabase.table('permisos_guerrero').select('*').execute().data
    return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        anio = request.form['anio'].upper()
        color = request.form['color'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        contribuyente = request.form['contribuyente'].upper()
        fecha_expedicion = datetime.now().strftime("%d/%m/%Y")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        folio = generar_folio()

        datos_qr = f"FOLIO: {folio}\nMARCA: {marca}\nSERIE: {serie}\nCONTRIBUYENTE: {contribuyente}"
        qr_path = generar_qr(folio, datos_qr)

        supabase.table('permisos_guerrero').insert({
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "anio": anio,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }).execute()

        doc = fitz.open("static/pdf/Guerrero.pdf")
        page = doc[0]
        page.insert_text((100, 100), f"FOLIO: {folio}", fontsize=12)
        page.insert_text((100, 120), f"MARCA: {marca}", fontsize=12)
        page.insert_text((100, 140), f"LINEA: {linea}", fontsize=12)
        page.insert_text((100, 160), f"AÑO: {anio}", fontsize=12)
        page.insert_text((100, 180), f"COLOR: {color}", fontsize=12)
        page.insert_text((100, 200), f"SERIE: {serie}", fontsize=12)
        page.insert_text((100, 220), f"MOTOR: {motor}", fontsize=12)
        page.insert_text((100, 240), f"CONTRIBUYENTE: {contribuyente}", fontsize=12)
        page.insert_text((100, 260), f"EXPEDICIÓN: {fecha_expedicion}", fontsize=12)
        page.insert_text((100, 280), f"VENCIMIENTO: {fecha_vencimiento}", fontsize=12)
        rect = fitz.Rect(400, 100, 500, 200)
        page.insert_image(rect, filename=qr_path)
        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        doc.save(pdf_path)

        return redirect(url_for('panel'))
    return render_template('formulario_guerrero.html')

@app.route('/editar/<folio>', methods=['GET', 'POST'])
def editar(folio):
    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        anio = request.form['anio'].upper()
        color = request.form['color'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        contribuyente = request.form['contribuyente'].upper()
        supabase.table('permisos_guerrero').update({
            "marca": marca,
            "linea": linea,
            "anio": anio,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente
        }).eq('folio', folio).execute()
        return redirect(url_for('panel'))
    permiso = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute().data[0]
    return render_template('editar_guerrero.html', permiso=permiso)

@app.route('/eliminar/<folio>')
def eliminar(folio):
    supabase.table('permisos_guerrero').delete().eq('folio', folio).execute()
    pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    return redirect(url_for('panel'))

@app.route('/descargar/<folio>')
def descargar(folio):
    pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "PDF no encontrado", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
