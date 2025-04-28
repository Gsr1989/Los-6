Cambia lo que debas y me lo regresas debidamente armado solo para copiar y pegar

from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os

app = Flask(name)

Carpetas

PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF = 'Guerrero.pdf'
FOLIO_FILE = 'folio_actual.txt'

Función para cargar o inicializar folio

def cargar_folio():
if not os.path.exists(FOLIO_FILE):
with open(FOLIO_FILE, 'w') as f:
f.write('AC0000')
with open(FOLIO_FILE, 'r') as f:
return f.read().strip()

Función para actualizar folio

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

Ruta formulario

@app.route('/', methods=['GET', 'POST'])
def formulario():
if request.method == 'POST':
tipo_vehiculo = request.form['tipo_vehiculo']
marca = request.form['marca']
linea = request.form['linea']
año = request.form['año']
serie = request.form['serie']
motor = request.form['motor']
color = request.form['color']
contribuyente = request.form['contribuyente']

folio_actual = cargar_folio()
folio_generado = siguiente_folio(folio_actual)

fecha_expedicion = datetime.now().strftime('%d/%m/%Y')    
fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')    

# Cargar plantilla    
doc = fitz.open(PLANTILLA_PDF)    
page = doc[0]    

# Insertar datos en coordenadas (ajústalas si quieres)    
page.insert_text((1700, 500), f"Folio: {folio_generado}", fontsize=50, color=(1, 0, 0))    
page.insert_text((1600, 530), f"Fecha expedición: {fecha_expedicion}", fontsize=45)    
page.insert_text((900, 1600), f"Fecha vencimiento: {fecha_vencimiento}", fontsize=20)    
page.insert_text((300, 1230), f"Tipo: {tipo_vehiculo}", fontsize=80)    
page.insert_text((300, 1860), f"Marca: {marca}", fontsize=20)    
page.insert_text((300, 1890), f"Línea: {linea}", fontsize=20)    
page.insert_text((300, 1910), f"Año: {año}", fontsize=20)    
page.insert_text((300, 1940), f"Serie: {serie}", fontsize=20)    
page.insert_text((300, 1970), f"Motor: {motor}", fontsize=20)    
page.insert_text((300, 2000), f"Color: {color}", fontsize=20)    
page.insert_text((300, 2030), f"Contribuyente: {contribuyente}", fontsize=20)    

# Guardar el nuevo PDF    
if not os.path.exists(PDF_OUTPUT_FOLDER):    
    os.makedirs(PDF_OUTPUT_FOLDER)    
output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio_generado}.pdf")    
doc.save(output_path)    
doc.close()    

return render_template('exito.html', folio=folio_generado)

return render_template('formulario.html')

Ruta para descargar PDF

@app.route('/descargar/<folio>')
def descargar(folio):
path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
return send_file(path, as_attachment=True)

if name == 'main':
app.run(debug=True)

