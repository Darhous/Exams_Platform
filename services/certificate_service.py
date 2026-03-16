from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime

CERT_DIR = Path("certificates")
CERT_DIR.mkdir(exist_ok=True)

def generate_certificate(student_name: str, percent: float, score: int, total: int) -> str:
    filename = CERT_DIR / f"certificate_{student_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    c = canvas.Canvas(str(filename), pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 4 * cm, "Digital Transformation Exam Platform")

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 6 * cm, "Certificate of Achievement")

    c.setFont("Helvetica", 14)
    c.drawCentredString(width / 2, height - 8 * cm, "This certificate is awarded to")

    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 10 * cm, student_name)

    c.setFont("Helvetica", 14)
    c.drawCentredString(
        width / 2,
        height - 12 * cm,
        f"For successfully passing the comprehensive exam with score {score}/{total} ({percent:.1f}%)"
    )

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 14 * cm, f"Date: {datetime.now().strftime('%Y-%m-%d')}")

    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(width / 2, 2.5 * cm, "designed by Ahmed Darhous")

    c.showPage()
    c.save()
    return str(filename)
