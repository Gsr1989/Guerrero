# main.py

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime, timedelta
from supabase import create_client
from PyPDF2 import PdfWriter
import qrcode
from PIL import Image

# -----------------------------------------------------------------------------
# Supabase (INLINE para copiar/pegar)
# -----------------------------------------------------------------------------
SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwic"
    "m9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30."
    "bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
)

# -----------------------------------------------------------------------------
# Flask + Supabase client setup
# -----------------------------------------------------------------------------
app = Flask(__name__)
app.secret_key = "cualquier-cosa-para-flask"  # Cámbiala si quieres

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------------------------------------------------------------
# RUTAS
# -----------------------------------------------------------------------------
@app.route("/")
def inicio():
    if session.get("user"):
        return redirect(url_for("panel"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    user = request.form.get("user")
    pwd = request.form.get("pwd")
    # Aquí tu lógica de autenticación: por ahora, cualquier user/pwd funciona
    session["user"] = user
    return redirect(url_for("panel"))


@app.route("/panel")
def panel():
    permisos = supabase.table("permisos").select("*").execute().data
    return render_template("panel_guerrero.html", permisos=permisos)


@app.route("/registrar_guerrero", methods=["GET", "POST"])
def registrar_guerrero():
    if request.method == "GET":
        return render_template("formulario_guerrero.html")

    # POST: recoge datos del formulario y genera fechas
    datos = {
        "marca":           request.form["marca"],
        "linea":           request.form["linea"],
        "anio":            request.form["anio"],
        "color":           request.form["color"],
        "serie":           request.form["serie"],
        "motor":           request.form["motor"],
        "contribuyente":   request.form["contribuyente"],
        "tipo_vehiculo":   request.form["tipo_vehiculo"],
        "fecha_expedicion":  datetime.now().date().isoformat(),
        "fecha_vencimiento": (datetime.now() + timedelta(days=365)).date().isoformat()
    }

    supabase.table("permisos").insert(datos).execute()
    return redirect(url_for("panel"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))


# -----------------------------------------------------------------------------
# EJECUCIÓN
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # En local corre en el puerto 5000; en Render se ignora y toma el suyo.
    app.run(host="0.0.0.0", port=5000)
