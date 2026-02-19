#!/usr/bin/env python3
"""
Generate unified PDF documentation for Xcapit FHE-ML Platform
"""

import os
import markdown
from weasyprint import HTML, CSS
from datetime import datetime

DOCS_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAMS_DIR = os.path.join(DOCS_DIR, "diagrams")

# CSS for the PDF
CSS_STYLES = """
@page {
    size: A4;
    margin: 2cm;
    @top-center {
        content: "Xcapit FHE-ML Platform - Technical Documentation";
        font-size: 10pt;
        color: #666;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-size: 10pt;
        color: #666;
    }
}

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #1a1a2e;
}

h1 {
    color: #6366f1;
    font-size: 28pt;
    border-bottom: 3px solid #6366f1;
    padding-bottom: 10px;
    margin-top: 40px;
    page-break-before: always;
}

h1:first-of-type {
    page-break-before: avoid;
}

h2 {
    color: #4f46e5;
    font-size: 18pt;
    margin-top: 30px;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 5px;
}

h3 {
    color: #7c3aed;
    font-size: 14pt;
    margin-top: 20px;
}

h4 {
    color: #8b5cf6;
    font-size: 12pt;
}

code {
    background-color: #f3f4f6;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 10pt;
}

pre {
    background-color: #1e1e2e;
    color: #cdd6f4;
    padding: 15px;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.4;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    padding: 0;
    color: inherit;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
    font-size: 10pt;
    page-break-inside: avoid;
}

th {
    background-color: #6366f1;
    color: white;
    padding: 12px;
    text-align: left;
}

td {
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
}

tr:nth-child(even) {
    background-color: #f9fafb;
}

blockquote {
    border-left: 4px solid #6366f1;
    margin: 20px 0;
    padding: 10px 20px;
    background-color: #f5f3ff;
}

ul, ol {
    margin: 15px 0;
    padding-left: 30px;
}

li {
    margin: 5px 0;
}

.diagram {
    text-align: center;
    margin: 30px 0;
    page-break-inside: avoid;
}

.diagram img {
    max-width: 100%;
    height: auto;
}

.diagram-caption {
    font-style: italic;
    color: #666;
    margin-top: 10px;
}

.cover-page {
    text-align: center;
    padding-top: 200px;
    page-break-after: always;
}

.cover-title {
    font-size: 36pt;
    color: #6366f1;
    margin-bottom: 20px;
}

.cover-subtitle {
    font-size: 18pt;
    color: #4b5563;
    margin-bottom: 40px;
}

.cover-info {
    font-size: 12pt;
    color: #6b7280;
}

.toc {
    page-break-after: always;
}

.toc h2 {
    border-bottom: none;
}

.toc ul {
    list-style: none;
    padding-left: 0;
}

.toc li {
    padding: 5px 0;
    border-bottom: 1px dotted #ccc;
}

.highlight-box {
    background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
    border: 1px solid #c4b5fd;
    border-radius: 8px;
    padding: 15px;
    margin: 20px 0;
}

.warning-box {
    background: #fef2f2;
    border: 1px solid #fca5a5;
    border-left: 4px solid #ef4444;
    padding: 15px;
    margin: 20px 0;
}

.success-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-left: 4px solid #10b981;
    padding: 15px;
    margin: 20px 0;
}
"""

def read_markdown_file(filename):
    """Read and convert markdown file to HTML."""
    filepath = os.path.join(DOCS_DIR, filename)
    if not os.path.exists(filepath):
        return ""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
    html = md.convert(content)
    return html

