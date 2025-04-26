from flask import Flask, render_template, request, redirect, url_for, send_file, session
from datetime import datetime, timedelta
from supabase import create_client, Client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXci"
    "LCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYw"
    "NzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ruta al PDF plantilla
TEMPLATE_PATH = os.path.join("static", "pdf", "Guerrero.pdf")
# Carpeta donde se guardarán los PDFs generados
OUTPUT_DIR = os.path.join("static", "pdfs")
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
    # Traer todos los permisos para listarlos
    resp = supabase.table('permisos').select('*').execute()
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

        # Generar PDF a partir de la plantilla
        doc = fitz.open(TEMPLATE_PATH)
        page = doc[0]
        y = 100
        for label, value in [
            ("FOLIO", folio),
            ("MARCA", marca),
            ("LÍNEA", linea),
            ("AÑO", anio),
            ("COLOR", color),
            ("SERIE", serie),
            ("MOTOR", motor),
            ("CONTRIBUYENTE", contribuyente),
            ("TIPO", tipo_vehiculo),
            ("EXPEDICIÓN", fecha_expedicion),
            ("VENCIMIENTO", fecha_vencimiento),
        ]:
            page.insert_text((100, y), f"{label}: {value}", fontsize=12)
            y += 20

        output_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        doc.save(output_path)
        doc.close()

        return send_file(output_path, as_attachment=True)

    return render_template('formulario_guerrero.html')


@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
