"""
Generate RAG_Agents_QA.pdf from docs/qa.md
Run: python3 generate_qa_pdf.py
"""

import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ── Colours ──────────────────────────────────────────────────────────────────
C_DARK_BLUE   = HexColor("#1B3A5C")   # chapter headers
C_MID_BLUE    = HexColor("#2563EB")   # question banners
C_LIGHT_BLUE  = HexColor("#EFF6FF")   # question banner bg
C_TEAL        = HexColor("#0D9488")   # follow-up banner
C_TEAL_BG     = HexColor("#F0FDFA")   # follow-up bg
C_ORANGE      = HexColor("#D97706")   # key term highlight
C_GREY_BG     = HexColor("#F8FAFC")   # body bg for answers
C_RULE        = HexColor("#CBD5E1")   # divider lines
C_CODE_BG     = HexColor("#F1F5F9")   # code block bg
C_CODE_TEXT   = HexColor("#1E293B")

PAGE_W, PAGE_H = A4
LEFT_M = RIGHT_M = 20 * mm
TOP_M  = BOTTOM_M = 20 * mm

# ── Doc setup ─────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    "RAG_Agents_QA.pdf",
    pagesize=A4,
    leftMargin=LEFT_M, rightMargin=RIGHT_M,
    topMargin=TOP_M,   bottomMargin=BOTTOM_M,
)

styles = getSampleStyleSheet()

_custom_styles = {}

def sty(name, parent="Normal", **kw):
    if isinstance(parent, str):
        parent_obj = _custom_styles.get(parent) or styles[parent]
    else:
        parent_obj = parent
    s = ParagraphStyle(name, parent=parent_obj, **kw)
    _custom_styles[name] = s
    return s

S_COVER_TITLE = sty("CoverTitle", fontSize=28, textColor=C_DARK_BLUE,
                     leading=34, spaceAfter=6, alignment=TA_CENTER, fontName="Helvetica-Bold")
S_COVER_SUB   = sty("CoverSub",   fontSize=14, textColor=C_MID_BLUE,
                     leading=18, spaceAfter=4, alignment=TA_CENTER)
S_COVER_META  = sty("CoverMeta",  fontSize=10, textColor=HexColor("#64748B"),
                     leading=14, alignment=TA_CENTER)

S_CHAPTER     = sty("Chapter", fontSize=16, textColor=white,
                     leading=22, spaceBefore=8, spaceAfter=6,
                     fontName="Helvetica-Bold", leftIndent=0)

S_Q_LABEL     = sty("QLabel", fontSize=12, textColor=C_MID_BLUE,
                     leading=16, fontName="Helvetica-Bold")
S_Q_TEXT      = sty("QText",  fontSize=12, textColor=C_DARK_BLUE,
                     leading=17, fontName="Helvetica-Bold", spaceAfter=4)

S_BODY        = sty("Body", fontSize=10, textColor=HexColor("#1E293B"),
                     leading=15, spaceAfter=3, alignment=TA_JUSTIFY)
S_BODY_INDENT = sty("BodyIndent", "Normal", leftIndent=12, spaceAfter=2,
                     fontSize=10, textColor=HexColor("#1E293B"), leading=15)

S_BULLET      = sty("Bullet", fontSize=10, textColor=HexColor("#1E293B"),
                     leading=14, leftIndent=16, firstLineIndent=-12, spaceAfter=2)

S_CODE        = sty("Code", fontSize=8.5, fontName="Courier",
                     textColor=C_CODE_TEXT, leading=12,
                     leftIndent=10, spaceAfter=2, backColor=C_CODE_BG)

S_FOLLOWUP_H  = sty("FUHead", fontSize=10, textColor=C_TEAL,
                     fontName="Helvetica-Bold", leading=14, spaceAfter=2)
S_FOLLOWUP    = sty("FU", fontSize=10, textColor=HexColor("#134E4A"),
                     leading=14, leftIndent=8, spaceAfter=2, alignment=TA_JUSTIFY)

S_TABLE_HEAD  = sty("TH", fontSize=9, textColor=white,
                     fontName="Helvetica-Bold", leading=12, alignment=TA_CENTER)
