from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os

app = Flask(__name__)

# Carpetas
PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF = 'Guerrero.pdf'
FOLIO_FILE = 'folio_actual.txt'

# Función para cargar o inicializar folio
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

def formatear_fecha_normal(fecha):
    meses = {
        "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
        "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
        "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
    }
    dia = fecha.day
    mes = meses[fecha.strftime('%B')]
    año = fecha.year
    return f"{dia} de {mes} del {año}"

def formatear_fecha_mayus(fecha):
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO", "April": "ABRIL",
        "May": "MAYO", "June": "JUNIO", "July": "JULIO", "August": "AGOSTO",
        "September": "SEPTIEMBRE", "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
    dia = fecha.day
    mes = meses[fecha.strftime('%B')]
    año = fecha.year
    return f"{dia} DE {mes} DE {año}"

# Ruta formulario
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
        fecha_expedicion = formatear_fecha_normal(fecha_actual)
        fecha_vencimiento = formatear_fecha_mayus(fecha_actual + timedelta(days=30))
        fecha_vigencia = f"{formatear_fecha_mayus(fecha_actual)} AL {fecha_vencimiento}"

        # Cargar plantilla
        doc = fitz.open(PLANTILLA_PDF)
        page = doc[0]

        # Insertar datos usando insert_textbox
        page.insert_textbox(fitz.Rect(125, 480, 500, 550), folio_generado, fontsize=14, fontname="helv", color=(1, 0, 0), render_mode=3, align=1)
        page.insert_textbox(fitz.Rect(320, 510, 1200, 580), f"TLAPA DE COMONFORT, GRO. A {fecha_expedicion.upper()}", fontsize=12, fontname="helv", color=(0, 0, 0), render_mode=3, align=0)
        page.insert_textbox(fitz.Rect(100, 620, 1200, 700), fecha_vigencia, fontsize=14, fontname="helv", color=(0, 0, 0), render_mode=3, align=1)

        caracteristicas_titulo = f"CARACTERÍSTICAS DEL {tipo_vehiculo}:"
        page.insert_textbox(fitz.Rect(100, 730, 1200, 780), caracteristicas_titulo, fontsize=12, fontname="helv", color=(0, 0, 0), render_mode=3, align=0)

        page.insert_textbox(fitz.Rect(100, 770, 1200, 800), f"NÚMERO DE SERIE: {serie}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 800, 1200, 830), f"NÚMERO DE MOTOR: {motor}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 830, 1200, 860), f"MARCA: {marca}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 860, 1200, 890), f"MODELO: {linea}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 890, 1200, 920), f"AÑO: {año}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 920, 1200, 950), f"COLOR: {color}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)
        page.insert_textbox(fitz.Rect(100, 950, 1200, 980), f"CONTRIBUYENTE: {contribuyente}", fontsize=10, fontname="helv", color=(0, 0, 0), render_mode=3)

        if not os.path.exists(PDF_OUTPUT_FOLDER):
            os.makedirs(PDF_OUTPUT_FOLDER)
        output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio_generado}.pdf")
        doc.save(output_path)
        doc.close()

        return render_template('exito.html', folio=folio_generado)

    return render_template('formulario.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
