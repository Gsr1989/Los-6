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
            f.write('AA|0|2024-01')
    with open(FOLIO_FILE, 'r') as f:
        letras, numero, mes = f.read().strip().split('|')
        return letras, int(numero), mes

def guardar_folio(letras, numero, mes):
    with open(FOLIO_FILE, 'w') as f:
        f.write(f'{letras}|{numero}|{mes}')

def incrementar_letras(letras):
    l1, l2 = letras
    if l2 != 'Z':
        l2 = chr(ord(l2) + 1)
    else:
        l2 = 'A'
        if l1 != 'Z':
            l1 = chr(ord(l1) + 1)
        else:
            l1 = 'A'
    return l1 + l2

def siguiente_folio():
    letras, numero, mes_guardado = cargar_folio()
    mes_actual = datetime.now().strftime('%Y-%m')

    if mes_actual != mes_guardado:
        letras = incrementar_letras(letras)
        numero = 1
        mes_guardado = mes_actual
    else:
        numero += 1
        if numero > 999999:
            letras = incrementar_letras(letras)
            numero = 1

    guardar_folio(letras, numero, mes_guardado)
    return f"{letras}{numero:04d}"

def guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    with open(REGISTRO_FILE, 'a') as f:
        f.write(f"{folio}|{marca}|{linea}|{anio}|{serie}|{motor}|{color}|{contribuyente}|{fecha_expedicion}|{fecha_vencimiento}\n")

def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]

    page.insert_text((376, 769), folio, fontsize=8, color=(1, 0, 0))
    page.insert_text((122, 755), fecha_expedicion, fontsize=8)
    page.insert_text((122, 768), fecha_vencimiento, fontsize=8)
    page.insert_text((376, 742), serie, fontsize=8)
    page.insert_text((376, 729), motor, fontsize=8)
    page.insert_text((376, 700), marca, fontsize=8)
    page.insert_text((376, 714), linea, fontsize=8)
    page.insert_text((376, 756), color, fontsize=8)
    page.insert_text((122, 700), contribuyente, fontsize=8)

    page.insert_text((440, 200), folio, fontsize=83, rotate=270, color=(0, 0, 0))
    page.insert_text((77, 205), fecha_expedicion, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((63, 205), fecha_vencimiento, fontsize=8, rotate=270, color=(0, 0, 0))
    page.insert_text((168, 110), serie, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((224, 110), motor, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((280, 110), marca, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((280, 340), linea, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((280, 458), anio, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((224, 410), color, fontsize=19, rotate=270, color=(0, 0, 0))
    page.insert_text((115, 205), contribuyente, fontsize=8, rotate=270, color=(0, 0, 0))

    if not os.path.exists(PDF_OUTPUT_FOLDER):
        os.makedirs(PDF_OUTPUT_FOLDER)

    output_path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    try:
        doc.save(output_path)
    except Exception as e:
        print(f"ERROR al guardar PDF: {e}")
    finally:
        doc.close()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contraseña']
        if usuario == USUARIO_VALIDO and contrasena == CONTRASENA_VALIDA:
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
        anio = request.form['año'].upper()
        serie = request.form['serie'].upper()
        motor = request.form['motor'].upper()
        color = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()

        folio = siguiente_folio()

        fecha_actual = datetime.now()
        fecha_expedicion = fecha_actual.strftime("%d/%m/%Y")
        fecha_vencimiento = (fecha_actual + timedelta(days=30)).strftime("%d/%m/%Y")

        guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fecha_expedicion, fecha_vencimiento)

        return render_template('exito.html', folio=folio)

    return render_template('formulario.html')

@app.route('/folio_actual')
def folio_actual():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    letras, numero, mes = cargar_folio()
    folio = f"{letras}{numero:04d}"

    if letras == "ZZ":
        mensaje = "¡Folio reiniciado! Sobreviviste 56 años, cabrón. Misión cumplida."
    else:
        mensaje = f"Folio actual: {folio} (Mes: {mes})"

    return render_template("folio_actual.html", mensaje=mensaje)

@app.route('/reimprimir', methods=['GET', 'POST'])
def reimprimir():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        criterio = request.form['criterio'].upper()
        with open(REGISTRO_FILE, 'r') as f:
            for linea in f:
                datos = linea.strip().split('|')
                if criterio in datos:
                    folio = datos[0]
                    return redirect(url_for('descargar', folio=folio))
        flash('No se encontró el folio/serie/nombre.', 'warning')
    return render_template('reimprimir.html')

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
