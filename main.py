from flask import Flask, render_template, request, redirect, url_for, send_file, session
from supabase import create_client
from datetime import datetime, timedelta
import os
import fitz
import qrcode

# --- Configuración inicial ---
app = Flask(__name__)
app.secret_key = 'clave_super_segura_2025'

SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

OUTPUT_DIR = "static/pdfs"
QR_DIR = "static/qr"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

# --- Utilidades ---

def generar_folio():
    archivo = "folios_globales.txt"
    if not os.path.exists(archivo):
        with open(archivo, "w") as f:
            f.write("BC0001\n")
        return "BC0001"
    
    with open(archivo, "r") as f:
        folios = [line.strip() for line in f]
    
    ultimo = folios[-1]
    letras, numeros = ultimo[:2], int(ultimo[2:])
    if numeros < 9999:
        nuevo = f"{letras}{numeros+1:04d}"
    else:
        l1, l2 = letras
        if l2 != "Z":
            l2 = chr(ord(l2) + 1)
        else:
            l2 = "A"
            l1 = chr(ord(l1) + 1) if l1 != "Z" else "A"
        nuevo = f"{l1}{l2}0001"
    
    with open(archivo, "a") as f:
        f.write(nuevo + "\n")
    return nuevo

def generar_qr(folio):
    data = f"https://validacion-guerrero.render.com/validar/{folio}"
    img = qrcode.make(data)
    path = os.path.join(QR_DIR, f"{folio}.png")
    img.save(path)
    return path

def generar_pdf(permiso):
    plantilla = fitz.open("static/pdf/Guerrero.pdf")
    page = plantilla[0]
    
    page.insert_text((100, 100), f"Folio: {permiso['folio']}", fontsize=12)
    page.insert_text((100, 120), f"Marca: {permiso['marca']}", fontsize=12)
    page.insert_text((100, 140), f"Línea: {permiso['linea']}", fontsize=12)
    page.insert_text((100, 160), f"Año: {permiso['anio']}", fontsize=12)
    page.insert_text((100, 180), f"Serie: {permiso['serie']}", fontsize=12)
    page.insert_text((100, 200), f"Motor: {permiso['motor']}", fontsize=12)
    page.insert_text((100, 220), f"Color: {permiso['color']}", fontsize=12)
    page.insert_text((100, 240), f"Contribuyente: {permiso['nombre']}", fontsize=12)
    page.insert_text((100, 260), f"Expedición: {permiso['fecha_expedicion']}", fontsize=12)
    page.insert_text((100, 280), f"Vencimiento: {permiso['fecha_vencimiento']}", fontsize=12)

    qr_path = generar_qr(permiso['folio'])
    rect = fitz.Rect(400, 100, 550, 250)
    page.insert_image(rect, filename=qr_path)

    pdf_path = os.path.join(OUTPUT_DIR, f"{permiso['folio']}.pdf")
    plantilla.save(pdf_path)
    plantilla.close()
    return pdf_path

# --- Rutas ---

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        contrasena = request.form["contrasena"]
        if usuario == "admin" and contrasena == "admin123":
            session["usuario"] = usuario
            return redirect(url_for("panel"))
    return render_template("login.html")

@app.route("/panel")
def panel():
    if "usuario" not in session:
        return redirect(url_for("login"))
    permisos = supabase.table("permisos_guerrero").select("*").execute().data
    return render_template("panel.html", permisos=permisos)

@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if "usuario" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        folio = generar_folio()
        marca = request.form["marca"].upper()
        linea = request.form["linea"].upper()
        anio = request.form["anio"]
        serie = request.form["serie"].upper()
        motor = request.form["motor"].upper()
        color = request.form["color"].upper()
        nombre = request.form["nombre"].upper()
        fecha_expedicion = datetime.now().strftime("%Y-%m-%d")
        fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        permiso = {
            "folio": folio,
            "marca": marca,
            "linea": linea,
            "anio": anio,
            "serie": serie,
            "motor": motor,
            "color": color,
            "nombre": nombre,
            "fecha_expedicion": fecha_expedicion,
            "fecha_vencimiento": fecha_vencimiento
        }
        supabase.table("permisos_guerrero").insert(permiso).execute()
        generar_pdf(permiso)
        return redirect(url_for("panel"))
    return render_template("formulario.html")

@app.route("/editar/<folio>", methods=["GET", "POST"])
def editar(folio):
    if "usuario" not in session:
        return redirect(url_for("login"))
    data = supabase.table("permisos_guerrero").select("*").eq("folio", folio).execute()
    if not data.data:
        return "Permiso no encontrado", 404
    permiso = data.data[0]
    if request.method == "POST":
        fields = ["marca", "linea", "anio", "serie", "motor", "color", "nombre", "fecha_expedicion", "fecha_vencimiento"]
        updates = {field: request.form[field].upper() for field in fields}
        supabase.table("permisos_guerrero").update(updates).eq("folio", folio).execute()
        permiso.update(updates)
        generar_pdf(permiso)
        return redirect(url_for("panel"))
    return render_template("editar_permiso.html", permiso=permiso)

@app.route("/eliminar/<folio>")
def eliminar(folio):
    if "usuario" not in session:
        return redirect(url_for("login"))
    supabase.table("permisos_guerrero").delete().eq("folio", folio).execute()
    pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    return redirect(url_for("panel"))

@app.route("/descargar/<folio>")
def descargar(folio):
    if "usuario" not in session:
        return redirect(url_for("login"))
    pdf_path = os.path.join(OUTPUT_DIR, f"{folio}.pdf")
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "Archivo no encontrado", 404

@app.route("/validar/<folio>")
def validar(folio):
    data = supabase.table("permisos_guerrero").select("*").eq("folio", folio).execute()
    if not data.data:
        return "Permiso no encontrado", 404
    permiso = data.data[0]
    return render_template("validar.html", permiso=permiso)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run()
