from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from datetime import datetime, timedelta
import fitz  # PyMuPDF
import os
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = "secreto_perro"

# ---------------- CONFIGURACIÓN SUPABASE ----------------
SUPABASE_URL = "https://xsagwqepoljfsogusubw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhzYWd3cWVwb2xqZnNvZ3VzdWJ3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0Mzk2Mzc1NSwiZXhwIjoyMDU5NTM5NzU1fQ.aaTWr2E_l20TlWjdZgKp3ddd3bmtnL22jZisvT_aN0w"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- CONSTANTES ----------------
PDF_OUTPUT_FOLDER = 'static/pdfs'
PLANTILLA_PDF     = 'Guerrero.pdf'
USUARIO_VALIDO    = "elwarrior"
CONTRASENA_VALIDA = "Warrior2025"

# ---------------- FOLIO ----------------
def generar_folio_unico(supabase):
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    inicio_letras = "AD"
    inicio_numero = 6032

    # Empezamos desde AD6032 hasta ZZ9999
    empezar = False
    for letra1 in letras:
        for letra2 in letras:
            combinacion = letra1 + letra2
            for numero in range(1, 10000):
                if not empezar:
                    if combinacion == inicio_letras and numero == inicio_numero:
                        empezar = True
                    else:
                        continue
                folio = f"{combinacion}{str(numero).zfill(4)}"
                existe = supabase.table("borradores_registros").select("folio").eq("folio", folio).execute()
                if not existe.data:
                    return folio
    return None

# ---------------- GUARDAR ----------------
def guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    supabase.table("borradores_registros").insert({
        "folio": folio,
        "marca": marca,
        "linea": linea,
        "anio": anio,
        "numero_serie": serie,
        "numero_motor": motor,
        "color": color,
        "contribuyente": contribuyente,
        "fecha_expedicion": fexp.isoformat(),
        "fecha_vencimiento": fven.isoformat()
    }).execute()

# ---------------- PDF ----------------
def generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, fexp, fven):
    doc = fitz.open(PLANTILLA_PDF)
    page = doc[0]
    page.insert_text((376,769), folio, fontsize=8, color=(1,0,0))
    page.insert_text((122,755), fexp.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((122,768), fven.strftime("%d/%m/%Y"), fontsize=8)
    page.insert_text((376,742), serie, fontsize=8)
    page.insert_text((376,729), motor, fontsize=8)
    page.insert_text((376,700), marca, fontsize=8)
    page.insert_text((376,714), linea, fontsize=8)
    page.insert_text((376,756), color, fontsize=8)
    page.insert_text((122,700), contribuyente, fontsize=8)
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
        if (u:=request.form['usuario'])==USUARIO_VALIDO and (p:=request.form['contraseña'])==CONTRASENA_VALIDA:
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

        folio  = generar_folio_unico(supabase)
        ahora  = datetime.now()
        ven    = ahora + timedelta(days=30)

        guardar_en_supabase(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, ven)
        generar_pdf(folio, marca, linea, anio, serie, motor, color, contribuyente, ahora, ven)
        return render_template('exito.html', folio=folio)
    return render_template('formulario.html')

@app.route('/listar')
def listar():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    res = supabase.table("borradores_registros").select("*").order("id", desc=True).execute()
    registros = []
    for r in res.data:
        registros.append({
            "folio": r["folio"],
            "marca": r["marca"],
            "linea": r["linea"],
            "anio":  r["anio"],
            "serie": r["numero_serie"],
            "motor": r["numero_motor"],
            "color": r["color"],
            "contribuyente": r["contribuyente"],
            "fecha_exp":    datetime.fromisoformat(r["fecha_expedicion"]).strftime("%d/%m/%Y"),
            "fecha_venc":   datetime.fromisoformat(r["fecha_vencimiento"]).strftime("%d/%m/%Y"),
        })
    return render_template('listar.html', registros=registros, ahora=datetime.now())

@app.route('/descargar/<folio>')
def descargar(folio):
    p = os.path.join(PDF_OUTPUT_FOLDER, f"{folio}.pdf")
    return send_file(p, as_attachment=True) if os.path.exists(p) else ("No existe",404)

@app.route('/reimprimir', methods=['GET','POST'])
def reimprimir():
    if request.method=='POST':
        fol = request.form['folio'].strip().upper()
        return redirect(url_for('descargar', folio=fol))
    return render_template('reimprimir.html')

@app.route('/renovar/<folio>')
def renovar(folio):
    res = supabase.table("borradores_registros").select("*").eq("folio", folio).limit(1).execute()
    if not res.data:
        flash("Folio no encontrado","danger")
        return redirect(url_for('listar'))
    row = res.data[0]
    nuevo = generar_folio_unico(supabase)
    hoy   = datetime.now()
    ven   = hoy + timedelta(days=30)
    guardar_en_supabase(nuevo, row["marca"], row["linea"], row["anio"],
                        row["numero_serie"], row["numero_motor"],
                        row["color"], row["contribuyente"], hoy, ven)
    generar_pdf(nuevo, row["marca"], row["linea"], row["anio"],
                row["numero_serie"], row["numero_motor"],
                row["color"], row["contribuyente"], hoy, ven)
    flash(f"Renovado folio {nuevo}","success")
    return redirect(url_for('descargar', folio=nuevo))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/eliminar_varios', methods=['POST'])
def eliminar_varios():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    folios = request.form.getlist('folios')
    if folios:
        for folio in folios:
            supabase.table("borradores_registros").delete().eq("folio", folio).execute()
        flash(f"Eliminados: {', '.join(folios)}", "success")
    else:
        flash("No seleccionaste ningún folio", "warning")
    return redirect(url_for('listar'))

if __name__ == '__main__':
    app.run(debug=True)
