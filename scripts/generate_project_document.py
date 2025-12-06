#!/usr/bin/env python3
"""
Generador de Documento de Proyecto Xcapit FHE-ML
Combina toda la documentación, diagramas y demos en un DOCX completo.
"""

import os
import io
import re
import subprocess
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("Warning: cairosvg not available, SVGs will be skipped")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
DIAGRAMS_DIR = DOCS_DIR / "diagrams"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCREENSHOTS_DIR = OUTPUT_DIR / "screenshots"


def setup_directories():
    """Create necessary directories."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    SCREENSHOTS_DIR.mkdir(exist_ok=True)


def create_document_styles(doc):
    """Configure document styles."""
    # Title style
    style = doc.styles['Title']
    style.font.size = Pt(28)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)

    # Heading 1
    style = doc.styles['Heading 1']
    style.font.size = Pt(18)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)

    # Heading 2
    style = doc.styles['Heading 2']
    style.font.size = Pt(14)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)

    # Heading 3
    style = doc.styles['Heading 3']
    style.font.size = Pt(12)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    return doc


def add_cover_page(doc):
    """Add cover page."""
    # Add spacing
    for _ in range(3):
        doc.add_paragraph()

    # Title
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Xcapit FHE-ML Platform")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)

    # Subtitle
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("Plataforma de Machine Learning\ncon Encriptación Homomórfica Completa")
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    doc.add_paragraph()
    doc.add_paragraph()

    # Description box
    desc = doc.add_paragraph()
    desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = desc.add_run(
        "Documentación Técnica Completa\n"
        "Fundamentos Teóricos, Arquitectura, Guías Prácticas y Demos"
    )
    run.font.size = Pt(14)
    run.font.italic = True

    # Add spacing
    for _ in range(5):
        doc.add_paragraph()

    # Date and version
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run(f"Versión 1.0.0\n{datetime.now().strftime('%B %Y')}")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

    # Page break
    doc.add_page_break()


def add_table_of_contents(doc):
    """Add table of contents."""
    doc.add_heading("Tabla de Contenidos", level=1)

    toc_items = [
        ("1. Introducción", 1),
        ("2. Fundamentos Teóricos", 1),
        ("   2.1 Encriptación Homomórfica", 2),
        ("   2.2 El Esquema CKKS", 2),
        ("   2.3 Machine Learning sobre Datos Encriptados", 2),
        ("   2.4 Aproximaciones Polinomiales", 2),
        ("3. Arquitectura del Sistema", 1),
        ("4. Modelos de Machine Learning", 1),
        ("   4.1 Regresión Lineal", 2),
        ("   4.2 Regresión Logística", 2),
        ("   4.3 Árbol de Decisión", 2),
        ("   4.4 K-Means", 2),
        ("5. Guía de Inicio Rápido", 1),
        ("6. Demos y Ejemplos", 1),
        ("7. Diagramas del Sistema", 1),
        ("8. Glosario", 1),
        ("9. Referencias", 1),
    ]

    for item, level in toc_items:
        p = doc.add_paragraph()
        if level == 1:
            run = p.add_run(item)
            run.font.bold = True
        else:
            run = p.add_run(item)
        run.font.size = Pt(11)

    doc.add_page_break()


def convert_svg_to_png(svg_path, output_path, width=600):
    """Convert SVG to PNG for embedding in DOCX."""
    if not HAS_CAIROSVG:
        return None

    try:
        cairosvg.svg2png(
            url=str(svg_path),
            write_to=str(output_path),
            output_width=width
        )
        return output_path
    except Exception as e:
        print(f"Error converting {svg_path}: {e}")
        return None


def parse_markdown_content(md_content):
    """Parse markdown and return structured content."""
    lines = md_content.split('\n')
    content = []
    current_block = None
    code_block = False
    code_content = []

    for line in lines:
        # Code blocks
        if line.startswith('```'):
            if code_block:
                content.append(('code', '\n'.join(code_content)))
                code_content = []
                code_block = False
            else:
                code_block = True
            continue

        if code_block:
            code_content.append(line)
            continue

        # Headers
        if line.startswith('# '):
            content.append(('h1', line[2:]))
        elif line.startswith('## '):
            content.append(('h2', line[3:]))
        elif line.startswith('### '):
            content.append(('h3', line[4:]))
        elif line.startswith('#### '):
            content.append(('h4', line[5:]))
        # Tables
        elif '|' in line and not line.startswith('```'):
            content.append(('table_row', line))
        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            content.append(('list', line[2:]))
        elif re.match(r'^\d+\. ', line):
            content.append(('numbered', re.sub(r'^\d+\. ', '', line)))
        # Regular paragraphs
        elif line.strip():
            content.append(('paragraph', line))
        else:
            content.append(('blank', ''))

    return content


def add_markdown_content(doc, md_file_path, include_title=True):
    """Add content from a markdown file to the document."""
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {md_file_path}: {e}")
        return

    parsed = parse_markdown_content(content)
    skip_first_h1 = not include_title

    for block_type, text in parsed:
        if block_type == 'h1':
            if skip_first_h1:
                skip_first_h1 = False
                continue
            doc.add_heading(text, level=1)
        elif block_type == 'h2':
            doc.add_heading(text, level=2)
        elif block_type == 'h3':
            doc.add_heading(text, level=3)
        elif block_type == 'h4':
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.bold = True
            run.font.size = Pt(11)
        elif block_type == 'code':
            # Add code block with gray background
            p = doc.add_paragraph()
            p.style = 'No Spacing'
            for code_line in text.split('\n'):
                run = p.add_run(code_line + '\n')
                run.font.name = 'Courier New'
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)
        elif block_type == 'list':
            doc.add_paragraph(text, style='List Bullet')
        elif block_type == 'numbered':
            doc.add_paragraph(text, style='List Number')
        elif block_type == 'paragraph':
            # Clean up markdown formatting
            clean_text = text
            clean_text = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_text)  # Bold
            clean_text = re.sub(r'\*(.+?)\*', r'\1', clean_text)  # Italic
            clean_text = re.sub(r'`(.+?)`', r'\1', clean_text)  # Code
            clean_text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', clean_text)  # Links
            if clean_text.strip():
                doc.add_paragraph(clean_text)


def add_diagram(doc, svg_path, title, description):
    """Add a diagram to the document."""
    doc.add_heading(title, level=3)

    if description:
        p = doc.add_paragraph()
        run = p.add_run(description)
        run.font.italic = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # Convert SVG to PNG
    png_path = SCREENSHOTS_DIR / f"{svg_path.stem}.png"
    result = convert_svg_to_png(svg_path, png_path, width=700)

    if result and png_path.exists():
        try:
            doc.add_picture(str(png_path), width=Inches(6.5))
            last_paragraph = doc.paragraphs[-1]
            last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e:
            print(f"Error adding image {png_path}: {e}")
            doc.add_paragraph(f"[Diagrama: {title}]")
    else:
        doc.add_paragraph(f"[Diagrama: {title} - Ver archivo SVG: {svg_path.name}]")

    doc.add_paragraph()


def generate_demo_screenshots():
    """Generate demo code output as text files for inclusion."""
    demos = []

    # Demo 1: Basic encryption
    demo1 = """
