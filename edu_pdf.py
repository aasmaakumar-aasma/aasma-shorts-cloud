import os
from fpdf import FPDF

FONT_PATHS = [
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
]

def find_font():
    for p in FONT_PATHS:
        if os.path.exists(p):
            return p
    return None

def make_edu_pdf(data, out_path="notes.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    try:
        pdf.set_text_shaping(True)
    except Exception:
        pass

    font_file = find_font()
    if font_file:
        pdf.add_font("Noto", "", font_file)
        pdf.add_font("Noto", "B", font_file)
        fn = "Noto"
    else:
        fn = "Helvetica"

    # Header Banner
    pdf.set_fill_color(24, 54, 128)
    pdf.rect(0, 0, 210, 28, "F")
    pdf.set_xy(10, 6)
    pdf.set_font(fn, "B", 10)
    pdf.set_text_color(200, 220, 255)
    pdf.cell(190, 6, f"AASMA SHORTS STUDY  |  {data.get('subject', 'Notes').upper()}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fn, "B", 15)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(190, 10, data.get("title", "Study Notes"), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_y(34)
    pdf.set_text_color(30, 30, 30)

    def section(heading, body_lines, bg=(245, 248, 255)):
        pdf.set_x(pdf.l_margin)
        pdf.set_fill_color(*bg)
        pdf.set_font(fn, "B", 12)
        pdf.set_text_color(20, 50, 110)
        pdf.cell(pdf.epw, 8, f"  {heading}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        pdf.set_font(fn, "", 11)
        pdf.set_text_color(35, 35, 35)
        for line in body_lines:
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pdf.epw - 6, 7, str(line))
            pdf.ln(1)
        pdf.ln(3)

    section("1. Definition / Paribhasha", [data.get("definition", "")], (238, 245, 255))
    section("2. Key Rules (Mukhya Niyam)", [f"- {r}" for r in data.get("rules", [])], (244, 249, 244))
    section("3. Exam Trick / Shortcut", [data.get("trick", "")], (255, 250, 232))
    section("4. Solved Examples", [f"- {e}" for e in data.get("examples", [])], (245, 245, 252))

    quiz_lines = []
    for i, q in enumerate(data.get("quiz", []), 1):
        quiz_lines.append(f"Q{i}. {q.get('q', '')}")
        opts = q.get("options", [])
        quiz_lines.append("    " + "   |   ".join([f"{chr(65+j)}) {o}" for j, o in enumerate(opts)]))
    section("5. Practice Quiz (10 Questions)", quiz_lines, (245, 242, 255))

    hw = data.get("homework", [])
    if hw:
        section("6. Homework", [f"- {h}" for h in hw], (240, 252, 245))

    ans = "  |  ".join([f"Q{i}: {q.get('ans', 'A')}" for i, q in enumerate(data.get("quiz", []), 1)])
    section("Answer Key", [ans], (242, 242, 242))

    pdf.set_y(-15)
    pdf.set_font(fn, "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(pdf.epw, 8, "Aasma Shorts Study  |  Telegram: @aasma_shorts_study", align="C")
    pdf.output(out_path)
    return out_path


def build_pdf(*args, **kwargs):
    data = {}
    out_path = kwargs.get("out_path", "notes.pdf")
    for a in args:
        if isinstance(a, dict):
            data = a
        elif isinstance(a, str) and a.endswith(".pdf"):
            out_path = a
    return make_edu_pdf(data, out_path)
