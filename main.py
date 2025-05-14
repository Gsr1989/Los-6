from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = "secreto_perro"

PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF = 'Guerrero.pdf'
FOLIO_FILE = 'folio_actual.txt'
REGISTRO_FILE = 'registros.txt'

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

def guardar_en_txt(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    with open(REGISTRO_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{folio}|{marca}|{linea}|{año}|{serie}|{motor}|{color}|{contribuyente}|{fecha_expedicion}|{fecha_vencimiento}\n")

def generar_pdf(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    # Datos parte superior
    page.insert_text((376, 769), folio, fontsize=8, color=(1, 0, 0))
    page.insert_text((122, 755), fecha_expedicion, fontsize=8)
    page.insert_text((122, 768), fecha_vencimiento, fontsize=8)
    page.insert_text((376, 742), serie, fontsize=8)
    page.insert_text((376, 729), motor, fontsize=8)
    page.insert_text((376, 700), marca, fontsize=8)
    page.insert_text((376, 714), linea, fontsize=8)
    page.insert_text((376, 756), color, fontsize=8)
    page.insert_text((122, 700), contribuyente, fontsize=8)

    # Parte rotada abajo
    page.insert_text((440, 200), folio, fontsize=83, rotate=270, color=(0, 0, 0))
    page.insert_text((77, 205), fecha_expedicion, fontsize=8, rotate=270)
    page.insert_text((63, 205), fecha_vencimiento, fontsize=8, rotate=270)
    page.insert_text((168, 110), serie, fontsize=18, rotate=270)
    page.insert_text((224, 110), motor, fontsize=18, rotate=270)
    page.insert_text((280, 110), marca, fontsize=18, rotate=270)
    page.insert_text((280, 340), linea, fontsize=18, rotate=270)
    page.insert_text((305, 530), año, fontsize=18, rotate=270)
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
        año = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()

        folio = siguiente_folio(cargar_folio())
        fecha_actual = datetime.now()
        fecha_exp = fecha_actual.strftime("%d/%m/%Y")
        fecha_ven = (fecha_actual + timedelta(days=30)).strftime("%d/%m/%Y")

        guardar_en_txt(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_exp, fecha_ven)
        generar_pdf(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_exp, fecha_ven)

        return render_template('exito.html', folio=folio)

    return render_template('formulario.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    return "El archivo no existe", 404

@app.route('/folio_actual')
def folio_actual():
    folio = cargar_folio()
    return render_template('folio_actual.html', mensaje=f"Folio actual: {folio}")

@app.route('/reimprimir', methods=['GET', 'POST'])
def reimprimir():
    if request.method == 'POST':
        folio = request.form['folio'].strip().upper()
        path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        else:
            flash("No se encontró el PDF con ese folio", "danger")
    return render_template('reimprimir.html')

@app.route('/listar')
def listar():
    if not os.path.exists(REGISTRO_FILE):
        return render_template('listar.html', registros=[], ahora=datetime.now())

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

@app.route('/renovar/<folio>')
def renovar(folio):
    if not os.path.exists(REGISTRO_FILE):
        flash("Archivo de registros no encontrado", "danger")
        return redirect(url_for('listar'))

    registros = []
    datos_antiguos = None

    with open(REGISTRO_FILE, 'r', encoding='utf-8') as f:
        for linea in f:
            partes = linea.strip().split('|')
            if len(partes) != 10:
                continue
            if partes[0] == folio:
                fecha_venc = datetime.strptime(partes[9], "%d/%m/%Y")
                if datetime.now() >= fecha_venc:
                    datos_antiguos = partes
            registros.append(linea)

    if not datos_antiguos:
        flash("No se puede renovar aún. El folio no ha vencido.", "warning")
        return redirect(url_for('listar'))

    nuevo_folio = siguiente_folio(cargar_folio())
    nueva_exp = datetime.now().strftime("%d/%m/%Y")
    nueva_ven = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

    _, marca, linea, año, serie, motor, color, contribuyente, _, _ = datos_antiguos

    guardar_en_txt(nuevo_folio, marca, linea, año, serie, motor, color, contribuyente, nueva_exp, nueva_ven)
    generar_pdf(nuevo_folio, marca, linea, año, serie, motor, color, contribuyente, nueva_exp, nueva_ven)

    flash(f"Permiso renovado. Nuevo folio: {nuevo_folio}", "success")
    return redirect(url_for('descargar', folio=nuevo_folio))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
