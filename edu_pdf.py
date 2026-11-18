import os, glob
from fpdf import FPDF

def build_pdf(pdf_path, subj, topic, n):
    class EduPDF(FPDF):
        def footer(self):
            self.set_y(-12)
            self.set_font(self._bf, "", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, "Aasma Shorts Study  |  Telegram: @aasma_shorts_study", align="C")

    pdf = EduPDF()
    pdf.set_compression(True)
    pdf.set_auto_page_break(True, margin=16)

    rob = glob.glob("/usr/share/fonts/**/NotoSans-Regular.ttf", recursive=True) + glob.glob("/system/fonts/*Roboto*Regular*.ttf")
    dev = glob.glob("/usr/share/fonts/**/NotoSansDevanagari-Regular.ttf", recursive=True) + glob.glob("/system/fonts/*Devanagari*Regular*.ttf")
    pdf._bf = "Helvetica"
    if rob:
        try: pdf.add_font("Base", "", rob[0]); pdf._bf = "Base"
        except Exception: pass
    if dev:
        try: pdf.add_font("Deva", "", dev[0]); pdf.set_fallback_fonts(["Deva"])
        except Exception: pass

    clean = lambda t: str(t) if dev else str(t).encode("latin-1", "ignore").decode("latin-1")
    bf = pdf._bf
    pdf.add_page()
    pdf.set_fill_color(30, 58, 138); pdf.rect(0, 0, 210, 30, "F")
    pdf.set_y(6); pdf.set_text_color(255, 255, 255); pdf.set_font(bf, "", 10)
    pdf.cell(0, 5, clean(f"AASMA SHORTS STUDY  |  {subj.upper()} GRAMMAR"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(bf, "", 14); pdf.multi_cell(0, 7, clean(topic), align="C"); pdf.set_y(35)

    def box(title, lines, fill_rgb):
        pdf.set_fill_color(*fill_rgb); pdf.set_text_color(15, 23, 42); pdf.set_font(bf, "", 11)
        pdf.set_x(pdf.l_margin); pdf.cell(pdf.epw, 7, clean(title), fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(bf, "", 10)
        for ln in lines: pdf.set_x(pdf.l_margin); pdf.multi_cell(pdf.epw, 6, clean(ln), fill=True)
        pdf.ln(3)

    box("1. Definition / Paribhasha:", [n.get("summary", "")], (239, 246, 255))
    box("2. Key Rules (Mukhya Niyam):", [f"- {r}" for r in n.get("rules", [])], (248, 250, 252))
    if n.get("trick"): box("3. Exam Trick / Shortcut:", [n["trick"]], (254, 243, 199))
    box("4. Solved Examples:", [f"- {e}" for e in n.get("examples", [])], (248, 250, 252))
    qs = n.get("quiz", [])
    ql, al = [], []
    for i, q in enumerate(qs, 1):
        ql += [f"Q{i}. {q['q']}", "   " + "   ".join(q["options"])]
        al.append(f"Q{i}: {q['ans']}")
    box("5. Practice Quiz:", ql, (245, 243, 255))
    box("6. Homework:", [f"- {h}" for h in n.get("homework", [])], (236, 253, 245))
    box("Answer Key:", ["  |  ".join(al)], (241, 245, 249))
    pdf.output(pdf_path)
