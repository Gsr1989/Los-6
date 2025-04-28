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

# Función para actualizar folio
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

# Función para formatear fechas
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
        fecha_expedicion = formatear_fecha(fecha_actual)
        fecha_vencimiento = formatear_fecha(fecha_actual + timedelta(days=30))
        vigencia_texto = f"{fecha_expedicion} AL {fecha_vencimiento}"

        # Cargar plantilla
        doc = fitz.open(PLANTILLA_PDF)
        page = doc[0]

        # Insertar datos en coordenadas más centradas
        page.insert_text((250, 100), f"{folio_generado}", fontsize=14, color=(1, 0, 0))
        page.insert_text((150, 150), f"TLAPA DE COMONFORT, GRO. A {fecha_expedicion}", fontsize=12)
        page.insert_text((150, 190), vigencia_texto, fontsize=12)
        page.insert_text((150, 240), f"CARACTERÍSTICAS DEL {tipo_vehiculo}:", fontsize=13)

        page.insert_text((150, 280), f"NÚMERO DE SERIE: {serie}", fontsize=11)
        page.insert_text((150, 310), f"NÚMERO DE MOTOR: {motor}", fontsize=11)
        page.insert_text((150, 340), f"MARCA: {marca}", fontsize=11)
        page.insert_text((150, 370), f"MODELO: {linea}", fontsize=11)
        page.insert_text((150, 400), f"AÑO: {año}", fontsize=11)
        page.insert_text((150, 430), f"COLOR: {color}", fontsize=11)
        page.insert_text((150, 460), f"CONTRIBUYENTE: {contribuyente}", fontsize=11)

        # Guardar el nuevo PDF
        if not os.path.exists(PDF_OUTPUT_FOLDER):
            os.makedirs(PDF_OUTPUT_FOLDER)
        output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio_generado}.pdf")
        doc.save(output_path)
        doc.close()

        return render_template('exito.html', folio=folio_generado)

    return render_template('formulario.html')

# Ruta para descargar PDF
@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