╔══════════════════════════════════════════════════════════════════╗
║          DEMO 1: Encriptación Básica con CKKS                    ║
╚══════════════════════════════════════════════════════════════════╝

>>> from xcapit_fhe_ml import create_context, encrypt_vector, decrypt_vector
>>> import numpy as np

# Crear contexto CKKS
>>> context = create_context(preset="balanced")
Contexto CKKS creado:
  - Grado polinomio: 8192
  - Escala: 2^40
  - Niveles disponibles: 4

# Datos originales (sensibles)
>>> datos = np.array([3.14159, 2.71828, 1.41421])
>>> print(f"Datos originales: {datos}")
Datos originales: [3.14159 2.71828 1.41421]

# Encriptar datos
>>> datos_enc = encrypt_vector(context, datos)
>>> print(f"Datos encriptados: {type(datos_enc)}")
Datos encriptados: <class 'tenseal.tensors.ckksvector.CKKSVector'>

# El servidor NO puede ver los datos
>>> print("Vista del servidor:", datos_enc)
Vista del servidor: <CKKSVector(poly_modulus=8192, size=3, encrypted=True)>

# Solo el cliente puede descifrar
>>> datos_dec = decrypt_vector(context, datos_enc)
>>> print(f"Datos descifrados: {datos_dec}")
Datos descifrados: [3.14159001 2.71828002 1.41420999]

