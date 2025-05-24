from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "secreto_perro"

# ————— Supabase 👇 —————
SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
SUPABASE_KEY = "TU_SUPABASE_ANON_KEY"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ————— Rutas y archivos 👇 —————
PDF_OUTPUT_FOLDER = "static/pdfs"
PLANTILLA_PDF = "Guerrero.pdf"
FOLIO_FILE = "data/folio_actual.txt"
REGISTRO_FILE = "data/registros.txt"

# ————— Credenciales 👇 —————
USUARIO_VALIDO = "elwarrior"
CONTRASENA_VALIDA = "Warrior2025"

def cargar_folio():
    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, "w") as f:
            f.write("AA0001")
    with open(FOLIO_FILE) as f:
        return f.read().strip()

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    try:
        nums = int(folio_actual[2:])
    except ValueError:
        nums = 0
    if nums < 9999:
        nums += 1
    else:
        letras = incrementar_letras(letras)
        nums = 1
    nuevo = f"{letras}{nums:04d}"
    with open(FOLIO_FILE, "w") as f:
        f.write(nuevo)
    return nuevo

def incrementar_letras(letras):
    a, b = letras
    if b != "Z":
        b = chr(ord(b) + 1)
    else:
        b = "A"
        a = chr(ord(a) + 1) if a != "Z" else "A"
    return a + b

def guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, exp, ven):
    supabase.table("borradores_registros").insert({
        "fol_texto": folio,
        "marca_texto": marca,
        "linea_texto": linea,
        "anio_texto": anio,
        "serie_texto": serie,
        "numero_motor": motor,
        "color_texto": color,
        "contribuyente_texto": contribuyente,
        "fecha_expedicion": exp.isoformat(),
        "fecha_vencimiento": ven.isoformat()
    }).execute()

def guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, exp_str, ven_str):
    with open(REGISTRO_FILE, "a", encoding="utf-8") as f:
        f.write(f"{folio}|{marca}|{linea}|{anio}|{serie}|{motor}|{color}|{contribuyente}|{exp_str}|{ven_str}\n")

def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, exp, ven):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]
    # — Inserta texto donde lo necesites 👇
    page.insert_text((376, 769), folio, fontsize=8, color=(1, 0, 0))
    page.insert_text((122, 755), exp.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((122, 768), ven.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((376, 742), serie, fontsize=8)
    page.insert_text((376, 729), motor, fontsize=8)
    page.insert_text((376, 700), marca, fontsize=8)
    page.insert_text((376, 714), linea, fontsize=8)
    page.insert_text((376, 756), color, fontsize=8)
    page.insert_text((122, 700), contribuyente, fontsize=8)
    # — Guardo PDF 👇
    os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)
    salida = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(salida)
    doc.close()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["usuario"]
        p = request.form["contraseña"]
        if u == USUARIO_VALIDO and p == CONTRASENA_VALIDA:
            session["usuario"] = u
            return redirect(url_for("panel"))
        else:
            flash("Credenciales incorrectas", "danger")
    return render_template("login.html")

@app.route("/panel")
def panel():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("panel.html")

@app.route("/formulario", methods=["GET", "POST"])
def formulario():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        # — Leer campos del formulario 👇
        marca        = request.form["marca"].upper()
        linea        = request.form["linea"].upper()
        anio         = request.form["anio"].upper()
        serie        = request.form["serie"].upper()
        motor        = request.form["motor"].upper()
        color        = request.form["color"].upper()
        contrib     = request.form["contribuyente"].upper()
        dias_validez = int(request.form["validez"])

        # — Generar folio y fechas 👇
        folio = siguiente_folio(cargar_folio())
        hoy   = datetime.now()
        ven   = hoy + timedelta(days=dias_validez)

        # — Guardar en Supabase y .txt 👇
        guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contrib, hoy, ven)
        guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contrib,
                       hoy.strftime("%d/%m/%Y"), ven.strftime("%d/%m/%Y"))

        # — Generar PDF 👇
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contrib, hoy, ven)

        return render_template("exito.html", folio=folio)

    return render_template("formulario.html")

@app.route("/listar")
def listar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    if not os.path.exists(REGISTRO_FILE):
        open(REGISTRO_FILE, "a").close()

    regs = []
    with open(REGISTRO_FILE, "r", encoding="utf-8") as f:
        for linea in f:
            datos = linea.strip().split("|")
            if len(datos) == 10:
                regs.append({
                    "folio": datos[0],
                    "marca": datos[1],
                    "linea": datos[2],
                    "anio": datos[3],
                    "serie": datos[4],
                    "motor": datos[5],
                    "color": datos[6],
                    "contribuyente": datos[7],
                    "fecha_exp": datos[8],
                    "fecha_venc": datos[9],
                })

    return render_template("listar.html", registros=regs, ahora=datetime.now())

@app.route("/reimprimir", methods=["GET", "POST"])
def reimprimir():
    if "usuario" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        folio = request.form["folio"].strip().upper()
        path  = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        else:
            flash("Folio no encontrado o no tiene PDF generado.", "danger")
    return render_template("reimprimir.html")

@app.route("/descargar/<folio>")
def descargar(folio):
    path = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(path, as_attachment=True) if os.path.exists(path) else ("No existe", 404)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
