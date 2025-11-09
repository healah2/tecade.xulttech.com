import os
import tempfile
from django.shortcuts import render, redirect
from django.utils.html import escape
from .models import LearningGuide
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl
from bs4 import BeautifulSoup
import os, tempfile
from django.shortcuts import render, redirect
from django.utils.html import escape
from bs4 import BeautifulSoup
from .models import LearningGuide


def iter_block_items(parent):
    """Yield paragraphs and tables in order from a docx element."""
    if hasattr(parent, "element") and hasattr(parent.element, "body"):
        parent_elm = parent.element.body  # Document
    else:
        parent_elm = parent._tc  # Table cell
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def runs_to_html(paragraph):
    """Convert runs (bold/italic/underline) into inline HTML."""
    parts = []
    for run in paragraph.runs:
        text = escape(run.text)
        if not text:
            continue
        if run.bold:
            text = f"<strong>{text}</strong>"
        if run.italic:
            text = f"<em>{text}</em>"
        if run.underline:
            text = f"<u>{text}</u>"
        parts.append(text)
    return "".join(parts)


def get_span_attrs(cell):
    """Extract colspan / rowspan info from a table cell XML."""
    colspan = 1
    rowspan = 1

    # check for gridSpan (colspan)
    gridspan = cell._element.xpath(".//w:gridSpan")
    if gridspan:
        colspan = int(
            gridspan[0].get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
            )
        )

    # check for vMerge (rowspan)
    vmerge = cell._element.xpath(".//w:vMerge")
    if vmerge and vmerge[0].get(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
    ) != "restart":
        rowspan = 0  # continuation of previous cell
    elif vmerge:
        rowspan = 1  # start of a vertical merge

    return colspan, rowspan


def table_to_html(table):
    """Convert a docx Table into HTML <table> with merged cells preserved."""
    html = '<table class="custom-table" style="width:100%; border-collapse:collapse;">'
    for row in table.rows:
        html += "<tr>"
        for cell in row.cells:
            colspan, rowspan = get_span_attrs(cell)
            if rowspan == 0:  # skip continuation of vertical merge
                continue

            cell_html = ""
            for block in iter_block_items(cell):
                if isinstance(block, Paragraph):
                    text = runs_to_html(block)
                    if text.strip():
                        cell_html += f"<p>{text}</p>"
                elif isinstance(block, Table):
                    cell_html += table_to_html(block)

            span_attr = ""
            if colspan > 1:
                span_attr += f' colspan="{colspan}"'
            if rowspan > 1:
                span_attr += f' rowspan="{rowspan}"'

            html += f"<td{span_attr}>{cell_html}</td>"
        html += "</tr>"
    html += "</table>"
    return html


def docx_to_html(path, header_paragraphs=4):
    """Convert DOCX → HTML (paragraphs + tables), optionally wrap top paragraphs in a header div."""
    doc = Document(path)
    html = ""
    paragraph_count = 0
    header_html = ""
    
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = runs_to_html(block)
            if text.strip():
                paragraph_count += 1
                if paragraph_count <= header_paragraphs:
                    # accumulate header paragraphs
                    header_html += f"<p>{text}</p>\n"
                else:
                    html += f"<p>{text}</p>\n"
        elif isinstance(block, Table):
            html += table_to_html(block) + "\n"

    # Wrap header paragraphs in a div
    if header_html:
        header_html = f'<div class="doc-header">\n{header_html}</div>\n'

    # Combine header + rest
    return header_html + html



def clean_html_with_bs4(html_content):
    """Optional cleanup: remove duplicate table cell contents using BeautifulSoup."""
    soup = BeautifulSoup(html_content, "html.parser")

    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            seen = set()
            for cell in row.find_all(["td", "th"]):
                text = cell.get_text(strip=True)
                if text in seen:
                    cell.decompose()  # remove duplicate cell
                else:
                    seen.add(text)

    return str(soup)


from django.shortcuts import render
from django.utils.timezone import now
import json
import google.generativeai as genai

import json
import google.generativeai as genai
from django.shortcuts import render