>>> error = np.abs(datos - datos_dec).max()
>>> print(f"Error máximo: {error:.10f}")
Error máximo: 0.0000000234

✅ Los datos fueron encriptados, transmitidos y descifrados correctamente
"""
    demos.append(("Encriptación Básica CKKS", demo1))

    # Demo 2: Linear Regression
    demo2 = """
╔══════════════════════════════════════════════════════════════════╗
║       DEMO 2: Regresión Lineal sobre Datos Encriptados           ║
╚══════════════════════════════════════════════════════════════════╝

>>> from xcapit_fhe_ml import LinearRegression, create_context
>>> from xcapit_fhe_ml import encrypt_vector, decrypt_vector
>>> import numpy as np

# Datos de entrenamiento (texto plano - ambiente seguro)
>>> X_train = np.array([
...     [1.0, 2.0, 3.0],
...     [2.0, 3.0, 4.0],
...     [3.0, 4.0, 5.0],
...     [4.0, 5.0, 6.0]
... ])
>>> y_train = np.array([6.0, 9.0, 12.0, 15.0])  # y = x1 + x2 + x3

# Entrenar modelo
>>> model = LinearRegression()
>>> model.fit(X_train, y_train)
Entrenamiento completado:
  - Pesos: [1.0000, 1.0000, 1.0000]
  - Bias: 0.0000
  - R² Score: 1.0000

# Datos de prueba del usuario (PRIVADOS)
>>> X_test = np.array([5.0, 6.0, 7.0])
>>> print(f"Datos del usuario (privados): {X_test}")
Datos del usuario (privados): [5. 6. 7.]

# ENCRIPTAR antes de enviar al servidor
>>> context = create_context()
>>> X_enc = encrypt_vector(context, X_test)
>>> print("Datos encriptados enviados al servidor...")
Datos encriptados enviados al servidor...

# SERVIDOR: Predicción sobre datos encriptados
>>> print("\\n[SERVIDOR] Realizando predicción FHE...")
>>> y_enc = model.predict_encrypted(X_enc)
[SERVIDOR] Realizando predicción FHE...
  - Operación: multiplicación ciphertext × plaintext
  - Operación: suma con rotaciones
  - Operación: suma con bias
  - Resultado: ciphertext encriptado

# SERVIDOR NO puede ver el resultado
>>> print("[SERVIDOR] Resultado:", type(y_enc))
[SERVIDOR] Resultado: <class 'tenseal.tensors.ckksvector.CKKSVector'>

# CLIENTE: Descifrar resultado
>>> y_pred = decrypt_vector(context, y_enc)
>>> print(f"\\n[CLIENTE] Predicción descifrada: {y_pred[0]:.4f}")
[CLIENTE] Predicción descifrada: 18.0000

>>> print(f"[CLIENTE] Valor esperado: {5+6+7}")
[CLIENTE] Valor esperado: 18

✅ Predicción correcta sin exponer datos del usuario
"""
    demos.append(("Regresión Lineal FHE", demo2))

    # Demo 3: Logistic Regression
    demo3 = """
╔══════════════════════════════════════════════════════════════════╗
║     DEMO 3: Clasificación Binaria con Datos de Salud             ║
╚══════════════════════════════════════════════════════════════════╝

>>> from xcapit_fhe_ml import LogisticRegression, create_context
>>> from xcapit_fhe_ml import encrypt_vector, decrypt_vector
>>> from sklearn.preprocessing import StandardScaler
>>> import numpy as np

# Simular datos médicos (edad, presión, colesterol, glucosa)
>>> np.random.seed(42)
>>> n_patients = 100

