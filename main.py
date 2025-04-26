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

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/inicio', methods=['POST'])
def inicio():
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']
    
    if usuario == 'admin' and contrasena == 'Nivelbasico2025':
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
        
        # Generar un folio automático
        folio = f"GR{datetime.now().strftime('%d%H%M%S')}"

        # Guardar en Supabase
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
        generar_pdf_guerrero(folio, marca, linea, anio, color, serie, motor, contribuyente, tipo_vehiculo, fecha_expedicion, fecha_vencimiento)

        return redirect(url_for('panel_guerrero'))
    
    return render_template('formulario_guerrero.html')

def generar_pdf_guerrero(folio, marca, linea, anio, color, serie, motor, contribuyente, tipo_vehiculo, fecha_expedicion, fecha_vencimiento):
    template_path = "static/pdf/Guerrero.pdf"
    output_path = f"static/pdf/{folio}.pdf"
    doc = fitz.open(template_path)
    page = doc[0]

    page.insert_text((100, 100), f"Folio: {folio}", fontsize=12)
    page.insert_text((100, 120), f"Marca: {marca}", fontsize=12)
    page.insert_text((100, 140), f"Línea: {linea}", fontsize=12)
    page.insert_text((100, 160), f"Año: {anio}", fontsize=12)
    page.insert_text((100, 180), f"Color: {color}", fontsize=12)
    page.insert_text((100, 200), f"Serie: {serie}", fontsize=12)
    page.insert_text((100, 220), f"Motor: {motor}", fontsize=12)
    page.insert_text((100, 240), f"Contribuyente: {contribuyente}", fontsize=12)
    page.insert_text((100, 260), f"Tipo de Vehículo: {tipo_vehiculo}", fontsize=12)
    page.insert_text((100, 280), f"Fecha de Expedición: {fecha_expedicion}", fontsize=12)
    page.insert_text((100, 300), f"Fecha de Vencimiento: {fecha_vencimiento}", fontsize=12)

    doc.save(output_path)
    doc.close()

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