def generate_learning_plan(request):
    GEMINI_API_KEY = "AIzaSyCgO3JupI-_EA1R4q5JGPTypvdFHfK9NBQ"
    genai.configure(api_key=GEMINI_API_KEY)

    def fetch_ai_session_details(title, expectations):
        joined_expectations = "; ".join(expectations)
        prompt = f"""
        Generate structured lesson plan details for a session with:
        Title: {title}
        Expectations: {joined_expectations}
        Return a valid JSON object with the keys:
        trainer_activities, trainee_activities, resources, assessments
        """

        def normalize(value):
            if isinstance(value, list):
                if all(isinstance(v, dict) for v in value):
                    return [f"{v.get('activity', '')}: {v.get('description', '')}" for v in value]
                return [str(v) for v in value]
            elif isinstance(value, str):
                return [value]
            return [str(value)]

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            content = response.text.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[len("json"):].strip()
            parsed = json.loads(content)
            return {
                "trainer_activities": normalize(parsed.get("trainer_activities", "")),
                "trainee_activities": normalize(parsed.get("trainee_activities", "")),
                "resources": normalize(parsed.get("resources", "")),
                "assessments": normalize(parsed.get("assessments", "")),
            }
        except Exception as e:
            print("Gemini API failed:", str(e))
            return {
                "trainer_activities": ["Guide learners through examples, supervise tasks."],
                "trainee_activities": ["Engage in group work, ask questions, practice hands-on tasks."],
                "resources": ["Computers, projector, whiteboard, course notes."],
                "assessments": ["Practical exercise, quiz, oral Q&A."]
            }

    if request.method == "POST":
        # -------------------------------
        # Collect metadata
        # -------------------------------
        unit_competence = request.POST.get("unit_competence", "").strip()
        unit_code = request.POST.get("unit_code", "").strip()
        trainer_name = request.POST.get("trainer_name", "").strip()
        course = request.POST.get("course", "").strip()
        institution = request.POST.get("institution", "").strip()
        level = request.POST.get("level", "").strip()
        date_preparation = request.POST.get("date_preparation", "").strip()
        date_revision = request.POST.get("date_revision", "").strip()
        term = request.POST.get("term", "").strip()
        trainees = request.POST.get("trainees", "").strip()
        class_name = request.POST.get("class_name", "").strip()

        try:
            total_time = int(request.POST.get("total_time", 0))
        except (TypeError, ValueError):
            total_time = 0

        # -------------------------------
        # Collect learning outcomes
        # -------------------------------
        outcomes = []
        idx = 0
        while True:
            title_key = f"outcomes[{idx}][title]"
            expect_key = f"outcomes[{idx}][expectations]"
            if title_key not in request.POST:
                break
            title = request.POST.get(title_key, "").strip()
            expectations_raw = request.POST.get(expect_key, "").strip()
            expectations = [e.strip() for e in expectations_raw.split(".") if e.strip()]
            if not expectations and expectations_raw:
                expectations = [expectations_raw]
            outcomes.append({
                "title": title or "Untitled Outcome",
                "expectations": expectations,
            })
            idx += 1

        # -------------------------------
        # Flatten expectations
        # -------------------------------
        flat_expectations = []
        for outcome in outcomes:
            for exp in outcome["expectations"]:
                flat_expectations.append({
                    "title": outcome["title"],
                    "expectation": exp
                })

        total_expectations = len(flat_expectations)

        # -------------------------------
        # Sessions config
        # -------------------------------
        HOURS_PER_SESSION = 2
        SESSIONS_PER_WEEK = 2
        ASSESSMENT_INTERVAL_WEEKS = 4  # assessment after every 4 weeks

        total_sessions = max(1, total_time // HOURS_PER_SESSION) if total_time > 0 else max(1, total_expectations)
        sessions_to_create = min(total_sessions, total_expectations) if total_expectations > 0 else total_sessions

        sessions = []

        # -------------------------------
        # Week 1: Reporting and Admission
        # -------------------------------
        sessions.append({
            "week": 1,
            "session_no": "",
            "title": "REPORTING AND ADMISSION",
            "trainer_activities": [],
            "trainee_activities": [],
            "resources": [],
            "assessments": [],
            "special": True
        })

        # -------------------------------
        # Generate normal sessions & insert assessment dynamically
        # -------------------------------
        if total_expectations > 0:
            base_count = total_expectations // sessions_to_create
            remainder = total_expectations % sessions_to_create
            ptr = 0
            current_week = 2  # start actual teaching from week 2

            # track outcome numbering
            outcome_seen = {}
            outcome_number = 0

            for s_idx in range(sessions_to_create):
                count = base_count + (1 if s_idx < remainder else 0)
                chunk = flat_expectations[ptr: ptr + count]
                ptr += count

                expectations_for_session = [c["expectation"] for c in chunk]
                outcome_title = chunk[0]["title"] if chunk else f"Outcome {s_idx+1}"

                # assign outcome number only first time we see it
                if outcome_title not in outcome_seen:
                    outcome_number += 1
                    outcome_seen[outcome_title] = outcome_number

                session_no = s_idx + 1
                ai_data = fetch_ai_session_details(outcome_title, expectations_for_session)

                sessions.append({
                    "week": current_week,
                    "session_no": session_no,
                    "title": f"Session {session_no}",
                    "learning_outcome": outcome_title,
                    "outcome_no": outcome_seen[outcome_title],  # ✅ numbered outcome
                    "expectations": expectations_for_session,
                    **ai_data,
                    "special": False
                })

                # Increment week normally
                if session_no % SESSIONS_PER_WEEK == 0:
                    current_week += 1

                # Insert assessment inline after interval
                if (current_week - 1) % ASSESSMENT_INTERVAL_WEEKS == 0 and (
                    session_no % SESSIONS_PER_WEEK == 0 or ptr == total_expectations
                ):
                    sessions.append({
                        "week": current_week,
                        "session_no": "",
                        "title": "ASSESSMENT",
                        "trainer_activities": [],
                        "trainee_activities": [],
                        "resources": [],
                        "assessments": [],
                        "special": True
                    })
                    current_week += 1  # skip a week after assessment

        # -------------------------------
        # Context for template
        # -------------------------------
        context = {
            "unit_competence": unit_competence,
            "unit_code": unit_code,
            "trainer_name": trainer_name,
            "course": course,
            "institution": institution,
            "level": level,
            "date_preparation": date_preparation,
            "date_revision": date_revision,
            "term": term,
            "trainees": trainees,
            "class_name": class_name,
            "total_time": total_time,
            "total_sessions": total_sessions,
            "sessions_created": len(sessions),
            "sessions": sessions,
        }

        return render(request, "trainer/learning_plan.html", context)

    return render(request, "trainer/generate_learning_plan.html")




from django.shortcuts import render, get_object_or_404
from .models import LearningGuide

def learning_guides_list(request):
    guides = LearningGuide.objects.all()
    return render(request, "trainer/learning_guides_list.html", {"guides": guides})

def view_learning_guide(request, pk):
    guide = get_object_or_404(LearningGuide, pk=pk)
    return render(request, "trainer/view_learning_guide.html", {"guide": guide})