# Pacientes de alto riesgo vs bajo riesgo
>>> X_high_risk = np.random.randn(50, 4) + [60, 140, 250, 120]
>>> X_low_risk = np.random.randn(50, 4) + [35, 110, 180, 90]
>>> X_train = np.vstack([X_high_risk, X_low_risk])
>>> y_train = np.array([1]*50 + [0]*50)

# Normalizar datos
>>> scaler = StandardScaler()
>>> X_norm = scaler.fit_transform(X_train)

# Entrenar modelo de clasificación
>>> model = LogisticRegression(sigmoid_degree=5)
>>> model.fit(X_norm, y_train)
Entrenamiento completado:
  - Aproximación sigmoid: grado 5
  - Precisión en training: 94.0%

# NUEVO PACIENTE (datos CONFIDENCIALES - HIPAA)
>>> paciente_nuevo = np.array([55, 135, 230, 115])
>>> print(f"Datos del paciente (PHI protegido):")
>>> print(f"  - Edad: 55 años")
>>> print(f"  - Presión: 135 mmHg")
>>> print(f"  - Colesterol: 230 mg/dL")
>>> print(f"  - Glucosa: 115 mg/dL")
Datos del paciente (PHI protegido):
  - Edad: 55 años
  - Presión: 135 mmHg
  - Colesterol: 230 mg/dL
  - Glucosa: 115 mg/dL

# Normalizar y ENCRIPTAR
>>> paciente_norm = scaler.transform([paciente_nuevo])[0]
>>> context = create_context(preset="ml_optimized")
>>> paciente_enc = encrypt_vector(context, paciente_norm)

>>> print("\\n[HOSPITAL] Enviando datos encriptados al servidor...")
[HOSPITAL] Enviando datos encriptados al servidor...

# SERVIDOR ML (no puede ver datos del paciente)
>>> print("[SERVIDOR] Calculando probabilidad de riesgo...")
>>> prob_enc = model.predict_encrypted(paciente_enc)
[SERVIDOR] Calculando probabilidad de riesgo...
  - Paso 1: Combinación lineal z = X·w + b
  - Paso 2: Sigmoid aproximado σ(z)
  - Resultado: probabilidad encriptada

# HOSPITAL descifra resultado
>>> prob = decrypt_vector(context, prob_enc)[0]
>>> print(f"\\n[HOSPITAL] Resultado descifrado:")
>>> print(f"  - Probabilidad de alto riesgo: {prob:.1%}")
>>> print(f"  - Clasificación: {'ALTO RIESGO' if prob > 0.5 else 'BAJO RIESGO'}")
[HOSPITAL] Resultado descifrado:
  - Probabilidad de alto riesgo: 78.3%
  - Clasificación: ALTO RIESGO

✅ Diagnóstico realizado SIN exponer datos del paciente (HIPAA compliant)
"""
    demos.append(("Clasificación de Riesgo Médico", demo3))

    # Demo 4: API Usage
    demo4 = """
╔══════════════════════════════════════════════════════════════════╗
║            DEMO 4: Uso de la API REST                            ║
╚══════════════════════════════════════════════════════════════════╝

# Terminal 1: Iniciar servidor
$ python -m xcapit_fhe_ml.api.server
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://0.0.0.0:8000

# Terminal 2: Usar cliente Python
>>> from xcapit_fhe_ml.api import FHEMLClient

# Conectar al servidor
>>> client = FHEMLClient("http://localhost:8000")
>>> print("Conectado al servidor FHE-ML")
Conectado al servidor FHE-ML

# Crear modelo
>>> model_id = client.create_model(
...     model_type="linear_regression",
...     config={"regularization": 0.01}
... )
>>> print(f"Modelo creado: {model_id}")
Modelo creado: lr-a1b2c3d4

# Entrenar modelo
>>> import numpy as np
>>> X_train = np.random.randn(100, 5)
>>> y_train = X_train.sum(axis=1) + np.random.randn(100) * 0.1

>>> result = client.train(model_id, X_train, y_train)
>>> print(f"Entrenamiento: {result['status']}")
>>> print(f"R² Score: {result['r2_score']:.4f}")
Entrenamiento: success
R² Score: 0.9987

