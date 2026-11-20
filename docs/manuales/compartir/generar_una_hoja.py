"""Exporta la guía de arranque manual en DEV a PDF y a texto seleccionable."""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate

OUTPUT = Path(__file__).resolve().parent
ROOT = OUTPUT.parents[2]
TITLE = "Garritas Store · Arranque manual en DEV"
ACCENT = colors.HexColor("#77264c")
FONTS = Path("/usr/share/fonts/truetype/dejavu")


def read_guide() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    clone = readme.split("## Clonar este repositorio\n", 1)[1].split("```powershell\n", 1)[1]
    clone = clone.split("```", 1)[0].rstrip()

    guide = (ROOT / "docs/ejecucion.md").read_text(encoding="utf-8")
    manual = guide.split("## Arranque manual en DEV con PowerShell\n", 1)[1]
    manual = manual.split("\n## Puertos de negocio DEV", 1)[0].strip()
    return (
        "### Preparación\n\n"
        "Si ya tienes el repositorio, utiliza esa misma carpeta. Las fotos y las bases locales "
        "se conservan en esa máquina. Si es una instalación nueva, clona el repositorio.\n\n"
        f"```powershell\n{clone}\n```\n\n{manual}"
    )


def inline_markup(line: str) -> str:
    line = escape(line)
    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
    return re.sub(r"`([^`]+)`", r'<font name="Code">\1</font>', line)


def page_footer(canvas, doc) -> None:
    canvas.setFillColor(ACCENT)
    canvas.setFont("Body", 8)
    canvas.drawString(38, 23, "Garritas Store · Guía de ejecución local")
    canvas.drawRightString(A4[0] - 38, 23, str(doc.page))


def main() -> None:
    for name, file in (
        ("Body", "DejaVuSans.ttf"),
        ("Bold", "DejaVuSans-Bold.ttf"),
        ("Code", "DejaVuSansMono.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Bold")

    title = ParagraphStyle(
        "title", fontName="Bold", fontSize=18, leading=23, textColor=ACCENT, spaceAfter=14
    )
    heading = ParagraphStyle(
        "heading", fontName="Bold", fontSize=11, leading=15, textColor=ACCENT,
        spaceBefore=10, spaceAfter=5, keepWithNext=True,
    )
    body = ParagraphStyle("body", fontName="Body", fontSize=9, leading=13, spaceAfter=6)
    code = ParagraphStyle(
        "code", fontName="Code", fontSize=7.8, leading=11, spaceAfter=7,
        leftIndent=7, backColor=colors.HexColor("#fff1f7"), borderPadding=5,
    )

    guide = read_guide()
    items = [Paragraph(TITLE, title)]
    parts = re.split(r"```powershell\n(.*?)\n```", guide, flags=re.S)
    for index, part in enumerate(parts):
        if index % 2:
            items.append(Preformatted(part, code))
            continue
        for line in filter(None, part.splitlines()):
            if line.startswith("### "):
                label = line[4:]
                if label.startswith(("3. Microservicios", "5. Grafana")):
                    items.append(PageBreak())
                items.append(Paragraph(inline_markup(label), heading))
            elif line.startswith("**") and line.endswith("**"):
                items.append(Paragraph(inline_markup(line[2:-2]), heading))
            else:
                items.append(Paragraph(inline_markup(line), body))

    pdf = OUTPUT / "Garritas-Store-inicio-una-hoja.pdf"
    doc = SimpleDocTemplate(
        str(pdf), pagesize=A4, leftMargin=38, rightMargin=38, topMargin=32,
        bottomMargin=38, title=TITLE, author="Garritas Store",
    )
    doc.build(items, onFirstPage=page_footer, onLaterPages=page_footer)

    plain = re.sub(r"^### |^```(?:powershell)?$|\*\*|`", "", guide, flags=re.M)
    (OUTPUT / "Garritas-Store-inicio-una-hoja.txt").write_text(f"{TITLE}\n\n{plain}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
