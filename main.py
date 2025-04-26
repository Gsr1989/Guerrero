from flask import Flask, render_template, request, redirect, url_for, session, send_file
from supabase import create_client, Client
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ruta raíz
@app.route('/')
def login():
    return render_template('login.html')

# Procesar login
@app.route('/inicio', methods=['POST'])
def inicio():
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']
    if usuario == 'admin' and contrasena == 'admin123':
        session['usuario'] = usuario
        return redirect(url_for('panel_guerrero'))
    else:
        return render_template('login.html', error='Credenciales incorrectas')

# Panel principal
@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' in session:
        permisos = supabase.table('permisos_guerrero').select('*').execute().data
        return render_template('panel_guerrero.html', permisos=permisos)
    else:
        return redirect(url_for('login'))

# Registrar nuevo permiso
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

        fecha_expedicion = datetime.now().strftime("%d/%m/%Y")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        folio = f"GR-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Guardar en la base de datos
        supabase.table('permisos_guerrero').insert({
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

        # Generar el PDF
        plantilla_path = 'static/pdf/Guerrero.pdf'
        salida_path = f'static/pdf/{folio}.pdf'

        doc = fitz.open(plantilla_path)
        page = doc[0]

        # Escribir texto (ajustar coordenadas si quieres mover)
        page.insert_text((150, 150), f"Folio: {folio}", fontsize=12)
        page.insert_text((150, 180), f"Contribuyente: {contribuyente}", fontsize=12)
        page.insert_text((150, 210), f"Marca: {marca}", fontsize=12)
        page.insert_text((150, 240), f"Línea: {linea}", fontsize=12)
        page.insert_text((150, 270), f"Año: {anio}", fontsize=12)
        page.insert_text((150, 300), f"Color: {color}", fontsize=12)
        page.insert_text((150, 330), f"Serie: {serie}", fontsize=12)
        page.insert_text((150, 360), f"Motor: {motor}", fontsize=12)
        page.insert_text((150, 390), f"Tipo de Vehículo: {tipo_vehiculo}", fontsize=12)
        page.insert_text((150, 420), f"Fecha Expedición: {fecha_expedicion}", fontsize=12)
        page.insert_text((150, 450), f"Fecha Vencimiento: {fecha_vencimiento}", fontsize=12)

        doc.save(salida_path)
        doc.close()

        return redirect(url_for('panel_guerrero'))

    return render_template('formulario_guerrero.html')

# Verificar permiso
@app.route('/verificar_guerrero/<folio>')
def verificar_guerrero(folio):
    permiso = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute().data
    if permiso:
        return render_template('verificador_guerrero.html', permiso=permiso[0])
    else:
        return "Permiso no encontrado"

# Editar permiso
@app.route('/editar_guerrero/<folio>', methods=['GET', 'POST'])
def editar_guerrero(folio):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = {
            "marca": request.form['marca'],
            "linea": request.form['linea'],
            "anio": request.form['anio'],
            "color": request.form['color'],
            "serie": request.form['serie'],
            "motor": request.form['motor'],
            "contribuyente": request.form['contribuyente'],
            "tipo_vehiculo": request.form['tipo_vehiculo']
        }
        supabase.table('permisos_guerrero').update(data).eq('folio', folio).execute()
        return redirect(url_for('panel_guerrero'))

    permiso = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute().data
    if permiso:
        return render_template('editar_guerrero.html', permiso=permiso[0])
    else:
        return "Permiso no encontrado"

# Cerrar sesión
@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
