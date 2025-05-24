from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os
from supabase import create_client, Client

# ---------------- INICIALIZAR FLASK Y SUPABASE ----------------
app = Flask(__name__)
app.secret_key = "secreto_perro"

SUPABASE_URL = "https://xsagwqepoljfsogusubw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzYWd3cWVwb2xqZnNvZ3VzdWJ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM5NjM3NTUsImV4cCI6MjA1OTUzOTc1NX0.NUixULn0m2o49At8j6X58UqbXre2O2_JStqzls_8Gws"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF       = 'Guerrero.pdf'
REGISTRO_FILE       = 'data/registros.txt'

USUARIO_VALIDO      = "elwarrior"
CONTRASENA_VALIDA   = "Warrior2025"

# ---------------- FUNCIONES DE FOLIO ----------------
def cargar_folio():
    resp = (
        supabase
        .table("borradores_registros")
        .select("fol_texto")
        .order("id", desc=True)     # ← usa `desc=True` para ordenar descendente
        .limit(1)
        .execute()
    )
    if resp.data and len(resp.data):
        return resp.data[0]["fol_texto"]
    return "AA0001"

def siguiente_folio(folio_actual):
    letras = folio_actual[:2]
    try:
        num = int(folio_actual[2:])
    except:
        num = 0
    if num < 9999:
        num += 1
    else:
        letras = incrementar_letras(letras)
        num = 1
    return f"{letras}{num:04d}"

def incrementar_letras(l):
    a, b = l
    if b != 'Z':
        b = chr(ord(b) + 1)
    else:
        b = 'A'
        a = chr(ord(a) + 1) if a != 'Z' else 'A'
    return a + b

# ---------------- GUARDAR DATOS ----------------
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

def guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp_str, fven_str):
    os.makedirs(os.path.dirname(REGISTRO_FILE), exist_ok=True)
    with open(REGISTRO_FILE, 'a', encoding='utf-8') as f:
        f.write(f"{folio}|{marca}|{linea}|{anio}|{serie}|{motor}|{color}|{contribuyente}|{fexp_str}|{fven_str}\n")