S_TABLE_CELL  = sty("TC", fontSize=9, textColor=HexColor("#1E293B"),
                     leading=12, alignment=TA_LEFT)

S_CHEAT_H     = sty("CheatH", fontSize=11, textColor=C_DARK_BLUE,
                     fontName="Helvetica-Bold", leading=15, spaceBefore=6, spaceAfter=2)
S_CHEAT_CODE  = sty("CheatCode", fontSize=8, fontName="Courier",
                     textColor=C_CODE_TEXT, leading=11, leftIndent=6, spaceAfter=1)

# ── Helpers ───────────────────────────────────────────────────────────────────
def chapter_banner(title):
    data = [[Paragraph(title, S_CHAPTER)]]
    t = Table(data, colWidths=[PAGE_W - LEFT_M - RIGHT_M])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), C_DARK_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("ROUNDEDCORNERS", [4]),
    ]))
    return t

def question_banner(q_num, q_text):
    inner = [
        [Paragraph(f"Q{q_num}", S_Q_LABEL),
         Paragraph(q_text, S_Q_TEXT)]
    ]
    t = Table(inner, colWidths=[30, PAGE_W - LEFT_M - RIGHT_M - 30])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_LIGHT_BLUE),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("LINEBELOW",     (0,0), (-1,-1), 1.5, C_MID_BLUE),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t

def followup_box(lines):
    content = [Paragraph("► Follow-up", S_FOLLOWUP_H)]
    for ln in lines:
        ln = ln.strip().lstrip(">").strip()
        if ln:
            content.append(Paragraph(ln, S_FOLLOWUP))
    inner = [[content]]
    t = Table([[inner]], colWidths=[PAGE_W - LEFT_M - RIGHT_M])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_TEAL_BG),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("RIGHTPADDING",  (0,0), (-1,-1), 10),
        ("LINERIGHT",     (0,0), (0,-1),  3, C_TEAL),
    ]))
    return t

def code_block(lines):
    content = []
    for ln in lines:
        content.append(Paragraph(ln.replace(" ", "&nbsp;"), S_CODE))
    inner = [content]
    t = Table([inner], colWidths=[PAGE_W - LEFT_M - RIGHT_M])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), C_CODE_BG),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("LINERIGHT",     (0,0), (0,-1),  3, C_RULE),
    ]))
    return t

def make_table(header, rows):
    col_n = len(header)
    col_w = (PAGE_W - LEFT_M - RIGHT_M) / col_n
    data = [[Paragraph(h, S_TABLE_HEAD) for h in header]]
    for row in rows:
        data.append([Paragraph(str(c), S_TABLE_CELL) for c in row])
    t = Table(data, colWidths=[col_w] * col_n, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  C_DARK_BLUE),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [white, C_GREY_BG]),
        ("GRID",          (0,0), (-1,-1), 0.5, C_RULE),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 5),
        ("RIGHTPADDING",  (0,0), (-1,-1), 5),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ])
    t.setStyle(ts)
    return t