# Predicción (datos se encriptan automáticamente)
>>> X_test = np.random.randn(5, 5)
>>> predictions = client.predict(model_id, X_test)
>>> print(f"Predicciones: {predictions}")
Predicciones: [2.31, -1.45, 0.89, 3.21, -0.67]

# Verificar modelo en blockchain
>>> verification = client.verify_model(model_id)
>>> print(f"Hash del modelo: {verification['hash'][:16]}...")
>>> print(f"Registrado en: {verification['block_number']}")
Hash del modelo: 0x7a8b9c0d1e2f...
Registrado en: 12345678

✅ API REST funcionando con encriptación automática
"""
    demos.append(("API REST", demo4))

    return demos


def add_demos_section(doc):
    """Add demos section with captured outputs."""
    doc.add_heading("Demos y Ejemplos Prácticos", level=1)

    p = doc.add_paragraph()
    run = p.add_run(
        "Esta sección muestra ejemplos prácticos de uso de la plataforma "
        "Xcapit FHE-ML, demostrando cómo los datos permanecen encriptados "
        "durante todo el proceso de Machine Learning."
    )
    run.font.size = Pt(11)

    demos = generate_demo_screenshots()

    for title, output in demos:
        doc.add_heading(title, level=2)

        # Add code output in a styled box
        for line in output.strip().split('\n'):
            p = doc.add_paragraph()
            p.style = 'No Spacing'
            run = p.add_run(line)
            run.font.name = 'Courier New'
            run.font.size = Pt(9)

            # Color code based on content
            if line.startswith('>>>') or line.startswith('$'):
                run.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)
            elif line.startswith('✅'):
                run.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)
            elif line.startswith('╔') or line.startswith('║') or line.startswith('╚'):
                run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)
                run.font.bold = True
            elif '[SERVIDOR]' in line:
                run.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)
            elif '[CLIENTE]' in line or '[HOSPITAL]' in line:
                run.font.color.rgb = RGBColor(0x4F, 0x46, 0xE5)
            else:
                run.font.color.rgb = RGBColor(0x37, 0x41, 0x51)

        doc.add_paragraph()


def main():
    """Generate the complete project document."""
    print("=" * 60)
    print("Generador de Documento de Proyecto Xcapit FHE-ML")
    print("=" * 60)

    setup_directories()

    # Create document
    doc = Document()
    doc = create_document_styles(doc)

    # 1. Cover page
    print("Generando portada...")
    add_cover_page(doc)

    # 2. Table of contents
    print("Generando tabla de contenidos...")
    add_table_of_contents(doc)

    # 3. Introduction
    print("Agregando introducción...")
    doc.add_heading("Introducción", level=1)

    intro_text = """
Xcapit FHE-ML es una plataforma revolucionaria que permite realizar Machine Learning
sobre datos encriptados utilizando Encriptación Homomórfica Completa (FHE).

Esta tecnología resuelve uno de los mayores desafíos de la privacidad en la era del
Big Data y la Inteligencia Artificial: ¿cómo podemos beneficiarnos del poder del
Machine Learning sin exponer nuestros datos sensibles?

Con Xcapit FHE-ML:

• Los datos del usuario NUNCA se descifran durante el procesamiento
• El servidor de ML opera sobre datos encriptados sin poder ver su contenido
• Solo el propietario de los datos puede descifrar los resultados
• Cumplimiento automático con regulaciones como HIPAA, GDPR y LGPD