def create_cover_page():
    """Create cover page HTML."""
    return f"""
    <div class="cover-page">
        <div class="cover-title">🔐 Xcapit FHE-ML Platform</div>
        <div class="cover-subtitle">Privacy-Preserving Machine Learning<br>Technical Documentation</div>
        <div class="cover-info">
            <p><strong>Version:</strong> 1.0</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d')}</p>
            <p><strong>Network:</strong> Arbitrum Sepolia (Testnet)</p>
            <p>&nbsp;</p>
            <p>Fully Homomorphic Encryption + Blockchain Governance</p>
            <p>&nbsp;</p>
            <p><em>privacy@xcapit.com</em></p>
            <p><em>https://xcapit-privacy.vercel.app</em></p>
        </div>
    </div>
    """

def create_toc():
    """Create table of contents."""
    return """
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
            <li><strong>1. Use Cases</strong>
                <ul>
                    <li>1.1 Fraud Detection (Banking Consortium)</li>
                    <li>1.2 Medical Research (Healthcare)</li>
                    <li>1.3 Credit Scoring (Fintech)</li>
                </ul>
            </li>
            <li><strong>2. Technical Architecture</strong>
                <ul>
                    <li>2.1 Platform Overview</li>
                    <li>2.2 FHE Component (TenSEAL)</li>
                    <li>2.3 Blockchain Component (Arbitrum)</li>
                    <li>2.4 Backend (Django)</li>
                </ul>
            </li>
            <li><strong>3. Diagrams</strong>
                <ul>
                    <li>3.1 Platform Architecture</li>
                    <li>3.2 FHE Encryption Flow</li>
                    <li>3.3 Consortium Model</li>
                    <li>3.4 Commit-Reveal Voting</li>
                </ul>
            </li>
            <li><strong>4. Smart Contracts</strong></li>
            <li><strong>5. Security Model</strong></li>
        </ul>
    </div>
    """

def create_diagrams_section():
    """Create diagrams section with embedded SVGs."""
    diagrams = [
        ("01_platform_architecture.svg", "Platform Architecture", "Overview of the complete system architecture"),
        ("02_fhe_encryption_flow.svg", "FHE Encryption Flow", "How data is encrypted and processed homomorphically"),
        ("03_consortium_fraud_detection.svg", "Consortium Model", "Multi-bank collaboration for fraud detection"),
        ("04_commit_reveal_voting.svg", "Commit-Reveal Voting", "Privacy-preserving governance mechanism"),
    ]

    html = "<h1>Diagrams</h1>"

    for filename, title, description in diagrams:
        filepath = os.path.join(DIAGRAMS_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                svg_content = f.read()

            html += f"""
            <h2>{title}</h2>
            <p><em>{description}</em></p>
            <div class="diagram">
                {svg_content}
            </div>
            """

    return html

def generate_pdf():
    """Generate the complete PDF documentation."""
    print("📄 Generating PDF documentation...")

    # Build HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xcapit FHE-ML Platform - Documentation</title>
    </head>
    <body>
        {create_cover_page()}
        {create_toc()}
        {read_markdown_file('USE_CASES.md')}
        {read_markdown_file('TECHNICAL_ARCHITECTURE.md')}
        {create_diagrams_section()}
    </body>
    </html>
    """

    # Save HTML for debugging
    html_path = os.path.join(DOCS_DIR, "documentation.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"   ✅ HTML saved: {html_path}")

    # Generate PDF
    pdf_path = os.path.join(DOCS_DIR, "Xcapit_FHE-ML_Documentation.pdf")

    try:
        HTML(string=html_content, base_url=DOCS_DIR).write_pdf(
            pdf_path,
            stylesheets=[CSS(string=CSS_STYLES)]
        )
        print(f"   ✅ PDF saved: {pdf_path}")

        # Get file size
        size_mb = os.path.getsize(pdf_path) / (1024 * 1024)
        print(f"   📊 Size: {size_mb:.2f} MB")

        return pdf_path
    except Exception as e:
        print(f"   ❌ Error generating PDF: {e}")
        return None

if __name__ == "__main__":
    pdf_path = generate_pdf()
    if pdf_path:
        print(f"\n✅ Documentation generated successfully!")
        print(f"   Open: {pdf_path}")
