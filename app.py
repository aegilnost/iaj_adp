
import os
import io
import json
import datetime as dt
from typing import Any, Dict, List

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

try:
    import docx
except Exception:
    docx = None

APP_NAME = "Write and Come Back"
APP_VERSION = "v0.10.0"

QUICK_STEPS = [
    "Welcome",
    "Read My Materials",
    "Choose the Main Legal Point",
    "Add to Your Paper",
    "Start Writing Package",
    "Review & Export",
]

DEEP_STEPS = [
    "Strengthen Support",
    "Tighten the Argument",
    "Improve the Writing Pack",
]

TIME_EST = {
    "quick_0": "1–2 min",
    "quick_1": "3–6 min",
    "quick_2": "4–7 min",
    "quick_3": "3–6 min",
    "quick_4": "2–4 min",
    "quick_5": "2–3 min",
    "deep_0": "4–8 min",
    "deep_1": "4–8 min",
    "deep_2": "3–6 min",
}

LAW_SUGGESTIONS = {
    "data privacy act": ("Republic Act No. 10173 (Data Privacy Act of 2012)", "https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/"),
    "constitution": ("1987 Constitution of the Republic of the Philippines", "https://www.officialgazette.gov.ph/constitutions/1987-constitution/"),
    "anti-money laundering act": ("Republic Act No. 9160 (Anti-Money Laundering Act of 2001)", "https://lawphil.net/statutes/repacts/ra2001/ra_9160_2001.html"),
    "amla": ("Republic Act No. 9160 (Anti-Money Laundering Act of 2001)", "https://lawphil.net/statutes/repacts/ra2001/ra_9160_2001.html"),
    "bank secrecy": ("Republic Act No. 1405 (Law on Secrecy of Bank Deposits)", "https://lawphil.net/statutes/repacts/ra1955/ra_1405_1955.html"),
}

def init_state():
    if "project" not in st.session_state:
        st.session_state.project = {
            "version": APP_VERSION,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "phase": "quick",  # quick or deep
            "step": 0,
            "answers": {},
            "outputs": {},
            "flags": [],
            "feedback": {},
            "api_log": [],
            "ran_steps": [],
        }

def touch():
    st.session_state.project["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")

def ans(key, default=None):
    return st.session_state.project["answers"].get(key, default)

def set_ans(key, value):
    st.session_state.project["answers"][key] = value
    touch()

def set_out(key, value):
    st.session_state.project["outputs"][key] = value
    touch()

def add_flag(text):
    if text and text not in st.session_state.project["flags"]:
        st.session_state.project["flags"].append(text)
        touch()

def get_openai_client():
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)

