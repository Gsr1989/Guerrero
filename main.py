from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from supabase import create_client, Client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

# Datos de conexión a Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Carpeta de PDFs
OUTPUT_DIR = "static/pdfs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# ---------------- RUTAS ------------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin123':
            session['usuario'] = username
            return redirect(url_for('panel_guerrero'))
        else:
            return render_template('login.html', error="Credenciales incorrectas")
    return render_template('login.html')

@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' in session:
        permisos = supabase.table('permisos').select('*').execute().data
        return render_template('panel_guerrero.html', permisos=permisos)
    else:
        return redirect(url_for('login'))

@app.route('/formulario_guerrero', methods=['GET', 'POST'])
def formulario_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        año = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        nombre = request.form['nombre'].upper()

        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        folio = f"DB{datetime.now().strftime('%d%H%M%S')}"

        # Insertar en Supabase
        supabase.table('permisos').insert({
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "anio": año,
            "color": color,
            "serie": serie,
            "motor": motor,
            "nombre": nombre,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }).execute()

        # Generar PDF
        plantilla = fitz.open("static/pdf/Guerrero.pdf")
        page = plantilla[0]
        page.insert_text((100, 100), f"FOLIO: {folio}", fontsize=12)
        page.insert_text((100, 120), f"MARCA: {marca}", fontsize=12)
        page.insert_text((100, 140), f"LINEA: {linea}", fontsize=12)
        page.insert_text((100, 160), f"AÑO: {año}", fontsize=12)
        page.insert_text((100, 180), f"COLOR: {color}", fontsize=12)
        page.insert_text((100, 200), f"SERIE: {serie}", fontsize=12)
        page.insert_text((100, 220), f"MOTOR: {motor}", fontsize=12)
        page.insert_text((100, 240), f"NOMBRE: {nombre}", fontsize=12)
        page.insert_text((100, 260), f"EXPEDICIÓN: {fecha_expedicion}", fontsize=12)
        page.insert_text((100, 280), f"VENCIMIENTO: {fecha_vencimiento}", fontsize=12)

        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        plantilla.save(pdf_path)

        return redirect(url_for('verificar_guerrero'))

    return render_template('formulario_guerrero.html')

@app.route('/verificar_guerrero', methods=['GET', 'POST'])
def verificar_guerrero():
    permiso = None
    if request.method == 'POST':
        folio = request.form['folio'].strip().upper()
        result = supabase.table('permisos').select('*').eq('folio', folio).execute()
        if result.data:
            permiso = result.data[0]
    return render_template('verificador_guerrero.html', permiso=permiso)

@app.route('/descargar/<folio>')
def descargar(folio):
    ruta_pdf = f"static/pdfs/{folio}.pdf"
    if os.path.exists(ruta_pdf):
        return send_file(ruta_pdf, as_attachment=True)
    else:
        return "Archivo no encontrado"

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

# -------------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
