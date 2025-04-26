from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://axgqvhgtbzkraytzaomw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImF4Z3F2aGd0YnprYXl0emFvbXciLCJyb2xlIjoiYW5vbiIsImlhdCI6MTc0NTU0MDA3NSwiZXhwIjoyMDYxMTYwNzV9.fWWMBg84zjeaCDAg-DV1SOJwVjbWDzKVsIMUTuVUVsY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        if usuario == 'admin' and contrasena == 'admin123':
            session['usuario'] = usuario
            return redirect(url_for('panel'))
        else:
            return render_template('login.html', error='Credenciales incorrectas')
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario' in session:
        return render_template('panel.html')
    else:
        return redirect(url_for('login'))

@app.route('/registrar_permiso', methods=['GET', 'POST'])
def registrar_permiso():
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
        
        # Generar un folio automático (ejemplo sencillo)
        folio = f"DB{datetime.now().strftime('%d%H%M')}"

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
        
        return redirect(url_for('ver_permiso', folio=folio))
    
    return render_template('registro.html')

@app.route('/verificar/<folio>')
def ver_permiso(folio):
    data = supabase.table('permisos').select('*').eq('folio', folio).execute()
    if data.data:
        permiso = data.data[0]
        return render_template('permiso.html', permiso=permiso)
    else:
        return "Permiso no encontrado"

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
