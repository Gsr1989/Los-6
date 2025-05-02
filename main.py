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
            f.write('AB0000')
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

def guardar_en_txt(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    with open(REGISTRO_FILE, 'a') as f:
        f.write(f"{folio}|{marca}|{linea}|{año}|{serie}|{motor}|{color}|{contribuyente}|{fecha_expedicion}|{fecha_vencimiento}\n")

def generar_pdf(folio, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    # PARTE SUPERIOR
    page.insert_text((402, 122), folio, fontsize=14, color=(1, 0, 0))
    page.insert_text((270, 132), fecha_expedicion, fontsize=10)
    page.insert_text((360, 132), fecha_vencimiento, fontsize=10)
    page.insert_text((83, 393), serie, fontsize=8)
    page.insert_text((77, 405), motor, fontsize=8)
    page.insert_text((129, 417), marca, fontsize=8)
    page.insert_text((123, 429), linea, fontsize=8)
    page.insert_text((140, 441), año, fontsize=8)
    page.insert_text((129, 453), color, fontsize=8)
    page.insert_text((89, 465), contribuyente, fontsize=8)

    # PARTE INFERIOR ROTADA 90° A LA IZQUIERDA
    page.insert_text((500, 650), folio, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 670), fecha_expedicion, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 690), fecha_vencimiento, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 710), serie, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 730), motor, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 750), marca, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 770), linea, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 790), año, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 810), color, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((500, 830), contribuyente, fontsize=8, rotate=270, color=(0, 0, 0))

    if not os.path.exists(PDF_OUTPUT_FOLDER):
        os.makedirs(PDF_OUTPUT_FOLDER)

    output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    try:
        doc.save(output_path)
        print(f"PDF guardado exitosamente en: {output_path}")
    except Exception as e:
        print(f"ERROR al guardar PDF: {e}")
    finally:
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
        fecha_expedicion = fecha_actual.strftime("%d/%m/%Y")
        fecha_vencimiento = (fecha_actual + timedelta(days=30)).strftime("%d/%m/%Y")

        guardar_en_txt(folio_generado, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)
        generar_pdf(folio_generado, marca, linea, año, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)

        return render_template('exito.html', folio=folio_generado)

    return render_template('formulario.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    if not os.path.exists(path):
        return "El archivo no existe", 404
    return send_file(path, as_attachment=True)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