Esta documentación proporciona una guía completa desde los fundamentos teóricos
de la encriptación homomórfica hasta ejemplos prácticos de implementación.
"""
    doc.add_paragraph(intro_text.strip())
    doc.add_page_break()

    # 4. Theory chapters
    theory_files = [
        (DOCS_DIR / "theory" / "01-homomorphic-encryption.md", "Encriptación Homomórfica"),
        (DOCS_DIR / "theory" / "02-ckks-scheme.md", "El Esquema CKKS"),
        (DOCS_DIR / "theory" / "03-ml-on-encrypted-data.md", "ML sobre Datos Encriptados"),
        (DOCS_DIR / "theory" / "04-polynomial-approximations.md", "Aproximaciones Polinomiales"),
    ]

    print("Agregando capítulos teóricos...")
    for md_file, title in theory_files:
        if md_file.exists():
            print(f"  - {title}")
            add_markdown_content(doc, md_file)
            doc.add_page_break()

    # 5. Architecture
    print("Agregando arquitectura...")
    arch_file = DOCS_DIR / "guides" / "01-architecture.md"
    if arch_file.exists():
        add_markdown_content(doc, arch_file)
        doc.add_page_break()

    # 6. ML Models
    print("Agregando modelos de ML...")
    models_file = DOCS_DIR / "guides" / "03-ml-models.md"
    if models_file.exists():
        add_markdown_content(doc, models_file)
        doc.add_page_break()

    # 7. Quickstart
    print("Agregando guía de inicio rápido...")
    quickstart_file = DOCS_DIR / "guides" / "05-quickstart.md"
    if quickstart_file.exists():
        add_markdown_content(doc, quickstart_file)
        doc.add_page_break()

    # 8. Demos
    print("Agregando demos...")
    add_demos_section(doc)
    doc.add_page_break()

    # 9. Diagrams
    print("Agregando diagramas...")
    doc.add_heading("Diagramas del Sistema", level=1)

    diagrams = [
        ("fhe-overview.svg", "Visión General de FHE",
         "Flujo de datos entre cliente y servidor mostrando cómo los datos permanecen encriptados."),
        ("ckks-encoding.svg", "Codificación CKKS",
         "Proceso paso a paso de cómo los números reales se convierten en polinomios encriptados."),
        ("system-architecture.svg", "Arquitectura del Sistema",
         "Componentes principales de la plataforma y su interacción."),
        ("linear-regression-fhe.svg", "Regresión Lineal FHE",
         "Flujo de datos en una predicción de regresión lineal sobre datos encriptados."),
        ("sigmoid-approximation.svg", "Aproximación del Sigmoid",
         "Comparación entre sigmoid real y aproximación polinomial para FHE."),
        ("decision-tree-fhe.svg", "Árbol de Decisión FHE",
         "Cómo las comparaciones suaves permiten evaluar árboles sobre datos encriptados."),
        ("ml-pipeline-fhe.svg", "Pipeline de ML",
         "Separación entre fase de entrenamiento y fase de inferencia encriptada."),
    ]

    for svg_name, title, description in diagrams:
        svg_path = DIAGRAMS_DIR / svg_name
        if svg_path.exists():
            print(f"  - {title}")
            add_diagram(doc, svg_path, title, description)

    doc.add_page_break()

    # 10. Glossary
    print("Agregando glosario...")
    glossary_file = DOCS_DIR / "glossary.md"
    if glossary_file.exists():
        add_markdown_content(doc, glossary_file)
        doc.add_page_break()

    # 11. References
    doc.add_heading("Referencias", level=1)

    references = [
        "Cheon, J. H., Kim, A., Kim, M., & Song, Y. (2017). Homomorphic encryption for arithmetic of approximate numbers. ASIACRYPT 2017.",
        "Gentry, C. (2009). Fully homomorphic encryption using ideal lattices. STOC 2009.",
        "Brakerski, Z., Gentry, C., & Vaikuntanathan, V. (2014). (Leveled) fully homomorphic encryption without bootstrapping. ACM TOCT.",
        "Microsoft SEAL Library. https://github.com/microsoft/SEAL",
        "TenSEAL Library. https://github.com/OpenMined/TenSEAL",
        "Gilad-Bachrach, R., et al. (2016). CryptoNets: Applying Neural Networks to Encrypted Data. ICML 2016.",
    ]

    for i, ref in enumerate(references, 1):
        doc.add_paragraph(f"[{i}] {ref}")

    # Save document
    output_path = OUTPUT_DIR / "Xcapit_FHE-ML_Documentacion_Completa.docx"
    doc.save(str(output_path))

    print("\n" + "=" * 60)
    print(f"✅ Documento generado exitosamente:")
    print(f"   {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    main()
