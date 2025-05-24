from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "secreto_perro"

SUPABASE_URL = "https://xsagwqepoljfsogusubw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzYWd3cWVwb2xqZnNvZ3VzdWJ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM5NjM3NTUsImV4cCI6MjA1OTUzOTc1NX0.NUixULn0m2o49At8j6X58UqbXre2O2_JStqzls_8Gws"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF = 'Guerrero.pdf'
FOLIO_FILE = 'data/folio_actual.txt'
REGISTRO_FILE = 'data/registros.txt'

USUARIO_VALIDO = "elwarrior"
CONTRASENA_VALIDA = "Warrior2025"

def cargar_folio():
    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, 'w') as f:
            f.write('AA0001')
    with open(FOLIO_FILE, 'r') as f:
        return f.read().strip()

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    try:
        numeros = int(folio_actual[2:])
    except ValueError:
        numeros = 0
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

def guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_exp, fecha_ven):
    supabase.table("borradores_registros").insert({
        "folio": folio,
        "marca": marca,
        "linea": linea,
        "anio": anio,
        "numero_serie": serie,
        "numero_motor": motor,
        "color": color,
        "contribuyente": contribuyente,
        "fecha_expedicion": fecha_exp.isoformat(),
        "fecha_vencimiento": fecha_ven.isoformat()
    }).execute()

def guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_exp, fecha_ven):
    with open(REGISTRO_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{folio}|{marca}|{linea}|{anio}|{serie}|{motor}|{color}|{contribuyente}|{fecha_exp}|{fecha_ven}\n")

def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_exp, fecha_ven):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    page.insert_text((376, 769), folio, fontsize=8, color=(1, 0, 0))
    page.insert_text((122, 755), fecha_exp.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((122, 768), fecha_ven.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((376, 742), serie, fontsize=8)
    page.insert_text((376, 729), motor, fontsize=8)
    page.insert_text((376, 700), marca, fontsize=8)
    page.insert_text((376, 714), linea, fontsize=8)
    page.insert_text((376, 756), color, fontsize=8)
    page.insert_text((122, 700), contribuyente, fontsize=8)

    page.insert_text((440, 200), folio, fontsize=83, rotate=270, color=(0, 0, 0))
    page.insert_text((77, 205), fecha_exp.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((63, 205), fecha_ven.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((168, 110), serie, fontsize=18, rotate=270)
    page.insert_text((224, 110), motor, fontsize=18, rotate=270)
    page.insert_text((280, 110), marca, fontsize=18, rotate=270)
    page.insert_text((280, 340), linea, fontsize=18, rotate=270)
    page.insert_text((305, 530), anio, fontsize=18, rotate=270)
    page.insert_text((224, 410), color, fontsize=18, rotate=270)
    page.insert_text((115, 205), contribuyente, fontsize=8, rotate=270)

    if not os.path.exists(PDF_OUTPUT_FOLDER):
        os.makedirs(PDF_OUTPUT_FOLDER)

    output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(output_path)
    doc.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contraseña = request.form['contraseña']
        if usuario == USUARIO_VALIDO and contraseña == CONTRASENA_VALIDA:
            session['usuario'] = usuario
            return redirect(url_for('panel'))
        else:
            flash('Credenciales incorrectas', 'danger')
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('panel.html')

@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca'].upper()
        linea = request.form['linea'].upper()
        anio = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()

        folio = siguiente_folio(cargar_folio())
        fecha_actual = datetime.now()
        fecha_ven = fecha_actual + timedelta(days=30)

        guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_actual, fecha_ven)
        guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_actual.strftime("%d/%m/%Y"), fecha_ven.strftime("%d/%m/%Y"))
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_actual, fecha_ven)

        return render_template('exito.html', folio=folio)

    return render_template('formulario.html')

@app.route('/consultar', methods=['GET', 'POST'])
def consultar():
    if request.method == 'POST':
        folio = request.form['folio'].strip().upper()
        path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        else:
            flash("Folio no encontrado o no tiene PDF generado.", "danger")
    return render_template('reimprimir.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "El archivo no existe", 404

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/listar')
def listar():
    if not os.path.exists(REGISTRO_FILE):
        open(REGISTRO_FILE, 'a').close()

    registros = []
    with open(REGISTRO_FILE, 'r', encoding='utf-8') as f:
        for linea in f:
            datos = linea.strip().split('|')
            if len(datos) == 10:
                registros.append({
                    "folio": datos[0],
                    "marca": datos[1],
                    "linea": datos[2],
                    "anio": datos[3],
                    "serie": datos[4],
                    "motor": datos[5],
                    "color": datos[6],
                    "contribuyente": datos[7],
                    "fecha_exp": datos[8],
                    "fecha_venc": datos[9]
                })

    return render_template('listar.html', registros=registros, ahora=datetime.now())

if __name__ == '__main__':
    app.run(debug=True)