def call_model_json(stage: str, system_prompt: str, user_prompt: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    client = get_openai_client()
    if client is None:
        st.session_state.project["api_log"].append({"stage": stage, "mode": "mock", "time": dt.datetime.now().isoformat(timespec="seconds")})
        return fallback
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        st.session_state.project["api_log"].append({"stage": stage, "mode": "openai", "time": dt.datetime.now().isoformat(timespec="seconds")})
        return data
    except Exception as e:
        st.warning(f"Model call failed at {stage}. Using fallback.")
        st.session_state.project["api_log"].append({"stage": stage, "mode": "fallback", "error": str(e), "time": dt.datetime.now().isoformat(timespec="seconds")})
        return fallback

def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    if name.endswith((".txt", ".md")):
        return raw.decode("utf-8", errors="ignore")
    if name.endswith(".docx") and docx is not None:
        d = docx.Document(io.BytesIO(raw))
        return "\n".join(p.text for p in d.paragraphs if p.text.strip())
    if name.endswith(".pdf") and PdfReader is not None:
        reader = PdfReader(io.BytesIO(raw))
        parts = []
        for page in reader.pages[:30]:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    return ""

def suggest_laws(query: str):
    q = (query or "").strip().lower()
    if not q:
        return []
    out = []
    for k, v in LAW_SUGGESTIONS.items():
        if q in k or k in q:
            out.append({"title": v[0], "link": v[1]})
    return out[:5]

def quote_box(title: str, body: str):
    st.markdown(f"""
    <div style="background:#f7f9fc;border:1px solid #dce3ee;border-radius:12px;padding:12px 14px;margin-bottom:12px">
      <div style="font-size:0.84rem;color:#445; font-weight:700; margin-bottom:6px">{title}</div>
      <div style="font-size:0.95rem;color:#222">{body}</div>
    </div>
    """, unsafe_allow_html=True)

def progress():
    phase = st.session_state.project["phase"]
    step = st.session_state.project["step"]
    steps = QUICK_STEPS if phase == "quick" else DEEP_STEPS
    total = len(steps)
    pct = int((step + 1) / total * 100)
    st.markdown("""
    <style>
    .stepcard{border:1px solid #dce3ee;border-radius:14px;background:#f8fbff;padding:10px;min-height:76px}
    .stepcard.active{background:#173b7a;color:white;border-color:#173b7a}
    .stepcard.done{background:#eef5ff}
    .flag{display:inline-block;background:#fff3cd;border:1px solid #ffe08a;color:#7a5b00;border-radius:999px;padding:4px 10px;font-size:.82rem;margin:3px 6px 0 0}
    .req{display:inline-block;border-radius:999px;padding:3px 9px;font-size:.75rem;background:#eef5ff;color:#173b7a;margin-right:6px}
    .opt{display:inline-block;border-radius:999px;padding:3px 9px;font-size:.75rem;background:#f5f5f5;color:#666;margin-right:6px}
    </style>
    """, unsafe_allow_html=True)
    st.write(f"**{APP_NAME}** · {APP_VERSION} · {'Quick Pass' if phase == 'quick' else 'Deep Pass'}")
    st.progress(pct / 100)
    cols = st.columns(total)
    for i, name in enumerate(steps):
        cls = "stepcard active" if i == step else ("stepcard done" if i < step else "stepcard")
        key = f"{phase}_{i}"
        cols[i].markdown(
            f'<div class="{cls}"><div style="font-size:.73rem;font-weight:700">STEP {i+1}</div><div style="font-size:.88rem;font-weight:600;line-height:1.2;margin-top:6px">{name}</div><div style="font-size:.74rem;opacity:.85;margin-top:6px">{TIME_EST.get(key,"")}</div></div>',
            unsafe_allow_html=True,
        )

def feedback_sidebar():
    phase = st.session_state.project["phase"]
    step = st.session_state.project["step"]
    name = (QUICK_STEPS if phase == "quick" else DEEP_STEPS)[step]
    label = f"{phase.title()} — {name}"
    fb = st.session_state.project["feedback"].setdefault(label, {})
    st.sidebar.markdown("## Notes for the next version")
    fb["worked"] = st.sidebar.text_area("What worked", value=fb.get("worked",""), key=f"worked_{label}")
    fb["confusing"] = st.sidebar.text_area("What was confusing", value=fb.get("confusing",""), key=f"conf_{label}")
    fb["too_much"] = st.sidebar.text_area("What felt too much", value=fb.get("too_much",""), key=f"too_{label}")
    fb["missing"] = st.sidebar.text_area("What is missing", value=fb.get("missing",""), key=f"miss_{label}")
    fb["notes"] = st.sidebar.text_area("Other notes", value=fb.get("notes",""), key=f"notes_{label}")
    touch()

def make_machine_export():
    return json.dumps(st.session_state.project, indent=2, ensure_ascii=False)

def make_human_export():
    d = docx.Document() if docx is not None else None
    if d is None:
        return make_machine_export().encode("utf-8")
    p = st.session_state.project
    d.add_heading(f"{APP_NAME} — Pre-Writing Kit", 0)
    d.add_paragraph(f"Version: {p['version']}")
    d.add_paragraph(f"Created: {p['created_at']}")
    d.add_paragraph(f"Updated: {p['updated_at']}")
    d.add_heading("Quick Pass", level=1)
    for key in ["materials_materials_summary", "selected_legal_point", "starter_starter_summary", "deepen_strengthened_summary"]:
        val = p["answers"].get(key)
        if val:
            d.add_paragraph(str(val))
    if p["answers"].get("starter_outline"):
        d.add_heading("Outline", level=2)
        for item in p["answers"]["starter_outline"]:
            d.add_paragraph(str(item), style="List Number")
    wp = p["answers"].get("writing_package")
    if wp:
        d.add_heading("Writing Package", level=2)
        d.add_paragraph(wp.get("abstract_seed",""))
        for item in wp.get("opening_options", []):
            d.add_paragraph(str(item), style="List Bullet")
    if p["answers"].get("deep_support_summary") or p["answers"].get("deep_argument_summary") or p["answers"].get("deep_writing_summary"):
        d.add_heading("Deep Pass", level=1)
        for key in ["deep_support_summary", "deep_argument_summary", "deep_writing_summary"]:
            val = p["answers"].get(key)
            if val:
                d.add_paragraph(str(val))
    if p.get("flags"):
        d.add_heading("Carry-forward Flags", level=1)
        for f in p["flags"]:
            d.add_paragraph(str(f), style="List Bullet")
    d.add_heading("What to do next", level=1)
    d.add_paragraph("1. Read this kit once without editing.")
    d.add_paragraph("2. Draft one section in your own words.")
    d.add_paragraph("3. Return to Deep Pass only if you need stronger support, a tighter argument, or a better writing pack.")
    bio = io.BytesIO()
    d.save(bio)
    bio.seek(0)
    return bio.getvalue()

def downstream_warning(changed_from_quick: int):
    st.warning("You may revisit an earlier quick-pass step. But if you change a response and run the model again, later outputs will be affected and should be rebuilt from that step forward.")
    if st.button("Clear downstream outputs from this step"):
        step_keys = {
            1: ["materials_materials_summary","materials_keywords","materials_legal_arguments","materials_authorities_mentioned","materials_possible_directions","materials_quotes"],
            2: ["selected_legal_point","main_point","main_emphasis","starter_starter_summary","starter_outline","starter_support_map","starter_missing_source_flags","starter_abstract_seed"],
            3: ["scope_in","scope_out","support_gap","weakness","deepen_strengthened_summary","deepen_refined_outline","deepen_new_flags"],
            4: ["writing_package", "deep_support_summary", "deep_argument_summary", "deep_writing_summary"],
        }
        for idx, ks in step_keys.items():
            if idx >= changed_from_quick:
                for k in ks:
                    st.session_state.project["answers"].pop(k, None)
                    st.session_state.project["outputs"].pop(k, None)
        st.session_state.project["flags"] = []
        st.success("Later outputs were cleared. Re-run from this step.")
        touch()
        st.rerun()

st.set_page_config(page_title=APP_NAME, layout="wide")
init_state()
progress()

with st.sidebar:
    st.markdown(f"### {APP_NAME}")
    st.caption(f"{APP_VERSION} · {'OpenAI connected' if get_openai_client() else 'Mock mode'}")
    st.write("Built for busy lecturers: write first, improve later.")
    st.divider()
    feedback_sidebar()
    st.divider()
    st.download_button("Export machine-readable file (.json)", data=make_machine_export(), file_name=f"checkpoint_{APP_VERSION}.json", mime="application/json", use_container_width=True)
    st.download_button("Export human-readable pre-writing kit (.docx)", data=make_human_export(), file_name=f"pre_writing_kit_{APP_VERSION}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    uploaded_cp = st.file_uploader("Load saved checkpoint", type=["json"], key="load_cp")
    if uploaded_cp and st.button("Load this checkpoint", use_container_width=True):
        st.session_state.project = json.load(uploaded_cp)
        st.success("Checkpoint loaded.")
        st.rerun()

phase = st.session_state.project["phase"]
step = st.session_state.project["step"]

# QUICK PASS
if phase == "quick":
    if step == 0:
        st.markdown("## Step 1 — Welcome")
        quote_box("What this platform does", "It reads your lecture materials, pulls out the strongest legal point it can find, and gets you to a first article package quickly. Deep Pass comes only after Quick Pass is done.")
        quote_box("What to expect", "Quick Pass comes first. The goal is movement, not perfection. After you finish Quick Pass, you can continue to Deep Pass to strengthen support, tighten the argument, and improve the writing package.")
        st.markdown("### Before you begin")
        st.markdown('<span class="req">Required</span> Start the quick pass.', unsafe_allow_html=True)
        st.caption("Indicative time for the whole quick pass: about 15–25 minutes, depending on your materials.")
        st.info("Robustness note: model-assisted results may vary slightly across runs. The goal is a workable starting point every time, then a stronger second pass if needed.")
        if st.button("Start Quick Pass", type="primary"):
            st.session_state.project["step"] = 1
            touch()
            st.rerun()

    elif step == 1:
        st.markdown("## Step 2 — Read My Materials")
        downstream_warning(1)
        quote_box("What to do here", "This step should ideally already be pre-loaded by your team with the lecture transcript and slide deck. You may still add optional materials here. The platform will read the materials first and extract legal arguments, not just any argument.")
        st.markdown(f'<span class="req">Required</span> Upload or confirm lecture materials. <span class="opt">Time: {TIME_EST["quick_1"]}</span>', unsafe_allow_html=True)
        preloaded_note = st.text_input("What has already been pre-loaded by the team? (Optional)", value=ans("preloaded_note",""))
        materials = st.file_uploader("Upload transcript, slides, notes, and optional bionote/CV", type=["pdf","docx","txt","md"], accept_multiple_files=True)
        st.markdown("**Optional.** Bionote or CV context")
        speaker_note = st.text_area("Bionote or CV note", value=ans("speaker_note",""), height=100)
        st.markdown("**Optional.** Mention a law, case, or rule only if you already have one in mind.")
        legal_text = st.text_input("Law, case, or rule to search (optional)", value="")
        suggestions = suggest_laws(legal_text)
        selected_laws = ans("selected_laws", [])
        if suggestions:
            for s in suggestions:
                if st.checkbox(f"{s['title']} — {s['link']}", key=f"law_{s['title']}"):
                    if s["title"] not in selected_laws:
                        selected_laws.append(s["title"])
        if st.button("Read the materials", type="primary"):
            set_ans("preloaded_note", preloaded_note)
            set_ans("speaker_note", speaker_note)
            set_ans("selected_laws", selected_laws)
            filenames, texts = [], []
            if materials:
                for f in materials:
                    filenames.append(f.name)
                    texts.append(f"\n\n### FILE: {f.name}\n{extract_text(f)[:30000]}")
            set_ans("uploaded_files", filenames)
            fallback = {
                "materials_summary": "The materials suggest one or more legal issues that can be turned into an article. The next step is to choose the strongest legal point to start from.",
                "keywords": ["legal point", "doctrine", "rule", "case law"],
                "legal_arguments": [
                    "A legal argument appears to arise from how a rule, doctrine, or statutory requirement is being interpreted or applied.",
                    "A second legal argument appears to arise from the legal consequence that follows from that interpretation.",
                    "A third legal argument may involve institutional or enforcement implications of the lecture's main issue.",
                ],
                "authorities_mentioned": selected_laws,
                "possible_directions": [
                    "Clarify the legal rule at the center of the lecture.",
                    "Show that the current doctrinal treatment is incomplete or unclear.",
                    "Explain the legal consequence that should follow from the doctrine or rule discussed.",
                ],
                "quotes": [],
            }
            system = """
Read the lecture materials and extract legal arguments, not just any argument.
Return JSON with:
materials_summary
keywords
legal_arguments (3 only, strongest first)
authorities_mentioned
possible_directions
quotes (up to 3 short quote objects with text and source label)
Use the lecture's language where possible.
"""
            user = f"""Preloaded note: {preloaded_note}
Speaker note: {speaker_note}
Selected laws: {selected_laws}
Files: {filenames}
MATERIALS:
{"".join(texts)[:80000]}
"""
            with st.spinner("Reading materials..."):
                data = call_model_json("read_materials", system, user, fallback)
            set_ans("materials_materials_summary", data.get("materials_summary"))
            set_ans("materials_keywords", data.get("keywords", []))
            set_ans("materials_legal_arguments", data.get("legal_arguments", []))
            set_ans("materials_authorities_mentioned", data.get("authorities_mentioned", []))
            set_ans("materials_possible_directions", data.get("possible_directions", []))
            set_ans("materials_quotes", data.get("quotes", []))
            st.session_state.project["step"] = 2
            touch()
            st.rerun()
        if ans("materials_materials_summary"):
            st.markdown("### What the app found in your materials")
            st.write(ans("materials_materials_summary"))
            st.write("**Top legal points, in decreasing order**")
            for i, item in enumerate(ans("materials_legal_arguments", []), 1):
                st.markdown(f"{i}. {item}")

    elif step == 2:
        st.markdown("## Step 3 — Choose the Main Legal Point")
        downstream_warning(2)
        quote_box("What to do here", "Choose the legal point that is closest to the title and the main points raised in the lecture. This legal point will be the starting point of your paper, which you can revise eventually.")
        st.markdown(f'<span class="req">Required</span> Pick one legal point and confirm it in your own words. <span class="opt">Time: {TIME_EST["quick_2"]}</span>', unsafe_allow_html=True)
        pts = ans("materials_legal_arguments", [])
        options = [""] + [f"{i}. {p}" for i, p in enumerate(pts, 1)] + ["Something else"]
        selected = st.radio("Choose the legal point closest to your lecture", options=options, index=0)
        main_point = st.text_area("State the legal point you want to begin with", value=ans("main_point",""), height=120)
        if st.button("Confirm legal point and build the article starter", type="primary"):
            set_ans("selected_legal_point", selected)
            set_ans("main_point", main_point)
            fallback = {
                "main_point_cleaned": main_point or selected,
                "working_question": "What legal question should the paper answer based on this starting point?",
                "working_title": "A Legal Issue Emerging from the Lecture",
                "reason_for_choice": "This starting point is close enough to the lecture to support a first article version.",
                "starter_summary": "This paper begins from a legal point surfaced in the lecture and turns it into a workable article focus.",
                "starter_outline": [
                    "Introduction and legal problem",
                    "Rule, doctrine, or legal framework",
                    "Main legal tension",
                    "Why the current treatment is insufficient or contested",
                    "Proposed resolution or clarified position",
                    "Conclusion",
                ],
                "starter_support_map": {
                    "supports_main_point": ans("materials_authorities_mentioned", []),
                    "related_but_not_yet_enough": [],
                    "may_be_missing_but_not_blocking": [],
                },
                "starter_missing_source_flags": [],
                "starter_abstract_seed": "This article examines a legal issue surfaced in the lecture and argues for a clearer doctrinal treatment.",
            }
            system = """
Given the selected legal point, return JSON with:
main_point_cleaned
working_question
working_title
reason_for_choice
starter_summary
starter_outline
starter_support_map
starter_missing_source_flags
starter_abstract_seed
Keep it practical. This is still a write-first stage.
"""
            user = f"""Legal arguments: {pts}
Selected legal point: {selected}
Writer's own statement: {main_point}
Authorities already visible: {ans('materials_authorities_mentioned',[])}
"""
            with st.spinner("Building from the legal point..."):
                data = call_model_json("choose_legal_point_plus_starter", system, user, fallback)
            set_out("main_point_result", {
                "main_point_cleaned": data.get("main_point_cleaned"),
                "working_question": data.get("working_question"),
                "working_title": data.get("working_title"),
                "reason_for_choice": data.get("reason_for_choice"),
            })
            set_ans("starter_starter_summary", data.get("starter_summary"))
            set_ans("starter_outline", data.get("starter_outline"))
            set_ans("starter_support_map", data.get("starter_support_map"))
            set_ans("starter_missing_source_flags", data.get("starter_missing_source_flags"))
            set_ans("starter_abstract_seed", data.get("starter_abstract_seed"))
            for f in data.get("starter_missing_source_flags", []):
                add_flag(f)
            st.session_state.project["step"] = 3
            touch()
            st.rerun()
        if st.session_state.project["outputs"].get("main_point_result"):
            res = st.session_state.project["outputs"]["main_point_result"]
            st.write(f"**Main legal point**: {res.get('main_point_cleaned','')}")
            st.write(f"**Working question**: {res.get('working_question','')}")
            st.write(f"**Working title**: {res.get('working_title','')}")
            st.write("**Starter outline**")
            for i, item in enumerate(ans("starter_outline", []), 1):
                st.markdown(f"{i}. {item}")

    elif step == 3:
        st.markdown("## Step 4 — Add to Your Paper")
        downstream_warning(3)
        quote_box("What to do here", "To add to your ideas to the paper, here are further questions that might be useful to be answered. Not all fields need to be filled. Use what helps.")
        st.markdown(f'<span class="opt">Optional refinement step</span><span class="opt">Time: {TIME_EST["quick_3"]}</span>', unsafe_allow_html=True)
        left, right = st.columns(2)
        with left:
            st.write("**Left side — what is already inside the paper**")
            scope_in = st.text_area("What clearly belongs inside the paper?", value=ans("scope_in",""), height=120)
        with right:
            st.write("**Right side — what consequence should follow from the legal point**")
            consequence = st.text_area("What consequence or legal result do you want the paper to show?", value=ans("scope_out",""), height=120)
        support_gap = st.text_area("Optional: what authority still feels missing?", value=ans("support_gap",""), height=90)
        weakness = st.text_area("Optional: what is the biggest weakness or uncertainty for now?", value=ans("weakness",""), height=90)
        if st.button("Add these refinements", type="primary"):
            set_ans("scope_in", scope_in)
            set_ans("scope_out", consequence)
            set_ans("support_gap", support_gap)
            set_ans("weakness", weakness)
            if support_gap:
                add_flag(f"Possible missing authority: {support_gap}")
            if weakness:
                add_flag(f"Known weakness: {weakness}")
            fallback = {
                "strengthened_summary": ans("starter_starter_summary",""),
                "refined_outline": ans("starter_outline", []),
                "new_flags": [x for x in [support_gap, weakness] if x],
            }
            system = """
Refine the current article starter based on optional writer answers.
Return JSON with:
strengthened_summary
refined_outline
new_flags
"""
            user = f"""Current summary: {ans('starter_starter_summary','')}
Current outline: {ans('starter_outline',[])}
Inside the paper: {scope_in}
Consequence or result to show: {consequence}
Missing authority: {support_gap}
Weakness: {weakness}
"""
            with st.spinner("Adding to the paper..."):
                data = call_model_json("add_to_paper", system, user, fallback)
            set_ans("deepen_strengthened_summary", data.get("strengthened_summary"))
            set_ans("deepen_refined_outline", data.get("refined_outline"))
            set_ans("deepen_new_flags", data.get("new_flags", []))
            for f in data.get("new_flags", []):
                add_flag(f)
            st.session_state.project["step"] = 4
            touch()
            st.rerun()

    elif step == 4:
        st.markdown("## Step 5 — Start Writing Package")
        downstream_warning(4)
        quote_box("What to do here", "This step gives you a usable drafting package right away. To make the paper your own, it gives you cues and starting language, not a finished article.")
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_4"]}</span>', unsafe_allow_html=True)
        if st.button("Create the writing package", type="primary"):
            outline = ans("deepen_refined_outline") or ans("starter_outline", [])
            fallback = {
                "abstract_seed": ans("starter_abstract_seed",""),
                "opening_options": [
                    "Start with the legal problem in direct terms.",
                    "Start with a case, doctrine, or rule already visible in the lecture.",
                    "Start with the legal consequence the paper wants to show.",
                ],
                "section_cues": {x: f"What do you want to say in '{x}' that your lecture already supports?" for x in outline},
                "ownership_prompt": "To make the paper your own, write one short paragraph explaining the paper’s main legal point in your own voice before drafting the first section.",
            }
            system = """
Create a practical writing package for a busy lecturer.
Return JSON with:
abstract_seed
opening_options
section_cues
ownership_prompt
"""
            user = f"""Outline: {outline}
Summary: {ans('deepen_strengthened_summary') or ans('starter_starter_summary')}
Main point result: {st.session_state.project['outputs'].get('main_point_result',{})}
Flags: {st.session_state.project['flags']}
"""
            with st.spinner("Creating the writing package..."):
                data = call_model_json("writing_package", system, user, fallback)
            set_ans("writing_package", data)
            st.session_state.project["step"] = 5
            touch()
            st.rerun()

    elif step == 5:
        st.markdown("## Step 6 — Review & Export")
        quote_box("What to do here", "This is the end of Quick Pass. Export your files, then start writing. After this, you may continue to Deep Pass to strengthen the paper further.")
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_5"]}</span>', unsafe_allow_html=True)
        if st.session_state.project["flags"]:
            st.write("**Carry-forward flags**")
            for f in st.session_state.project["flags"]:
                st.markdown(f'<span class="flag">{f}</span>', unsafe_allow_html=True)
        st.markdown("### Your exports")
        st.caption("You have two export types: one for humans, one for machines.")
        st.download_button("Download human-readable pre-writing kit (.docx)", data=make_human_export(), file_name=f"pre_writing_kit_{APP_VERSION}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
        st.download_button("Download machine-readable checkpoint (.json)", data=make_machine_export(), file_name=f"checkpoint_{APP_VERSION}.json", mime="application/json")
        st.markdown("### What to do after Quick Pass")
        st.write("1. Export your files.")
        st.write("2. You may already begin drafting from the kit.")
        st.write("3. If you want to improve the paper before drafting, continue to Deep Pass.")
        if st.button("Continue to Deep Pass"):
            st.session_state.project["phase"] = "deep"
            st.session_state.project["step"] = 0
            touch()
            st.rerun()

# DEEP PASS
else:
    if step == 0:
        st.markdown("## Deep Pass — Step 1 — Strengthen Support")
        quote_box("What this step does", "This step revisits your paper only after Quick Pass is done. It helps identify stronger authorities, missing support, and support priorities without restarting the whole workflow.")
        st.markdown(f'<span class="req">Required for Deep Pass</span><span class="opt">Time: {TIME_EST["deep_0"]}</span>', unsafe_allow_html=True)
        current_flags = st.session_state.project["flags"]
        if current_flags:
            st.write("Current carry-forward flags")
            for f in current_flags:
                st.markdown(f'<span class="flag">{f}</span>', unsafe_allow_html=True)
        more_sources = st.text_area("What sources, cases, or authorities do you now want to add or prioritize?", value=ans("deep_support_input",""), height=120)
        if st.button("Strengthen support", type="primary"):
            set_ans("deep_support_input", more_sources)
            fallback = {
                "support_summary": "The paper now has a clearer list of authorities to prioritize.",
                "support_priorities": ["Add the strongest directly relevant authority first.", "Mark which authorities support the main point and which only add background."],
                "new_flags": [],
            }
            system = """
Strengthen support for an existing article starter.
Return JSON with:
support_summary
support_priorities
new_flags
"""
            user = f"""Current outline: {ans('deepen_refined_outline') or ans('starter_outline')}
Current flags: {current_flags}
New source priorities: {more_sources}
Authorities already mentioned: {ans('materials_authorities_mentioned',[])}
"""
            with st.spinner("Strengthening support..."):
                data = call_model_json("deep_strengthen_support", system, user, fallback)
            set_ans("deep_support_summary", data.get("support_summary"))
            set_ans("deep_support_priorities", data.get("support_priorities", []))
            for f in data.get("new_flags", []):
                add_flag(f)
            st.session_state.project["step"] = 1
            touch()
            st.rerun()
        if ans("deep_support_summary"):
            st.write(ans("deep_support_summary"))
            for item in ans("deep_support_priorities", []):
                st.markdown(f"- {item}")

    elif step == 1:
        st.markdown("## Deep Pass — Step 2 — Tighten the Argument")
        quote_box("What this step does", "This step helps narrow, sharpen, or stress-test the paper’s main legal point after Quick Pass has already produced a usable draft path.")
        st.markdown(f'<span class="req">Required for Deep Pass</span><span class="opt">Time: {TIME_EST["deep_1"]}</span>', unsafe_allow_html=True)
        stress = st.text_area("What part of the current argument still feels too broad, weak, or under-defined?", value=ans("deep_argument_input",""), height=120)
        if st.button("Tighten the argument", type="primary"):
            set_ans("deep_argument_input", stress)
            fallback = {
                "argument_summary": "The argument has been tightened by clarifying what the paper must prove and what it should leave aside.",
                "narrowing_moves": ["Make the main claim more precise.", "Cut side issues that do not help prove the main legal point."],
                "new_flags": [],
            }
            system = """
Tighten an existing article argument after a quick pass.
Return JSON with:
argument_summary
narrowing_moves
new_flags
"""
            user = f"""Current legal point: {st.session_state.project['outputs'].get('main_point_result',{})}
Current outline: {ans('deepen_refined_outline') or ans('starter_outline')}
Current concern: {stress}
"""
            with st.spinner("Tightening the argument..."):
                data = call_model_json("deep_tighten_argument", system, user, fallback)
            set_ans("deep_argument_summary", data.get("argument_summary"))
            set_ans("deep_narrowing_moves", data.get("narrowing_moves", []))
            for f in data.get("new_flags", []):
                add_flag(f)
            st.session_state.project["step"] = 2
            touch()
            st.rerun()
        if ans("deep_argument_summary"):
            st.write(ans("deep_argument_summary"))
            for item in ans("deep_narrowing_moves", []):
                st.markdown(f"- {item}")

    elif step == 2:
        st.markdown("## Deep Pass — Step 3 — Improve the Writing Pack")
        quote_box("What this step does", "This final Deep Pass step improves the package you will draft from: stronger opening options, clearer section cues, and a tighter abstract seed.")
        st.markdown(f'<span class="req">Required for Deep Pass</span><span class="opt">Time: {TIME_EST["deep_2"]}</span>', unsafe_allow_html=True)
        improve_note = st.text_area("What part of the writing package do you want to improve most?", value=ans("deep_writing_input",""), height=120)
        if st.button("Improve the writing pack", type="primary"):
            set_ans("deep_writing_input", improve_note)
            fallback = {
                "writing_summary": "The writing package has been improved to make drafting easier and more direct.",
                "extra_opening_options": ["Use the sharpest legal conflict first.", "Open with the clearest practical consequence for the field."],
            }
            system = """
Improve an existing writing package after quick pass.
Return JSON with:
writing_summary
extra_opening_options
"""
            user = f"""Current writing package: {ans('writing_package')}
Improvement requested: {improve_note}
"""
            with st.spinner("Improving the writing pack..."):
                data = call_model_json("deep_improve_writing_pack", system, user, fallback)
            set_ans("deep_writing_summary", data.get("writing_summary"))
            set_ans("deep_extra_opening_options", data.get("extra_opening_options", []))
            touch()
            st.success("Deep Pass complete.")
        if ans("deep_writing_summary"):
            st.write(ans("deep_writing_summary"))
            for item in ans("deep_extra_opening_options", []):
                st.markdown(f"- {item}")
            st.markdown("### Final exports")
            st.download_button("Download updated human-readable pre-writing kit (.docx)", data=make_human_export(), file_name=f"pre_writing_kit_{APP_VERSION}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
            st.download_button("Download updated machine-readable checkpoint (.json)", data=make_machine_export(), file_name=f"checkpoint_{APP_VERSION}.json", mime="application/json")
