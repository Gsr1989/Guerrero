from flask import Flask, render_template, request, redirect, url_for, send_file, session
from supabase import create_client
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

# Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Carpeta de salida de PDFs
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

    # Traer todos los permisos
    resp = supabase.table('permisos').select('*').order('fecha_expedicion', desc=True).execute()
    permisos = resp.data or []
    return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Captura de datos
        marca = request.form['marca']
        linea = request.form['linea']
        anio = request.form['anio']
        color = request.form['color']
        serie = request.form['serie']
        motor = request.form['motor']
        contribuyente = request.form['contribuyente']
        tipo_vehiculo = request.form['tipo_vehiculo']

        # Fechas
        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Folio único
        folio = f"DB{datetime.now().strftime('%d%H%M%S')}"

        # Inserción en Supabase
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

        # Generar PDF desde plantilla Guerrero.pdf
        plantilla = fitz.open("static/pdf/Guerrero.pdf")
        pt = plantilla[0]
        x, y, fs = 100, 100, 12
        datos = [
            f"FOLIO: {folio}", f"MARCA: {marca}", f"LÍNEA: {linea}", f"AÑO: {anio}",
            f"COLOR: {color}", f"SERIE: {serie}", f"MOTOR: {motor}",
            f"CONTRIBUYENTE: {contribuyente}", f"TIPO: {tipo_vehiculo}",
            f"EXPEDICIÓN: {fecha_expedicion}", f"VENCIMIENTO: {fecha_vencimiento}"
        ]
        for i, texto in enumerate(datos):
            pt.insert_text((x, y + i*20), texto, fontsize=fs)

        pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        plantilla.save(pdf_path)

        return send_file(pdf_path, as_attachment=True)

    return render_template('formulario_guerrero.html')

@app.route('/verificar_guerrero/<folio>')
def verificar_guerrero(folio):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    resp = supabase.table('permisos').select('*').eq('folio', folio).execute()
    permiso = resp.data[0] if resp.data else None
    return render_template('verificador_guerrero.html', permiso=permiso)

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
