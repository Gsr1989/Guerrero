from flask import Flask, render_template, request, redirect, url_for, session from datetime import datetime, timedelta import os import fitz  # PyMuPDF from supabase import create_client, Client

app = Flask(name) app.secret_key = 'clave_muy_segura'

SUPABASE_URL = os.getenv("SUPABASE_URL") SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/') def login(): return render_template('login.html')

@app.route('/iniciar_sesion', methods=['POST']) def iniciar_sesion(): usuario = request.form['usuario'] contrasena = request.form['contrasena']

if usuario == 'admin' and contrasena == 'admin123':
    session['usuario'] = usuario
    return redirect(url_for('panel_guerrero'))
else:
    return 'Usuario o contraseña incorrectos'

@app.route('/cerrar_sesion') def cerrar_sesion(): session.pop('usuario', None) return redirect(url_for('login'))

@app.route('/panel_guerrero') def panel_guerrero(): if 'usuario' not in session: return redirect(url_for('login'))

permisos = supabase.table('permisos_guerrero').select('*').execute()
return render_template('panel_guerrero.html', permisos=permisos.data)

@app.route('/registrar_guerrero', methods=['POST']) def registrar_guerrero(): if 'usuario' not in session: return redirect(url_for('login'))

try:
    marca = request.form['marca']
    linea = request.form['linea']
    anio = request.form['anio']
    color = request.form['color']
    serie = request.form['serie']
    motor = request.form['motor']
    contribuyente = request.form['contribuyente']
    tipo_vehiculo = request.form['tipo_vehiculo']

    fecha_expedicion = datetime.now().strftime('%Y-%m-%d')
    fecha_vencimiento = (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d')

    permisos = supabase.table('permisos_guerrero').select('folio').execute()
    if permisos.data:
        ultimo_folio = max([int(p['folio']) for p in permisos.data])
        nuevo_folio = str(ultimo_folio + 1)
    else:
        nuevo_folio = "1000"

    data = {
        "marca": marca,
        "linea": linea,
        "anio": anio,
        "color": color,
        "serie": serie,
        "motor": motor,
        "contribuyente": contribuyente,
        "tipo_vehiculo": tipo_vehiculo,
        "fecha_expedicion": fecha_expedicion,
        "fecha_vencimiento": fecha_vencimiento,
        "folio": nuevo_folio
    }
    resultado = supabase.table('permisos_guerrero').insert(data).execute()

    if resultado.status_code != 201:
        print(f"Error al registrar permiso en base de datos: {resultado.data}")
        return "Error al registrar en la base de datos", 500

    plantilla = fitz.open('static/pdf/guerrero.pdf')
    pagina = plantilla[0]

    pagina.insert_text((100, 100), f"Folio: {nuevo_folio}", fontsize=12, color=(1, 0, 0))
    pagina.insert_text((100, 120), f"Marca: {marca}", fontsize=11)
    pagina.insert_text((100, 140), f"Línea: {linea}", fontsize=11)
    pagina.insert_text((100, 160), f"Año: {anio}", fontsize=11)
    pagina.insert_text((100, 180), f"Color: {color}", fontsize=11)
    pagina.insert_text((100, 200), f"Serie: {serie}", fontsize=11)
    pagina.insert_text((100, 220), f"Motor: {motor}", fontsize=11)
    pagina.insert_text((100, 240), f"Contribuyente: {contribuyente}", fontsize=11)
    pagina.insert_text((100, 260), f"Tipo: {tipo_vehiculo}", fontsize=11)
    pagina.insert_text((100, 280), f"Expedición: {fecha_expedicion}", fontsize=11)
    pagina.insert_text((100, 300), f"Vencimiento: {fecha_vencimiento}", fontsize=11)

    output_dir = 'static/pdfs'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'permiso_guerrero_{nuevo_folio}.pdf')
    plantilla.save(output_path)
    plantilla.close()

    return redirect(url_for('panel_guerrero'))

except Exception as e:
    print(f"Error en registrar_guerrero: {e}")
    return "Error interno en el servidor", 500

if name == 'main': app.run(debug=True)

