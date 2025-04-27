from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import os
import qrcode
import pytz
from supabase import create_client

app = Flask(__name__)

# Configura tu Supabase
SUPABASE_URL = 'TU_SUPABASE_URL'
SUPABASE_KEY = 'TU_SUPABASE_KEY'
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Página principal
@app.route('/')
def index():
    return render_template('login.html')

# Ruta para mostrar el panel
@app.route('/panel')
def panel():
    return render_template('panel.html')

# Ruta para registrar un nuevo permiso
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    if request.method == 'POST':
        # Recibir los datos del formulario
        marca = request.form.get('marca')
        linea = request.form.get('linea')
        año = request.form.get('anio')
        serie = request.form.get('serie')
        motor = request.form.get('motor')
        color = request.form.get('color')
        nombre = request.form.get('nombre')

        # Generar fechas
        ahora = datetime.now(pytz.timezone('America/Mexico_City'))
        fecha_expedicion = ahora.strftime('%d/%m/%Y')
        fecha_vencimiento = (ahora + timedelta(days=90)).strftime('%d/%m/%Y')  # Vigencia 90 días

        # Generar folio automático (este puede cambiar si quieres reglas especiales)
        registros = supabase.table('permisos').select('*').execute()
        conteo = len(registros.data) + 1
        folio = f"BC{conteo:04d}"

        # Guardar en Supabase
        datos = {
            'folio': folio,
            'marca': marca,
            'linea': linea,
            'anio': año,
            'serie': serie,
            'motor': motor,
            'color': color,
            'fecha_expedicion': fecha_expedicion,
            'fecha_vencimiento': fecha_vencimiento,
            'nombre': nombre
        }
        supabase.table('permisos').insert(datos).execute()

        # Generar QR
        qr_info = f"Folio: {folio}\nMarca: {marca}\nSerie: {serie}\nFecha Expedición: {fecha_expedicion}\nFecha Vencimiento: {fecha_vencimiento}"
        qr = qrcode.make(qr_info)
        qr_path = f"static/qrs/{folio}.png"
        os.makedirs(os.path.dirname(qr_path), exist_ok=True)
        qr.save(qr_path)

        return redirect(url_for('panel'))

    return render_template('registrar.html')

# Para que Render funcione
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
