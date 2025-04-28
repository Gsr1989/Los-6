# main.py

from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from datetime import datetime, timedelta
from supabase import create_client, Client
import fitz   # PyMuPDF
import os

app = Flask(__name__)
app.secret_key = "secreto_perro"

# ————————————————
# Conexión a Supabase (incluida)
SUPABASE_URL = "https://iuwsippnvyynwnxanwnv.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml1d3NpcHBudnl5bndueGFud252Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDU2NDU3MDcsImV4cCI6MjA2MTIyMTcwN30."
    "bm7J6b3k_F0JxPFFRTklBDOgHRJTvEa1s-uwvSwVxTs"
)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# ————————————————

PDF_OUTPUT_FOLDER = "static/pdfs"
PLANTILLA_PDF = "Guerrero.pdf"
FOLIO_FILE = "folio_actual.txt"

def cargar_folio():
    if not os.path.exists(FOLIO_FILE):
        with open(FOLIO_FILE, "w") as f:
            f.write("AC0000")
    with open(FOLIO_FILE, "r") as f:
        return f.read().strip()

def incrementar_letras(letras):
    a, b = letras
    if b != "Z":
        b = chr(ord(b) + 1)
    else:
        b = "A"
        a = chr(ord(a) + 1) if a != "Z" else "A"
    return a + b

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    num = int(folio_actual[2:])
    if num < 9999:
        num += 1
    else:
        letras = incrementar_letras(letras)
        num = 1
    nuevo = f"{letras}{num:04d}"
    with open(FOLIO_FILE, "w") as f:
        f.write(nuevo)
    return nuevo

def formatear_fecha(dt):
    meses = {
        "January": "ENERO", "February": "FEBRERO", "March": "MARZO",
        "April": "ABRIL", "May": "MAYO", "June": "JUNIO",
        "July": "JULIO", "August": "AGOSTO", "September": "SEPTIEMBRE",
        "October": "OCTUBRE", "November": "NOVIEMBRE", "December": "DICIEMBRE"
    }
    return f"{dt.day} DE {meses[dt.strftime('%B')]} DE {dt.year}"

def obtener_texto_carac(tipo):
    m = {
        "AUTOMOVIL": "DEL AUTOMÓVIL",
        "MOTOCICLETA": "DE LA MOTOCICLETA",
        "CAMIONETA": "DE LA CAMIONETA",
        "OFICINA MOVIL": "DE LA OFICINA MÓVIL",
        "REMOLQUE": "DEL REMOLQUE"
    }
    return m.get(tipo.upper(), tipo.upper())

def guardar_en_supabase(folio, tipo, marca, linea, año, serie, motor, color, contribuyente, fecha):
    datos = {
        "folio": folio,
        "tipo_vehiculo": tipo,
        "marca": marca,
        "linea": linea,
        "año": año,
        "serie": serie,
        "motor": motor,
        "color": color,
        "contribuyente": contribuyente,
        "fecha_expedicion": fecha
    }
    supabase.table("permisos_guerrero").insert(datos).execute()

def generar_pdf(folio, tipo, marca, linea, año, serie, motor, color, contribuyente, expe, venc):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]
    t = obtener_texto_carac(tipo)
    page.insert_text((1700, 500), folio, fontsize=55, color=(1, 0, 0))
    page.insert_text((1325, 555), f"TLAPA DE COMONFORT, GRO. A {expe}", fontsize=38)
    page.insert_text((400, 1240), f"{expe} AL {venc}", fontsize=60)
    page.insert_text((255, 1550), f"CARACTERÍSTICAS {t}:", fontsize=75)
    page.insert_text((400, 1700), f"NÚMERO DE SERIE: {serie}", fontsize=35)
    page.insert_text((375, 1745), f"NÚMERO DE MOTOR: {motor}", fontsize=35)
    page.insert_text((602, 1790), f"MARCA: {marca}", fontsize=35)
    page.insert_text((575, 1835), f"MODELO: {linea}", fontsize=35)
    page.insert_text((652, 1880), f"AÑO: {año}", fontsize=35)
    page.insert_text((602, 1925), f"COLOR: {color}", fontsize=35)
    page.insert_text((426, 1970), f"CONTRIBUYENTE: {contribuyente}", fontsize=35)
    os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)
    salida = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(salida)
    doc.close()

@app.route("/", methods=["GET", "POST"])
def formulario():
    if request.method == "POST":
        datos = {k: request.form[k].upper() for k in (
            "tipo_vehiculo", "marca", "linea", "año",
            "serie", "motor", "color", "contribuyente"
        )}
        folio_act = cargar_folio()
        fol = siguiente_folio(folio_act)
        ahora = datetime.now()
        expe = formatear_fecha(ahora)
        venc = formatear_fecha(ahora + timedelta(days=30))
        guardar_en_supabase(fol, *datos.values(), expe)
        generar_pdf(fol, *datos.values(), expe, venc)
        return render_template("exito.html", folio=fol)
    return render_template("formulario.html")

@app.route("/descargar/<folio>")
def descargar(folio):
    return send_file(os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf"), as_attachment=True)

@app.route("/panel")
def panel():
    buscar = request.args.get("buscar", "").lower()
    regs = supabase.table("permisos_guerrero").select("*").execute().data
    if buscar:
        regs = [r for r in regs if buscar in r["serie"].lower()]
    return render_template("panel.html", registros=regs)

@app.route("/editar/<folio>", methods=["GET", "POST"])
def editar(folio):
    if request.method == "POST":
        upd = {k: request.form[k].upper() for k in (
            "tipo_vehiculo", "marca", "linea", "año",
            "serie", "motor", "color", "contribuyente"
        )}
        supabase.table("permisos_guerrero").update(upd).eq("folio", folio).execute()
        flash("Registro actualizado.", "success")
        return redirect(url_for("panel"))
    reg = supabase.table("permisos_guerrero").select("*").eq("folio", folio).single().execute().data
    return render_template("editar.html", registro=reg)

@app.route("/eliminar/<folio>")
def eliminar(folio):
    supabase.table("permisos_guerrero").delete().eq("folio", folio).execute()
    flash("Registro eliminado.", "success")
    return redirect(url_for("panel"))

@app.route("/regenerar_pdf/<folio>")
def regenerar_pdf(folio):
    reg = supabase.table("permisos_guerrero").select("*").eq("folio", folio).single().execute().data
    if not reg:
        flash("Folio no encontrado.", "danger")
        return redirect(url_for("panel"))
    ahora = datetime.now()
    venc = formatear_fecha(ahora + timedelta(days=30))
    generar_pdf(
        reg["folio"], reg["tipo_vehiculo"], reg["marca"], reg["linea"],
        reg["año"], reg["serie"], reg["motor"], reg["color"],
        reg["contribuyente"], reg["fecha_expedicion"], venc
    )
    flash("PDF reimpreso.", "success")
    return redirect(url_for("panel"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