def bold_inline(text):
    """Convert **text** and `code` to ReportLab markup."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.+?)\*',     r'<i>\1</i>', text)
    text = re.sub(r'`(.+?)`',       r'<font name="Courier" color="#B45309">\1</font>', text)
    return text

# ── Parse the markdown ────────────────────────────────────────────────────────
with open("docs/qa.md", "r") as f:
    raw = f.read()

lines = raw.split("\n")

story = []

# Cover page
story += [
    Spacer(1, 60*mm),
    Paragraph("RAG &amp; Agents", S_COVER_TITLE),
    Paragraph("Interview Q&amp;A", sty("CT2", "CoverTitle", fontSize=22, spaceAfter=12)),
    HRFlowable(width="60%", thickness=2, color=C_MID_BLUE, spaceAfter=12, hAlign="CENTER"),
    Paragraph("Retrieval-Augmented Generation · LLM Agents · Context Engineering", S_COVER_SUB),
    Spacer(1, 8*mm),
    Paragraph("25 Interview Questions · 9 Chapters · Quick Reference Cheat Sheet", S_COVER_META),
    PageBreak(),
]

i = 0
q_counter = 0
in_code = False
code_lines = []
in_followup = False
followup_lines = []
in_table = False
table_header = []
table_rows = []

def flush_code():
    global in_code, code_lines
    if code_lines:
        story.append(code_block(code_lines))
        story.append(Spacer(1, 3))
    in_code = False
    code_lines = []

def flush_followup():
    global in_followup, followup_lines
    if followup_lines:
        story.append(followup_box(followup_lines))
        story.append(Spacer(1, 4))
    in_followup = False
    followup_lines = []

def flush_table():
    global in_table, table_header, table_rows
    if table_header and table_rows:
        story.append(make_table(table_header, table_rows))
        story.append(Spacer(1, 4))
    in_table = False
    table_header = []
    table_rows = []

while i < len(lines):
    line = lines[i]

    # ── Code fence ──
    if line.strip().startswith("```"):
        if in_code:
            flush_code()
        else:
            if in_followup: flush_followup()
            if in_table:    flush_table()
            in_code = True
        i += 1
        continue

    if in_code:
        code_lines.append(line)
        i += 1
        continue

    # ── Follow-up blockquote ──
    if line.strip().startswith(">"):
        if not in_followup:
            if in_table: flush_table()
            in_followup = True
            followup_lines = []
        followup_lines.append(line)
        i += 1
        continue
    else:
        if in_followup:
            flush_followup()

    # ── Table ──
    if line.strip().startswith("|"):
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        # skip separator rows
        if all(re.match(r'^[-:]+$', p) for p in parts if p):
            i += 1
            continue
        if not in_table:
            in_table = True
            table_header = parts
            table_rows = []
        else:
            table_rows.append(parts)
        i += 1
        continue
    else:
        if in_table:
            flush_table()

    stripped = line.strip()

    # Skip horizontal rules and blank lines (handled by spacers)
    if stripped in ("---", "___", "***"):
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_RULE, spaceAfter=4))
        i += 1
        continue

    if stripped == "":
        story.append(Spacer(1, 3))
        i += 1
        continue

    # ── Chapter heading ──
    if stripped.startswith("## Chapter") or stripped.startswith("## Quick Reference"):
        title = stripped.lstrip("#").strip()
        story.append(Spacer(1, 6))
        story.append(chapter_banner(title))
        story.append(Spacer(1, 6))
        i += 1
        continue

    # ── H1 title (skip, used for cover only) ──
    if stripped.startswith("# "):
        i += 1
        continue

    # ── H2 generic ──
    if stripped.startswith("## "):
        title = stripped[3:].strip()
        story.append(Spacer(1, 6))
        story.append(chapter_banner(title))
        story.append(Spacer(1, 6))
        i += 1
        continue

    # ── H3 (sub-heading inside cheat sheet) ──
    if stripped.startswith("### "):
        title = stripped[4:].strip()
        story.append(Paragraph(title, S_CHEAT_H))
        i += 1
        continue

    # ── Question ──
    m = re.match(r'\*\*Q(\d+)\.\s+(.+?)\*\*', stripped)
    if m:
        q_num  = m.group(1)
        q_text = m.group(2)
        story.append(Spacer(1, 5))
        story.append(question_banner(q_num, q_text))
        story.append(Spacer(1, 4))
        i += 1
        continue

    # ── Bullet list ──
    if stripped.startswith("- ") or stripped.startswith("* "):
        text = bold_inline(stripped[2:].strip())
        story.append(Paragraph(f"• {text}", S_BULLET))
        i += 1
        continue

    # ── Numbered list ──
    m = re.match(r'^(\d+)\.\s+(.*)', stripped)
    if m:
        num  = m.group(1)
        text = bold_inline(m.group(2))
        story.append(Paragraph(f"{num}. {text}", S_BULLET))
        i += 1
        continue

    # ── Regular paragraph ──
    text = bold_inline(stripped)
    story.append(Paragraph(text, S_BODY))
    i += 1

# Flush any open states
flush_code()
flush_followup()
flush_table()

# Build
doc.build(story)
print("✓ RAG_Agents_QA.pdf generated")
