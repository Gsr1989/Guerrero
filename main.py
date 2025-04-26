from flask import Flask, render_template, request, redirect, url_for, session, send_file
from supabase import create_client
from datetime import datetime, timedelta
import fitz  # PyMuPDF para generar PDFs
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

# Configuración de Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ruta donde se guardarán los PDFs
OUTPUT_DIR = 'static/pdfs'
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
    if 'usuario' in session:
        return render_template('panel_guerrero.html')
    else:
        return redirect(url_for('login'))

@app.route('/formulario_guerrero', methods=['GET', 'POST'])
def formulario_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        modelo = request.form['modelo'].upper()
        color = request.form['color'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        contribuyente = request.form['contribuyente'].upper()
        tipo_vehiculo = request.form['tipo_vehiculo'].upper()

        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        folio = f"GRO{datetime.now().strftime('%d%H%M%S')}"

        # Guardar en Supabase
        supabase.table('permisos_guerrero').insert({
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "anio": modelo,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "tipo_vehiculo": tipo_vehiculo,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }).execute()

        # Generar PDF
        generar_pdf(folio, marca, linea, modelo, color, serie, motor, contribuyente, tipo_vehiculo, fecha_expedicion, fecha_vencimiento)

        return redirect(url_for('verificador_guerrero', folio=folio))

    return render_template('formulario_guerrero.html')

def generar_pdf(folio, marca, linea, modelo, color, serie, motor, contribuyente, tipo_vehiculo, fecha_expedicion, fecha_vencimiento):
    plantilla = fitz.open('static/img/Guerrero.pdf')
    pagina = plantilla[0]

    # Insertar textos (puedes ajustar las coordenadas X, Y según se necesite)
    pagina.insert_text((100, 100), f"Folio: {folio}", fontsize=12, color=(1, 0, 0))
    pagina.insert_text((100, 120), f"Marca: {marca}", fontsize=11)
    pagina.insert_text((100, 140), f"Línea: {linea}", fontsize=11)
    pagina.insert_text((100, 160), f"Modelo: {modelo}", fontsize=11)
    pagina.insert_text((100, 180), f"Color: {color}", fontsize=11)
    pagina.insert_text((100, 200), f"Serie: {serie}", fontsize=11)
    pagina.insert_text((100, 220), f"Motor: {motor}", fontsize=11)
    pagina.insert_text((100, 240), f"Contribuyente: {contribuyente}", fontsize=11)
    pagina.insert_text((100, 260), f"Tipo de Vehículo: {tipo_vehiculo}", fontsize=11)
    pagina.insert_text((100, 280), f"Expedición: {fecha_expedicion}", fontsize=11)
    pagina.insert_text((100, 300), f"Vencimiento: {fecha_vencimiento}", fontsize=11)

    output_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
    plantilla.save(output_path)
    plantilla.close()

@app.route('/verificador_guerrero/<folio>')
def verificador_guerrero(folio):
    data = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute()
    if data.data:
        permiso = data.data[0]
        return render_template('verificador_guerrero.html', permiso=permiso)
    else:
        return "Permiso no encontrado."

@app.route('/editar_guerrero/<folio>', methods=['GET', 'POST'])
def editar_guerrero(folio):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        modelo = request.form['modelo'].upper()
        color = request.form['color'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        contribuyente = request.form['contribuyente'].upper()
        tipo_vehiculo = request.form['tipo_vehiculo'].upper()

        supabase.table('permisos_guerrero').update({
            "marca": marca,
            "linea": linea,
            "anio": modelo,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "tipo_vehiculo": tipo_vehiculo
        }).eq('folio', folio).execute()

        return redirect(url_for('panel_guerrero'))

    data = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute()
    if data.data:
        permiso = data.data[0]
        return render_template('editar_guerrero.html', permiso=permiso)
    else:
        return "Permiso no encontrado."

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
