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
    # traemos siempre el último folio guardado en Supabase
    resp = supabase.table("borradores_registros") \
        .select("fol_texto") \
        .order("id", desc=True) \
        .limit(1) \
        .execute()
    if resp.data and len(resp.data):
        return resp.data[0]["fol_texto"]
    # fallback si la tabla está vacía
    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, 'w') as f:
            f.write('AA0001')
    with open(FOLIO_FILE, 'r') as f:
        return f.read().strip()

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    try:
        numero = int(folio_actual[2:])
    except ValueError:
        numero = 0
    if numero < 9999:
        numero += 1
    else:
        letras = incrementar_letras(letras)
        numero = 1
    nuevo = f"{letras}{numero:04d}"
    # guardamos también en txt para consistencia local
    with open(FOLIO_FILE, 'w') as f:
        f.write(nuevo)
    return nuevo

def incrementar_letras(l):
    a, b = l
    if b != 'Z':
        b = chr(ord(b) + 1)
    else:
        b = 'A'
        a = chr(ord(a) + 1) if a != 'Z' else 'A'
    return a + b

def guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    supabase.table("borradores_registros").insert({
        "fol_texto": folio,
        "marca_texto": marca,
        "linea_texto": linea,
        "anio_texto": anio,
        "serie_texto": serie,
        "motor_texto": motor,
        "color_texto": color,
        "contribuyente_texto": contribuyente,
        "fecha_expedicion": fexp.isoformat(),
        "fecha_vencimiento": fven.isoformat()
    }).execute()

def guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    with open(REGISTRO_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{folio}|{marca}|{linea}|{anio}|{serie}|{motor}|{color}|{contribuyente}|{fexp}|{fven}\n")

def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]
    # insertamos en plantilla
    page.insert_text((376, 769), folio, fontsize=8, color=(1, 0, 0))
    page.insert_text((122, 755), fexp.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((122, 768), fven.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((376, 742), serie, fontsize=8)
    page.insert_text((376, 729), motor, fontsize=8)
    page.insert_text((376, 700), marca, fontsize=8)
    page.insert_text((376, 714), linea, fontsize=8)
    page.insert_text((376, 756), color, fontsize=8)
    page.insert_text((122, 700), contribuyente, fontsize=8)
    # marcas de agua giradas
    page.insert_text((440, 200), folio, fontsize=83, rotate=270, color=(0, 0, 0))
    page.insert_text((77, 205), fexp.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((63, 205), fven.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((168, 110), serie, fontsize=18, rotate=270)
    page.insert_text((224, 110), motor, fontsize=18, rotate=270)
    page.insert_text((280, 110), marca, fontsize=18, rotate=270)
    page.insert_text((280, 340), linea, fontsize=18, rotate=270)
    page.insert_text((305, 530), anio, fontsize=18, rotate=270)
    page.insert_text((224, 410), color, fontsize=18, rotate=270)
    page.insert_text((115, 205), contribuyente, fontsize=8, rotate=270)
    if not os.path.exists(PDF_OUTPUT_FOLDER):
        os.makedirs(PDF_OUTPUT_FOLDER)
    salida = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(salida)
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
        marca        = request.form['marca'].upper()
        linea        = request.form['linea'].upper()
        anio         = request.form['anio'].upper()
        serie        = request.form['serie'].upper()
        motor        = request.form['motor'].upper()
        color        = request.form['color'].upper()
        contribuyente= request.form['contribuyente'].upper()
        dias         = int(request.form.get('validez', 30))
        folio        = siguiente_folio(cargar_folio())
        ahora        = datetime.now()
        vencimiento  = ahora + timedelta(days=dias)
        guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, vencimiento)
        guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente,
                       ahora.strftime("%d/%m/%Y"), vencimiento.strftime("%d/%m/%Y"))
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, vencimiento)
        return render_template('exito.html', folio=folio)
    return render_template('formulario.html')

# ruta adicional para evitar BuildError en panel.html
@app.route('/consultar')
def consultar():
    # muestra la página de reimpresión
    return render_template('reimprimir.html')

@app.route('/reimprimir', methods=['GET', 'POST'])
def reimprimir():
    if request.method == 'POST':
        folio = request.form['folio'].strip().upper()
        path  = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
