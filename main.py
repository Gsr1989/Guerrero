from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

# Configuración de Supabase
SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Rutas
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/inicio', methods=['POST'])
def inicio():
    usuario = request.form['usuario']
    contrasena = request.form['contrasena']
    if usuario == 'admin' and contrasena == 'admin123':
        session['usuario'] = usuario
        return redirect(url_for('panel'))
    else:
        return render_template('login.html', error='Credenciales incorrectas')

@app.route('/panel')
def panel():
    if 'usuario' in session:
        return render_template('panel_guerrero.html')
    else:
        return redirect(url_for('login'))

@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca']
        linea = request.form['linea']
        modelo = request.form['modelo']
        color = request.form['color']
        serie = request.form['serie']
        motor = request.form['motor']
        contribuyente = request.form['contribuyente']
        tipo_vehiculo = request.form['tipo_vehiculo']

        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        folio = f"GRO{datetime.now().strftime('%d%H%M%S')}"

        supabase.table('permisos_guerrero').insert({
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "modelo": modelo,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "tipo_vehiculo": tipo_vehiculo,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }).execute()

        return redirect(url_for('verificador', folio=folio))

    return render_template('formulario_guerrero.html')

@app.route('/verificador/<folio>')
def verificador(folio):
    data = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute()
    if data.data:
        permiso = data.data[0]
        return render_template('verificador_guerrero.html', permiso=permiso)
    else:
        return "Permiso no encontrado."

@app.route('/editar/<folio>', methods=['GET', 'POST'])
def editar(folio):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Actualizar
        marca = request.form['marca']
        linea = request.form['linea']
        modelo = request.form['modelo']
        color = request.form['color']
        serie = request.form['serie']
        motor = request.form['motor']
        contribuyente = request.form['contribuyente']
        tipo_vehiculo = request.form['tipo_vehiculo']

        supabase.table('permisos_guerrero').update({
            "marca": marca,
            "linea": linea,
            "modelo": modelo,
            "color": color,
            "serie": serie,
            "motor": motor,
            "contribuyente": contribuyente,
            "tipo_vehiculo": tipo_vehiculo
        }).eq('folio', folio).execute()

        return redirect(url_for('panel'))

    data = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute()
    if data.data:
        permiso = data.data[0]
        return render_template('editar_guerrero.html', permiso=permiso)
    else:
        return "Permiso no encontrado."

@app.route('/cerrar')
def cerrar():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
