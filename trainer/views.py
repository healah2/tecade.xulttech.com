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
from django.shortcuts import render
from django.utils.timezone import now
import json
import google.generativeai as genai
from django.shortcuts import render, get_object_or_404



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

        # Week 1: Reporting and Admission
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

        # Generate normal sessions & insert assessment dynamically
        if total_expectations > 0:
            base_count = total_expectations // sessions_to_create
            remainder = total_expectations % sessions_to_create
            ptr = 0
            current_week = 2
            outcome_seen = {}
            outcome_number = 0

            for s_idx in range(sessions_to_create):
                count = base_count + (1 if s_idx < remainder else 0)
                chunk = flat_expectations[ptr: ptr + count]
                ptr += count

                expectations_for_session = [c["expectation"] for c in chunk]
                outcome_title = chunk[0]["title"] if chunk else f"Outcome {s_idx+1}"

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
                    "outcome_no": outcome_seen[outcome_title],
                    "expectations": expectations_for_session,
                    **ai_data,
                    "special": False
                })

                if session_no % SESSIONS_PER_WEEK == 0:
                    current_week += 1

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
                    current_week += 1

        # -------------------------------
        # Save generated guide in DB
        # -------------------------------
        guide = LearningGuide.objects.create(
            unit_code=unit_code,
            unit_competence=unit_competence,
            trainer_name=trainer_name,
            course=course,
            institution=institution,
            level=level,
            date_preparation=date_preparation or None,
            date_revision=date_revision or None,
            term=term,
            trainees=trainees,
            class_name=class_name,
            total_time=total_time,
            sessions_json=sessions
        )

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
            "guide_saved": True  # Flag to auto-display success
        }

        return render(request, "trainer/learning_plan.html", context)

    return render(request, "trainer/generate_learning_plan.html")








def learning_guides_list(request):
    guides = LearningGuide.objects.all()
    return render(request, "trainer/learning_guides_list.html", {"guides": guides})

import json
from django.shortcuts import render, get_object_or_404
from .models import LearningGuide

import ast
from django.shortcuts import get_object_or_404, render

def view_learning_guide(request, pk):
    guide = get_object_or_404(LearningGuide, pk=pk)

    # Convert string representation of list to Python list
    if guide.sessions_json:
        try:
            sessions = ast.literal_eval(guide.sessions_json)
        except Exception as e:
            sessions = []
            print("Error parsing sessions_json:", e)
    else:
        sessions = []

    return render(request, "trainer/view_learning_plan.html", {
        "guide": guide,
        "sessions": sessions
    })

import ast
import json
from django.shortcuts import get_object_or_404, render, redirect
from .models import LearningGuide, SavedSessionPlan

def generate_session_plan(request):
    guides = LearningGuide.objects.all()

    # Prepare units dropdown
    units = []
    for guide in guides:
        if guide.unit_competence:
            try:
                sessions = ast.literal_eval(guide.sessions_json or "[]")
            except Exception as e:
                print("Error parsing sessions_json for guide", guide.id, e)
                sessions = []

            units.append({
                'id': guide.id,
                'unit_competence': guide.unit_competence,
                'sessions': sessions
            })

    # Selected guide for AJAX reload
    selected_guide_id = request.GET.get('unit_id')
    selected_sessions = []

    if selected_guide_id:
        guide = get_object_or_404(LearningGuide, id=selected_guide_id)

        try:
            sessions = ast.literal_eval(guide.sessions_json or "[]")
        except Exception as e:
            print("Error parsing sessions_json:", e)
            sessions = []

        for s in sessions:
            if not s.get('special', False):
                selected_sessions.append({
                    'title': s.get('title', ''),
                    'expectations': json.dumps(s.get('expectations', [])),  # <-- JSON encode
                    'trainer_activities': s.get('trainer_activities', []),
                    'trainee_activities': s.get('trainee_activities', []),
                    'resources': s.get('resources', [])
                })

    # ----------------------------------------------------------
    # SAVE SESSION PLAN
    # ----------------------------------------------------------
    if request.method == 'POST':
        guide_id = request.POST.get('unit_id')
        session_title = request.POST.get('session_title')
        presenter_name = request.POST.get('presenter_name')
        date = request.POST.get('date')
        duration = request.POST.get('duration')
        bridge_in = request.POST.get('bridge_in')
        pre_assessment = request.POST.get('pre_assessment')
        post_assessment = request.POST.get('post_assessment')
        summary = request.POST.get('summary')
        time = request.POST.getlist('time[]')

        # MULTIPLE EXPECTATIONS
        expectations = request.POST.getlist('expectation[]')
        expectation_str = "\n".join([e.strip() for e in expectations if e.strip()])

        # Activity Lists
        trainer_activities = request.POST.getlist('trainer_activities[]')
        trainee_activities = request.POST.getlist('trainee_activities[]')
        resources = request.POST.getlist('resources[]')

        # Clean strings
        trainer_str = '\n'.join([t.strip() for t in trainer_activities if t.strip()])
        trainee_str = '\n'.join([t.strip() for t in trainee_activities if t.strip()])
        resources_str = '\n'.join([r.strip() for r in resources if r.strip()])
        time_str = '\n'.join([ti.strip() for ti in time if ti.strip()])

        guide = get_object_or_404(LearningGuide, id=guide_id)

        SavedSessionPlan.objects.create(
            unit=guide,
            session_title=session_title,
            presenter_name=presenter_name,
            date=date,
            duration=duration,
            bridge_in=bridge_in,
            pre_assessment=pre_assessment,
            post_assessment=post_assessment,
            summary=summary,
            expectation=expectation_str,
            time=time_str,
            trainer_activities=trainer_str,
            trainee_activities=trainee_str,
            resources=resources_str
        )

        return redirect("session_plans_list")

    return render(request, 'trainer/generate_session_plan.html', {
        'guides': guides,
        'units': units,
        'selected_sessions': selected_sessions,
        'selected_guide_id': selected_guide_id
    })



def session_plans_list(request):
    plans = SavedSessionPlan.objects.select_related('unit').all().order_by('-date')
    return render(request, 'trainer/session_plans_list.html', {'plans': plans})


def view_session_plan(request, plan_id):
    plan = get_object_or_404(SavedSessionPlan, id=plan_id)

    trainer_activities = plan.trainer_activities.splitlines() if plan.trainer_activities else []
    trainee_activities = plan.trainee_activities.splitlines() if plan.trainee_activities else []
    resources = plan.resources.splitlines() if plan.resources else []
    time = plan.time.splitlines() if plan.time else []

    # Split expectations too (NEW)
    expectations = plan.expectation.splitlines() if plan.expectation else []

    participatory_rows = list(zip(time, trainer_activities, trainee_activities, resources))

    return render(request, 'trainer/view_session_plan.html', {
        'plan': plan,
        'participatory_rows': participatory_rows,
        'expectations': expectations
    })



def sp(request):
    return render(request, 'trainer/sp.html')


def session_plan(request, session_no):
    # For simplicity, assume one guide; otherwise filter by course/unit/etc.
    guide = get_object_or_404(LearningGuide, pk=1)  

    # Parse sessions JSON
    sessions = guide.sessions  # uses the property you defined

    # Find the specific session by session_no
    session = next((s for s in sessions if s.get('session_no') == session_no), None)

    if not session:
        return render(request, 'session_not_found.html', {'session_no': session_no})

    return render(request, 'session_plan.html', {'session': session})




