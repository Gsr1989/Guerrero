from flask import Flask, render_template, request, redirect, url_for, session, send_file
from datetime import datetime, timedelta
import os
import fitz  # PyMuPDF
import pytz
import qrcode
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = 'clave_muy_segura_123456'

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username == 'admin' and password == 'admin123':
        session['usuario'] = username
        return redirect(url_for('panel_guerrero'))
    else:
        return render_template('login.html', error="Incorrect credentials.")

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('index'))

@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    permisos = supabase.table('permisos_guerrero').select('*').execute().data
    return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
    if 'usuario' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        marca = request.form.get('marca')
        linea = request.form.get('linea')
        anio = request.form.get('anio')
        color = request.form.get('color')
        serie = request.form.get('serie')
        motor = request.form.get('motor')
        contribuyente = request.form.get('contribuyente')
        tipo_vehiculo = request.form.get('tipo_vehiculo')

        now = datetime.now(pytz.timezone('America/Mexico_City'))
        fecha_expedicion = now.strftime('%d/%m/%Y')
        fecha_vencimiento = (now + timedelta(days=90)).strftime('%d/%m/%Y')

        folio = f"GR-{now.strftime('%Y%m%d%H%M%S')}"

        # Generate QR
        qr_data = f"Folio: {folio}\nContribuyente: {contribuyente}"
        qr = qrcode.make(qr_data)
        qr_filename = os.path.join(OUTPUT_DIR, f"{folio}_qr.png")
        qr.save(qr_filename)

        # Generate PDF
        pdf_filename = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
        doc = fitz.open()
        page = doc.new_page()

        background_path = "static/img/plantilla_guerrero.png"
        if os.path.exists(background_path):
            page.insert_image(page.rect, filename=background_path)

        page.insert_text((50, 100), f"Folio: {folio}", fontsize=14, color=(0, 0, 0))
        page.insert_text((50, 130), f"Marca: {marca}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 150), f"Línea: {linea}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 170), f"Año: {anio}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 190), f"Color: {color}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 210), f"Serie: {serie}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 230), f"Motor: {motor}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 250), f"Contribuyente: {contribuyente}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 270), f"Tipo de vehículo: {tipo_vehiculo}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 300), f"Fecha de expedición: {fecha_expedicion}", fontsize=12, color=(0, 0, 0))
        page.insert_text((50, 320), f"Fecha de vencimiento: {fecha_vencimiento}", fontsize=12, color=(0, 0, 0))

        qr_rect = fitz.Rect(400, 50, 550, 200)
        page.insert_image(qr_rect, filename=qr_filename)

        doc.save(pdf_filename)
        doc.close()

        os.remove(qr_filename)

        # Save to Supabase
        supabase.table('permisos_guerrero').insert({
            'folio': folio,
            'marca': marca,
            'linea': linea,
            'anio': anio,
            'color': color,
            'serie': serie,
            'motor': motor,
            'contribuyente': contribuyente,
            'tipo_vehiculo': tipo_vehiculo,
            'fecha_expedicion': fecha_expedicion,
            'fecha_vencimiento': fecha_vencimiento
        }).execute()

        return send_file(pdf_filename, as_attachment=True)

    return render_template('registro_guerrero.html')

if __name__ == '__main__':
    app.run(debug=True)
