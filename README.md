# Sistema Web Local para Generar PDFs

Este sistema permite llenar un formulario web y generar automáticamente un PDF sobre la plantilla `cdmxdigital2025ppp.pdf`, con campos insertados en coordenadas específicas.

## Uso Local
```bash
pip install -r requirements.txt
python main.py
```

## Deploy en Render
- Runtime: Python 3
- Start command: `gunicorn main:app`

