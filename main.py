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
            f.write('AA0000')
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

def guardar_en_txt(folio, tipo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    with open(REGISTRO_FILE, 'a') as f:
        f.write(f"{folio}|{tipo}|{marca}|{linea}|{año}|{serie}|{motor}|{color}|{contribuyente}|{fecha_expedicion}|{fecha_vencimiento}\n")

def generar_pdf(folio, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    tipo_texto = obtener_texto_caracteristicas(tipo_vehiculo)
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    # Coordenadas centradas para tamaño carta (aproximadas)
    page.insert_text((250, 150), f"FOLIO: {folio}", fontsize=24, color=(1, 0, 0))
    page.insert_text((180, 200), f"TLAPA DE COMONFORT, GRO. A {fecha_expedicion}", fontsize=16)
    page.insert_text((180, 230), f"VIGENCIA: {fecha_expedicion} AL {fecha_vencimiento}", fontsize=16)

    page.insert_text((180, 280), f"CARACTERÍSTICAS {tipo_texto}:", fontsize=20)

    page.insert_text((180, 320), f"NÚMERO DE SERIE: {serie}", fontsize=14)
    page.insert_text((180, 345), f"NÚMERO DE MOTOR: {motor}", fontsize=14)
    page.insert_text((180, 370), f"MARCA: {marca}", fontsize=14)
    page.insert_text((180, 395), f"MODELO: {linea}", fontsize=14)
    page.insert_text((180, 420), f"AÑO: {año}", fontsize=14)
    page.insert_text((180, 445), f"COLOR: {color}", fontsize=14)
    page.insert_text((180, 470), f"CONTRIBUYENTE: {contribuyente}", fontsize=14)

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
            return redirect(url_for('formulario'))
        else:
            flash('Credenciales incorrectas', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/formulario', methods=['GET', 'POST'])
def formulario():
    if 'usuario' not in session:
        return redirect(url_for('login'))

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

        guardar_en_txt(folio_generado, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)
        generar_pdf(folio_generado, tipo_vehiculo, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)

        return render_template('exito.html', folio=folio_generado)

    return render_template('formulario.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(path, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