# ---------------- GENERAR PDF ----------------
def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]
    # Normal
    page.insert_text((376,769), folio, fontsize=8, color=(1,0,0))
    page.insert_text((122,755), fexp.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((122,768), fven.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((376,742), serie, fontsize=8)
    page.insert_text((376,729), motor, fontsize=8)
    page.insert_text((376,700), marca, fontsize=8)
    page.insert_text((376,714), linea, fontsize=8)
    page.insert_text((376,756), color, fontsize=8)
    page.insert_text((122,700), contribuyente, fontsize=8)
    # Rotado
    page.insert_text((440,200), folio, fontsize=83, rotate=270)
    page.insert_text((77,205), fexp.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((63,205), fven.strftime("%d/%m/%Y"), fontsize=8, rotate=270)
    page.insert_text((168,110), serie, fontsize=18, rotate=270)
    page.insert_text((224,110), motor, fontsize=18, rotate=270)
    page.insert_text((280,110), marca, fontsize=18, rotate=270)
    page.insert_text((280,340), linea, fontsize=18, rotate=270)
    page.insert_text((305,530), anio, fontsize=18, rotate=270)
    page.insert_text((224,410), color, fontsize=18, rotate=270)
    page.insert_text((115,205), contribuyente, fontsize=8, rotate=270)
    os.makedirs(PDF_OUTPUT_FOLDER, exist_ok=True)
    out = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    doc.save(out)
    doc.close()

# ---------------- RUTAS ----------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form['usuario']
        p = request.form['contraseña']
        if u==USUARIO_VALIDO and p==CONTRASENA_VALIDA:
            session['usuario']=u
            return redirect(url_for('panel'))
        flash('Credenciales incorrectas','danger')
    return render_template('login.html')

@app.route('/panel')
def panel():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('panel.html')

@app.route('/formulario', methods=['GET','POST'])
def formulario():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        marca         = request.form['marca'].upper()
        linea         = request.form['linea'].upper()
        anio          = request.form['anio'].upper()
        serie         = request.form['serie'].upper()
        motor         = request.form['motor'].upper()
        color         = request.form['color'].upper()
        contribuyente = request.form['contribuyente'].upper()
        dias          = int(request.form.get('validez', 30))

        folio = siguiente_folio(cargar_folio())
        ahora = datetime.now()
        venc  = ahora + timedelta(days=dias)

        guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, venc)
        guardar_en_txt(folio, marca, linea, anio, serie, motor, color, contribuyente,
                       ahora.strftime("%d/%m/%Y"), venc.strftime("%d/%m/%Y"))
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, venc)
        return render_template('exito.html', folio=folio)
    return render_template('formulario.html')

@app.route('/consultar', methods=['GET','POST'])
def consultar():
    if request.method=='POST':
        fol = request.form['folio'].strip().upper()
        pth = os.path.join(PDF_OUTPUT_FOLDER, f"{fol}.pdf")
        if os.path.exists(pth):
            return send_file(pth, as_attachment=True)
        flash("Folio no encontrado","danger")
    return render_template('reimprimir.html')

@app.route('/descargar/<folio>')
def descargar(folio):
    pth = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    if os.path.exists(pth):
        return send_file(pth, as_attachment=True)
    return "Archivo no existe",404

@app.route('/listar')
def listar():
    if not os.path.exists(REGISTRO_FILE):
        os.makedirs(os.path.dirname(REGISTRO_FILE), exist_ok=True)
        open(REGISTRO_FILE,'a').close()
    registros=[]
    with open(REGISTRO_FILE,'r',encoding='utf-8') as f:
        for ln in f:
            d=ln.strip().split('|')
            if len(d)==10:
                registros.append({
                    "folio":d[0],"marca":d[1],"linea":d[2],"anio":d[3],
                    "serie":d[4],"motor":d[5],"color":d[6],
                    "contribuyente":d[7],"fecha_exp":d[8],"fecha_venc":d[9]
                })
    return render_template('listar.html', registros=registros, ahora=datetime.now())

@app.route('/reimprimir', methods=['GET','POST'])
def reimprimir():
    if request.method=='POST':
        fol = request.form['folio'].strip().upper()
        pth = os.path.join(PDF_OUTPUT_FOLDER, f"{fol}.pdf")
        if os.path.exists(pth):
            return send_file(pth, as_attachment=True)
        flash("No se encontró el PDF","danger")
    return render_template('reimprimir.html')

@app.route('/renovar/<folio>')
def renovar(folio):
    if not os.path.exists(REGISTRO_FILE):
        flash("Registros no existen","danger")
        return redirect(url_for('listar'))
    datos=None
    for ln in open(REGISTRO_FILE,'r',encoding='utf-8'):
        p=ln.strip().split('|')
        if len(p)==10 and p[0]==folio:
            fv=datetime.strptime(p[9],"%d/%m/%Y")
            if datetime.now()>=fv:
                datos=p
            break
    if not datos:
        flash("No vence o no existe","warning")
        return redirect(url_for('listar'))
    _,ma,li,an,se,mo,co,ct,fe,fv=datos
    nuevo=siguiente_folio(cargar_folio())
    hoy=datetime.now()
    ven=hoy+timedelta(days=30)
    guardar_en_supabase(nuevo,ma,li,an,se,mo,co,ct,hoy,ven)
    guardar_en_txt(nuevo,ma,li,an,se,mo,co,ct,
                   hoy.strftime("%d/%m/%Y"), ven.strftime("%d/%m/%Y"))
    generar_pdf(nuevo,ma,li,an,se,mo,co,ct,hoy,ven)
    flash(f"Renovado folio {nuevo}","success")
    return redirect(url_for('descargar', folio=nuevo))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)
