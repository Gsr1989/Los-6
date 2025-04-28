from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from datetime import datetime, timedelta
from supabase import create_client, Client
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = "secreto_perro"

# Conexión a Supabase
SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30.bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF = 'Guerrero.pdf'
FOLIO_FILE = 'folio_actual.txt'

def cargar_folio():
    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, 'w') as f:
            f.write('AC0000')
    with open(FOLIO_FILE, 'r') as f:
        return f.read().strip()

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    numeros = int(folio_actual[2:])
    if numeros < 9999:
        numeros += 1
    else:
        letras = incrementar_letras(letras)
        numeros = 1
    nuevo_folio = f"{letras}{numeros:04d}"
    with open(FOLIO_FILE, 'w') as f:
        f.write(nuevo_folio)
    return nuevo_folio

def incrementar_letras(letras):
    letra1, letra2 = letras
    if letra2 != 'Z':
        letra2 = chr(ord(letra2) + 1)
    else:
        letra2 = 'A'
        if letra1 != 'Z':
            letra1 = chr(ord(letra1) + 1)
        else:
            letra1 = 'A'
    return letra1 + letra2

def formatear_fecha(fecha):
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL",
        "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO",
        "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
    dia = fecha.day
    mes = meses[fecha.strftime('%B')]
    año = fecha.year
    return f"{dia} DE {mes} DE {año}"

def obtener_texto_caracteristicas(tipo):
    tipo = tipo.upper()
    if tipo == "AUTOMOVIL":
        return "DEL AUTOMÓVIL"
    elif tipo == "MOTOCICLETA":
        return "DE LA MOTOCICLETA"
    elif tipo == "CAMIONETA":
        return "DE LA CAMIONETA"
    elif tipo == "OFICINA MOVIL":
        return "DE LA OFICINA MÓVIL"
    elif tipo == "REMOLQUE":
        return "DEL REMOLQUE"
    else:
        return tipo

def guardar_en_supabase(folio, tipo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    data = {
        "folio_generado": folio,
        "tipo_vehiculo": tipo,
        "marca": marca,
        "linea": linea,
        "anio": año,
        "serie": serie,
        "motor": motor,
        "color": color,
        "contribuyente": contribuyente,
        "fecha_expedicion": fecha_expedicion,
        "fecha_vencimiento": fecha_vencimiento
    }
    supabase.table("permisos_guerrero").insert(data).execute()

def generar_pdf(folio, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    tipo_texto = obtener_texto_caracteristicas(tipo_vehiculo)
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    page.insert_text((1700, 500), f"{folio}", fontsize=55, color=(1, 0, 0))
    page.insert_text((1325, 555), f"TLAPA DE COMONFORT, GRO. A {fecha_expedicion}", fontsize=38)
    page.insert_text((400, 1240), f"{fecha_expedicion} AL {fecha_vencimiento}", fontsize=60)
    page.insert_text((255, 1550), f"CARACTERÍSTICAS {tipo_texto}:", fontsize=75)
    page.insert_text((400, 1700), f"NÚMERO DE SERIE: {serie}", fontsize=35)
    page.insert_text((375, 1745), f"NÚMERO DE MOTOR: {motor}", fontsize=35)
    page.insert_text((602, 1790), f"MARCA: {marca}", fontsize=35)
    page.insert_text((575, 1835), f"MODELO: {linea}", fontsize=35)
    page.insert_text((652, 1880), f"AÑO: {año}", fontsize=35)
    page.insert_text((602, 1925), f"COLOR: {color}", fontsize=35)
    page.insert_text((426, 1970), f"CONTRIBUYENTE: {contribuyente}", fontsize=35)

    if not os.path.exists(PDF_OUTPUT_FOLDER):
        os.makedirs(PDF_OUTPUT_FOLDER)
    output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(output_path)
    doc.close()

@app.route('/', methods=['GET', 'POST'])
def formulario():
    if request.method == 'POST':
        tipo_vehiculo = request.form['tipo_vehiculo'].upper()
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        año = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()

        folio_actual = cargar_folio()
        folio_generado = siguiente_folio(folio_actual)

        fecha_actual = datetime.now()
        fecha_expedicion = formatear_fecha(fecha_actual)
        fecha_vencimiento = formatear_fecha(fecha_actual + timedelta(days=30))

        guardar_en_supabase(folio_generado, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)
        generar_pdf(folio_generado, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)

        return render_template('exito.html', folio=folio_generado)

    return render_template('formulario.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(path, as_attachment=True)

@app.route('/panel', methods=['GET'])
def panel():
    buscar = request.args.get('buscar', '')
    registros = supabase.table('permisos_guerrero').select('*').execute().data

    if buscar:
        registros = [r for r in registros if buscar.lower() in r['serie'].lower()]

    return render_template('panel.html', registros=registros)

@app.route('/editar/<folio>', methods=['GET', 'POST'])
def editar(folio):
    if request.method == 'POST':
        tipo_vehiculo = request.form['tipo_vehiculo'].upper()
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        año = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()

        supabase.table('permisos_guerrero').update({
            "tipo_vehiculo": tipo_vehiculo,
            "marca": marca,
            "linea": linea,
            "anio": año,
            "serie": serie,
            "motor": motor,
            "color": color,
            "contribuyente": contribuyente
        }).eq('folio_generado', folio).execute()

        flash('Registro actualizado exitosamente.', 'success')
        return redirect(url_for('panel'))

    registro = supabase.table('permisos_guerrero').select('*').eq('folio_generado', folio).single().execute().data
    return render_template('editar.html', registro=registro)

@app.route('/eliminar/<folio>')
def eliminar(folio):
    supabase.table('permisos_guerrero').delete().eq('folio_generado', folio).execute()
    flash('Registro eliminado exitosamente.', 'success')
    return redirect(url_for('panel'))

@app.route('/regenerar_pdf/<folio>')
def regenerar_pdf(folio):
    registro = supabase.table('permisos_guerrero').select('*').eq('folio_generado', folio).single().execute().data

    if not registro:
        flash('Folio no encontrado.', 'danger')
        return redirect(url_for('panel'))

    fecha_actual = datetime.now()
    fecha_vencimiento = formatear_fecha(fecha_actual + timedelta(days=30))

    generar_pdf(
        folio=registro['folio_generado'],
        tipo_vehiculo=registro['tipo_vehiculo'],
        marca=registro['marca'],
        linea=registro['linea'],
        año=registro['anio'],
        serie=registro['serie'],
        motor=registro['motor'],
        color=registro['color'],
        contribuyente=registro['contribuyente'],
        fecha_expedicion=registro['fecha_expedicion'],
        fecha_vencimiento=fecha_vencimiento
    )

    flash('PDF reimpreso exitosamente.', 'success')
    return redirect(url_for('panel'))

if __name__ == '__main__':
    app.run(debug=True)
