from flask import Flask, render_template, request, redirect, url_for, session, send_file from supabase import create_client, Client from datetime import datetime, timedelta import fitz  # PyMuPDF import os

app = Flask(name) app.secret_key = 'clave_super_segura'

Configura tu conexión Supabase

SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co" SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs" supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

Rutas principales

@app.route('/') def login(): return render_template('login.html')

@app.route('/panel_guerrero') def panel_guerrero(): busqueda = request.args.get('busqueda', '') if busqueda: permisos = supabase.table('permisos_guerrero').select('').ilike('serie', f'%{busqueda}%').execute().data else: permisos = supabase.table('permisos_guerrero').select('').execute().data

for permiso in permisos:
    fecha_vencimiento = datetime.strptime(permiso['fecha_vencimiento'], '%d/%m/%Y')
    permiso['estatus'] = 'VIGENTE' if fecha_vencimiento >= datetime.now() else 'VENCIDO'

return render_template('panel_guerrero.html', permisos=permisos)

@app.route('/registrar_guerrero', methods=['GET', 'POST']) def registrar_guerrero(): if request.method == 'POST': datos = { 'folio': generar_folio(), 'fecha_expedicion': datetime.now().strftime('%d/%m/%Y'), 'fecha_vencimiento': (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y'), 'marca': request.form['marca'].upper(), 'linea': request.form['linea'].upper(), 'anio': request.form['anio'], 'color': request.form['color'].upper(), 'serie': request.form['serie'].upper(), 'motor': request.form['motor'].upper(), 'contribuyente': request.form['contribuyente'].upper(), 'tipo_vehiculo': request.form['tipo_vehiculo'].upper() } supabase.table('permisos_guerrero').insert(datos).execute() return redirect(url_for('panel_guerrero')) return render_template('registro_guerrero.html')

@app.route('/editar_guerrero/<folio>', methods=['GET', 'POST']) def editar_guerrero(folio): permiso = buscar_permiso(folio) if request.method == 'POST': actualizar = { 'marca': request.form['marca'].upper(), 'linea': request.form['linea'].upper(), 'anio': request.form['anio'], 'color': request.form['color'].upper(), 'serie': request.form['serie'].upper(), 'motor': request.form['motor'].upper(), 'contribuyente': request.form['contribuyente'].upper(), 'tipo_vehiculo': request.form['tipo_vehiculo'].upper() } supabase.table('permisos_guerrero').update(actualizar).eq('folio', folio).execute() return redirect(url_for('panel_guerrero')) return render_template('editar_guerrero.html', permiso=permiso)

@app.route('/eliminar_guerrero/<folio>', methods=['POST']) def eliminar_guerrero(folio): supabase.table('permisos_guerrero').delete().eq('folio', folio).execute() return redirect(url_for('panel_guerrero'))

@app.route('/generar_pdf_guerrero/<folio>') def generar_pdf_guerrero(folio): permiso = buscar_permiso(folio) # Aquí iría tu lógica para generar el PDF basado en el permiso return f"Generar PDF para {folio} (aquí iría la lógica)"

@app.route('/verificar_folio/<folio>') def verificar_folio(folio): permiso = buscar_permiso(folio) if permiso: return render_template('resultado_verificador.html', permiso=permiso) else: return "Permiso no encontrado", 404

@app.route('/cerrar_sesion') def cerrar_sesion(): session.clear() return redirect(url_for('login'))

Funciones auxiliares

def buscar_permiso(folio): result = supabase.table('permisos_guerrero').select('*').eq('folio', folio).execute() if result.data: return result.data[0] else: return None

def generar_folio(): ahora = datetime.now() return ahora.strftime('%d%m%Y%H%M%S')

if name == "main": app.run(debug=True)

