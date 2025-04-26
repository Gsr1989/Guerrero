from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from datetime import datetime, timedelta
from supabase import create_client, Client
import os, io, fitz, qrcode
from PIL import Image

app = Flask(__name__)
app.secret_key = 'clave_muy_segura_123456'

# Conexión REAL a tu Supabase
SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario'].upper()
        contrasena = request.form['contrasena'].upper()
        if usuario == 'ADMIN' and contrasena == 'NIVELGUERRERO2025':
            session['usuario'] = usuario
            return redirect('/panel_guerrero')
        else:
            flash("Credenciales incorrectas")
    return render_template('login.html')

@app.route('/cerrar_sesion')
def cerrar_sesion():
    session.clear()
    return redirect('/login')

# PANEL
@app.route('/panel_guerrero')
def panel_guerrero():
    if 'usuario' not in session:
        return redirect('/login')
    data = supabase.table("permisos_guerrero").select("*").execute().data
    hoy = datetime.now().date()
    for permiso in data:
        vencimiento = datetime.strptime(permiso['fecha_vencimiento'], "%Y-%m-%d").date()
        permiso['estatus'] = 'VIGENTE' if vencimiento >= hoy else 'VENCIDO'
    return render_template("panel_guerrero.html", permisos=data)

# REGISTRO
@app.route('/registrar_guerrero', methods=['GET', 'POST'])
def registrar_guerrero():
    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':
        datos = {k: v.upper() for k, v in request.form.items()}
        fecha_exp = datetime.now().date()
        fecha_ven = fecha_exp + timedelta(days=30)
        folio = generar_folio()

        supabase.table("permisos_guerrero").insert({
            "folio": folio,
            "fecha_expedicion": str(fecha_exp),
            "fecha_vencimiento": str(fecha_ven),
            **datos
        }).execute()

        return redirect(f'/verificar_folio/{folio}')

    return render_template('formulario_guerrero.html')

# VERIFICADOR PÚBLICO
@app.route('/verificar_folio/<folio>')
def verificar_folio(folio):
    data = supabase.table("permisos_guerrero").select("*").eq("folio", folio.upper()).execute().data
    if data:
        permiso = {k: v.upper() if isinstance(v, str) else v for k, v in data[0].items()}
        return render_template("verificador_guerrero.html", permiso=permiso)
    return "Folio no encontrado"

# EDITAR
@app.route('/editar_guerrero/<folio>', methods=['GET', 'POST'])
def editar_guerrero(folio):
    if 'usuario' not in session:
        return redirect('/login')
    if request.method == 'POST':
        nuevos_datos = {k: v.upper() for k, v in request.form.items()}
        supabase.table("permisos_guerrero").update(nuevos_datos).eq("folio", folio.upper()).execute()
        return redirect('/panel_guerrero')
    data = supabase.table("permisos_guerrero").select("*").eq("folio", folio.upper()).execute().data
    if not data:
        return "Folio no encontrado"
    permiso = {k: v.upper() if isinstance(v, str) else v for k, v in data[0].items()}
    return render_template("editar_guerrero.html", permiso=permiso)

# ELIMINAR
@app.route('/eliminar_guerrero/<folio>')
def eliminar_guerrero(folio):
    if 'usuario' not in session:
        return redirect('/login')
    supabase.table("permisos_guerrero").delete().eq("folio", folio.upper()).execute()
    return redirect('/panel_guerrero')

# DESCARGAR PLANTILLA SIN ACTIVAR
@app.route('/descargar_plantilla/<folio>')
def descargar_plantilla(folio):
    plantilla_path = "plantillas/Guerrero.pdf"
    output_path = f"{OUTPUT_DIR}/{folio.upper()}_plantilla.pdf"

    doc = fitz.open(plantilla_path)
    doc.save(output_path)
    return send_file(output_path, as_attachment=True)

# GENERAR RECIBO DE PAGO
@app.route('/generar_recibo/<folio>')
def generar_recibo(folio):
    data = supabase.table("permisos_guerrero").select("*").eq("folio", folio.upper()).execute().data
    if not data:
        return "Folio no encontrado"
    permiso = data[0]

    recibo_path = "plantillas/recibo_guerrero.pdf"
    output_path = f"{OUTPUT_DIR}/{folio.upper()}_recibo.pdf"

    doc = fitz.open(recibo_path)
    page = doc[0]
    page.insert_text((100, 100), f"FOLIO: {folio.upper()}", fontsize=12)
    page.insert_text((100, 120), f"NOMBRE: {permiso['contribuyente'].upper()}", fontsize=12)
    page.insert_text((100, 140), f"FECHA: {permiso['fecha_expedicion']}", fontsize=12)
    doc.save(output_path)
    return send_file(output_path, as_attachment=True)

# GENERAR QR DINÁMICO
def generar_qr(folio):
    folio = folio.upper()
    qr = qrcode.make(f"https://tusitio.com/verificar_folio/{folio}")
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    return buffer.getvalue()

# FOLIO ÚNICO
def generar_folio():
    import random
    letras = "DB"
    numeros = random.randint(1000, 9999)
    return f"{letras}{numeros}"

if __name__ == '__main__':
    app.run(debug=True)
