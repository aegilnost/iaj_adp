import os
import json
import datetime as dt
from io import BytesIO
from typing import Any, Dict, List, Optional

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import docx
except Exception:
    docx = None

try:
    from pypdf import PdfReader
except Exception:
    PdfReader = None

APP_NAME = "Write and Come Back"
APP_VERSION = "v0.8.0"
STEPS = [
    "Welcome",
    "Read My Materials",
    "Choose the Main Legal Point",
    "Build the Article Starter",
    "Add to Your Paper",
    "Start Writing Package",
    "Review & Export",
]

LAW_SUGGESTIONS = {
    "data privacy act": {
        "title": "Republic Act No. 10173 (Data Privacy Act of 2012)",
        "link": "https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/",
    },
    "intellectual property code": {
        "title": "Republic Act No. 8293 (Intellectual Property Code of the Philippines)",
        "link": "https://www.officialgazette.gov.ph/1997/06/06/republic-act-no-8293/",
    },
    "constitution": {
        "title": "1987 Constitution of the Republic of the Philippines",
        "link": "https://www.officialgazette.gov.ph/constitutions/1987-constitution/",
    },
    "electronic evidence": {
        "title": "Rules on Electronic Evidence",
        "link": "https://lawphil.net/courts/supreme/am/am_01-7-01-sc_2001.html",
    },
    "cybercrime prevention act": {
        "title": "Republic Act No. 10175 (Cybercrime Prevention Act of 2012)",
        "link": "https://www.officialgazette.gov.ph/2012/09/12/republic-act-no-10175/",
    },
}


def init_state() -> None:
    if "project" not in st.session_state:
        st.session_state.project = {
            "version": APP_VERSION,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "step": 0,
            "answers": {},
            "outputs": {},
            "flags": [],
            "feedback": {},
            "api_log": [],
        }


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def touch() -> None:
    st.session_state.project["updated_at"] = now_iso()


def get_answer(key: str, default=None):
    return st.session_state.project["answers"].get(key, default)


def set_answer(key: str, value: Any) -> None:
    st.session_state.project["answers"][key] = value
    touch()


def get_output(key: str, default=None):
    return st.session_state.project["outputs"].get(key, default)


def set_output(key: str, value: Any) -> None:
    st.session_state.project["outputs"][key] = value
    touch()


def add_flag(flag: str) -> None:
    if flag and flag not in st.session_state.project["flags"]:
        st.session_state.project["flags"].append(flag)
        touch()


def get_openai_client() -> Optional[Any]:
    api_key = None
    try:
        api_key = st.secrets.get("OPENAI_API_KEY")
    except Exception:
        pass
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def model_status() -> str:
    return "OpenAI connected" if get_openai_client() else "Mock mode"


def safe_json_load(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end+1])
            except Exception:
                return {}
    return {}


def call_model_json(system_prompt: str, user_prompt: str, fallback: Dict[str, Any], stage: str) -> Dict[str, Any]:
    client = get_openai_client()
    if client is None:
        st.session_state.project["api_log"].append({"stage": stage, "mode": "mock", "time": now_iso()})
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
        content = resp.choices[0].message.content or "{}"
        data = safe_json_load(content)
        st.session_state.project["api_log"].append({"stage": stage, "mode": "openai", "time": now_iso()})
        return data or fallback
    except Exception as e:
        st.warning(f"The model call failed at {stage}. The app used a mock result instead. Error: {e}")
        st.session_state.project["api_log"].append({"stage": stage, "mode": "fallback_mock", "time": now_iso(), "error": str(e)})
        return fallback


def extract_text_from_upload(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    if name.endswith(".txt") or name.endswith(".md"):
        try:
            return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    if name.endswith(".docx") and docx is not None:
        try:
            d = docx.Document(BytesIO(raw))
            return "\n".join([p.text for p in d.paragraphs if p.text.strip()])
        except Exception:
            return ""
    if name.endswith(".pdf") and PdfReader is not None:
        try:
            reader = PdfReader(BytesIO(raw))
            pages = []
            for p in reader.pages[:30]:
                pages.append(p.extract_text() or "")
            return "\n".join(pages)
        except Exception:
            return ""
    return ""


def suggest_laws(query: str) -> List[Dict[str, str]]:
    q = (query or "").strip().lower()
    if not q:
        return []
    matches = []
    for key, val in LAW_SUGGESTIONS.items():
        if q in key or key in q:
            matches.append(val)
    return matches[:5]


def progress_ratio(step_idx: int) -> float:
    return (step_idx + 1) / len(STEPS)


def lecture_terms() -> List[str]:
    return get_answer("materials_keywords", []) or []


def project_packet() -> str:
    return json.dumps(st.session_state.project, indent=2, ensure_ascii=False)


def render_styles() -> None:
    st.markdown(
        """
        <style>
        .top-progress-wrap {margin-top: 0.35rem; margin-bottom: 1rem;}
        .top-progress-bar {height: 10px; background: #E8ECF2; border-radius: 999px; overflow: hidden;}
        .top-progress-fill {height: 10px; background: linear-gradient(90deg, #173b7a, #2b6cb0); border-radius: 999px;}
        .top-progress-steps {display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 14px;}
        .top-step {padding: 10px 8px; border: 1px solid #d8dde6; border-radius: 12px; background: #f9fbff; min-height: 74px;}
        .top-step.active {background: #173b7a; color: white; border-color: #173b7a;}
        .top-step.done {background: #eef5ff; border-color: #8fb4e8;}
        .top-step-num {font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; opacity: 0.92;}
        .top-step-title {font-size: 0.81rem; font-weight: 600; line-height: 1.24; margin-top: 4px;}
        .instruction-box {background: #f7f9fc; border: 1px solid #dce3ee; border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;}
        .soft-callout {background: #f9fbff; border-left: 4px solid #2b6cb0; padding: 12px 14px; border-radius: 8px; margin-bottom: 12px;}
        .flag-chip {display: inline-block; background: #fff3cd; color: #7a5b00; border: 1px solid #ffe08a; border-radius: 999px; padding: 4px 10px; margin: 4px 6px 0 0; font-size: 0.83rem;}
        .small-muted {color: #5c6773; font-size: 0.90rem;}
        .section-card {background: white; border: 1px solid #dce3ee; border-radius: 16px; padding: 18px;}
        .subhead {font-size: 0.97rem; font-weight: 600; margin-top: 0.2rem; margin-bottom: 0.4rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_progress(step_idx: int) -> None:
    pct = int(progress_ratio(step_idx) * 100)
    blocks = []
    for i, title in enumerate(STEPS):
        cls = "top-step"
        if i == step_idx:
            cls += " active"
        elif i < step_idx:
            cls += " done"
        blocks.append(f'<div class="{cls}"><div class="top-step-num">STEP {i+1}</div><div class="top-step-title">{title}</div></div>')
    st.markdown(
        f"""
        <div class="top-progress-wrap">
          <div class="small-muted"><strong>{APP_NAME}</strong> · {APP_VERSION} · {pct}% complete in this run</div>
          <div class="top-progress-bar"><div class="top-progress-fill" style="width:{pct}%"></div></div>
          <div class="top-progress-steps">{''.join(blocks)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"### {APP_NAME}")
        st.caption(f"{APP_VERSION} · {model_status()}")
        st.write("Built for busy lecturers: move forward first, improve later.")
        st.divider()
        st.markdown("#### Notes for the next version")
        step_name = STEPS[st.session_state.project["step"]]
        bucket = st.session_state.project["feedback"].setdefault(step_name, {})
        bucket["worked"] = st.text_area("What worked", value=bucket.get("worked", ""), key=f"fb_w_{step_name}")
        bucket["confusing"] = st.text_area("What was confusing", value=bucket.get("confusing", ""), key=f"fb_c_{step_name}")
        bucket["too_much"] = st.text_area("What felt too much", value=bucket.get("too_much", ""), key=f"fb_t_{step_name}")
        bucket["missing"] = st.text_area("What is missing", value=bucket.get("missing", ""), key=f"fb_m_{step_name}")
        bucket["notes"] = st.text_area("Other notes", value=bucket.get("notes", ""), key=f"fb_n_{step_name}")
        touch()
        st.download_button(
            "Export one refinement file",
            data=project_packet(),
            file_name=f"{APP_NAME.lower().replace(' ','_')}_refinement_{APP_VERSION}.json",
            mime="application/json",
            use_container_width=True,
        )


def advance_step() -> None:
    st.session_state.project["step"] += 1
    touch()
    st.rerun()


st.set_page_config(page_title=APP_NAME, layout="wide")
init_state()
render_styles()
render_sidebar()
render_top_progress(st.session_state.project["step"])

step = st.session_state.project["step"]

# STEP 1 Welcome
if step == 0:
    st.markdown("## Welcome")
    st.markdown(
        '<div class="instruction-box"><strong>How this platform helps</strong><br>'
        'It reads your lecture materials, pulls out likely legal points, and gets you to a usable article starter quickly. '
        'It is designed so you can write first and improve later. There is no backtracking in this run. Each step simply moves forward.</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="soft-callout">This early version is for busy lecturers. The goal is not perfection at the start. '
        'The goal is to get you to a workable article package without stopping your momentum.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("What to expect"):
        st.write("- The platform starts from your own lecture, transcript, slides, and legal materials.")
        st.write("- It focuses on legal arguments, not just any argument.")
        st.write("- It asks for only enough input to keep the paper moving.")
        st.write("- It carries missing-source notes to the end instead of blocking progress.")
        st.write("- This is a prototype. Do not upload confidential materials yet.")

    if st.button("Start the quick pass", type="primary"):
        advance_step()

# STEP 2 Read materials
elif step == 1:
    st.markdown("## Step 1 — Read My Materials")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'Upload your transcript, slides, notes, and optional bionote or CV. The platform will first read the materials and give back likely legal arguments, laws or cases already mentioned, and a few possible directions for the paper. '
        'You will confirm what is useful before moving on.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Lecture or presentation title", value=get_answer("presentation_title", ""))
        summary = st.text_area(
            "Short note on what the lecture was about",
            value=get_answer("short_context", ""),
            height=120,
        )
    with c2:
        speaker_note = st.text_area(
            "Bionote or CV note (optional)",
            value=get_answer("speaker_note", ""),
            height=120,
            help="Add this only if you want the platform to better understand your expertise or likely perspective.",
        )

    st.markdown(
        '<div class="instruction-box"><strong>Optional legal materials for now</strong><br>'
        'If you already know a law, rule, or case is central, mention it here. You may also upload PDF legal materials now. The platform will suggest likely sources for you to confirm.</div>',
        unsafe_allow_html=True,
    )
    legal_text = st.text_area(
        "Laws, cases, rules, or doctrines already central to the lecture",
        value=get_answer("legal_text", ""),
        height=110,
        placeholder="Example: Data Privacy Act, Rule on Electronic Evidence, Oposa v. Factoran, due process in administrative proceedings",
    )
    law_search = st.text_input("Search one law or rule to add now (optional)", value="")
    selected_laws = []
    suggestions = suggest_laws(law_search)
    if suggestions:
        st.write("Likely materials to confirm")
        for item in suggestions:
            checked = st.checkbox(f"{item['title']} — {item['link']}", key=f"law_{item['title']}")
            if checked:
                selected_laws.append(f"{item['title']} ({item['link']})")

    uploads = st.file_uploader(
        "Upload transcript, slides, notes, and optional PDF legal materials",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        key="uploads_v8",
    )

    if st.button("Read my materials", type="primary"):
        set_answer("presentation_title", title)
        set_answer("short_context", summary)
        set_answer("speaker_note", speaker_note)
        set_answer("legal_text", legal_text)
        set_answer("selected_laws", selected_laws)

        all_texts = []
        filenames = []
        for f in uploads or []:
            filenames.append(f.name)
            extracted = extract_text_from_upload(f)
            if extracted:
                all_texts.append(f"\n\n### FILE: {f.name}\n{extracted[:30000]}")
        set_answer("uploaded_files", filenames)

        joined = "\n".join(all_texts)[:90000]
        fallback = {
            "materials_summary": "The materials raise one or more legal problems that can be turned into an article. The next step is to confirm which legal point should anchor the paper.",
            "keywords": ["legal issue", "statutory framework", "case law"],
            "legal_arguments": [
                "A likely legal argument in the lecture concerns how a rule, doctrine, or statutory requirement should be understood.",
                "Another likely legal argument concerns what legal effect, duty, or consequence should follow from that rule or doctrine.",
            ],
            "authorities_mentioned": selected_laws,
            "possible_directions": [
                "Clarify the legal rule or doctrine at the center of the lecture.",
                "Show why the current legal treatment is insufficient or unclear.",
                "Argue for a sharper legal resolution to the problem raised in the lecture.",
            ],
            "support_map": {
                "supports_main_point": selected_laws,
                "related_but_not_yet_enough": [],
                "may_be_missing_but_not_blocking": [],
            },
        }
        system = """
You are helping a busy law lecturer turn lecture materials into a paper starter.
Read the materials and extract legal arguments only.
Do not extract just any argument.
Return JSON with:
materials_summary
keywords (5 to 10 recurring lecture-aware terms)
legal_arguments (3 to 6 likely legal arguments or legal tensions)
authorities_mentioned (laws, rules, cases, agencies, doctrines)
possible_directions (3 to 5 possible article directions)
support_map {supports_main_point, related_but_not_yet_enough, may_be_missing_but_not_blocking}
Use the lecture's own language where possible.
"""
        user = f"""
Lecture title: {title}
Short context: {summary}
Speaker note: {speaker_note}
Legal materials already in mind: {legal_text}
Confirmed legal materials from search suggestions: {selected_laws}
Uploaded files: {filenames}

MATERIALS:
{joined}
"""
        with st.spinner("Reading your materials..."):
            result = call_model_json(system, user, fallback, "read_materials")
        for k, v in result.items():
            set_answer(f"materials_{k}", v)
        advance_step()

    if get_answer("materials_materials_summary"):
        st.markdown("### What the platform found")
        st.write(get_answer("materials_materials_summary"))
        st.write("Likely legal arguments from your lecture")
        for arg in get_answer("materials_legal_arguments", []):
            st.markdown(f"- {arg}")
        st.write("Authorities already visible from your materials")
        for a in get_answer("materials_authorities_mentioned", []):
            st.markdown(f"- {a}")

# STEP 3 Choose main legal point
elif step == 2:
    st.markdown("## Step 2 — Choose the Main Legal Point")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'Below are legal arguments drawn from your materials. Choose the one closest to the paper you want to write. '
        'This step is about extracting legal arguments, not just any argument.</div>',
        unsafe_allow_html=True,
    )
    args = get_answer("materials_legal_arguments", [])
    dirs = get_answer("materials_possible_directions", [])
    selected = st.radio(
        "Choose the legal point closest to the paper you want",
        options=[""] + args + dirs + ["Something else"],
        index=0,
        key="main_legal_choice_v8",
    )

    terms = lecture_terms()
    term_hint = terms[0] if terms else "your lecture"
    st.markdown(
        f'<div class="instruction-box"><strong>Instructions</strong><br>'
        f'Use your own words here. If helpful, use the language already visible in {term_hint}. '
        f'The goal is not to perfect the paper. The goal is to state clearly what legal point the paper will push.</div>',
        unsafe_allow_html=True,
    )
    main_point = st.text_area(
        "What do you want to argue for this article?",
        value=get_answer("main_point", ""),
        height=130,
        placeholder="Example: In explaining the anatomy of the ghost project, I want the article to argue that the weak point is not just implementation but the legal structure that allows accountability to blur.",
    )
    emphasis = st.text_input(
        "Which part of the legal point do you most want to emphasize?",
        value=get_answer("main_emphasis", ""),
        placeholder="Example: flood control, ghost project, due process, authorization, transparency",
    )

    if st.button("Build the main legal point", type="primary"):
        set_answer("selected_legal_point", selected)
        set_answer("main_point", main_point)
        set_answer("main_emphasis", emphasis)
        fallback = {
            "main_point_cleaned": main_point or selected,
            "working_question": "What is the strongest legal question that follows from this lecture point, and how should the paper answer it?",
            "working_title": "A Legal Problem Emerging from the Lecture Materials",
            "reason_for_choice": "This legal point seems most capable of becoming a clear paper because it identifies a legal problem and points toward a legal consequence or resolution.",
        }
        system = """
You help a busy law lecturer sharpen one legal point into an article anchor.
Return JSON with:
main_point_cleaned
working_question
working_title
reason_for_choice
Use lecture-aware language where possible.
Focus on legal argument only.
"""
        user = f"""
Lecture-aware terms: {terms}
Legal arguments extracted: {args}
Possible directions: {dirs}
Chosen option: {selected}
Writer's own main point: {main_point}
Part to emphasize: {emphasis}
"""
        with st.spinner("Sharpening the main legal point..."):
            result = call_model_json(system, user, fallback, "choose_legal_point")
        set_output("main_legal_point_result", result)
        advance_step()

    result = get_output("main_legal_point_result")
    if result:
        st.markdown("### Article anchor")
        st.write(f"**Main legal point**: {result.get('main_point_cleaned','')}")
        st.write(f"**Working question**: {result.get('working_question','')}")
        st.write(f"**Working title**: {result.get('working_title','')}")
        st.caption(result.get("reason_for_choice", ""))

# STEP 4 Build article starter
elif step == 3:
    st.markdown("## Step 3 — Build the Article Starter")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'This step gives you a first article package quickly: a title, a main question, a short article summary, a rough outline, and a support map. '
        'You are not polishing yet. You are getting something you can write from.</div>',
        unsafe_allow_html=True,
    )

    if st.button("Build my article starter", type="primary"):
        anchor = get_output("main_legal_point_result", {})
        fallback = {
            "starter_summary": anchor.get("main_point_cleaned", "A legal article starter has been built from the lecture materials."),
            "outline": [
                "Opening legal problem",
                "Rule, doctrine, or framework",
                "Main legal tension",
                "Why the current treatment is insufficient or unclear",
                "Proposed legal resolution",
                "Conclusion",
            ],
            "support_map": {
                "supports_main_point": get_answer("materials_authorities_mentioned", []),
                "related_but_not_yet_enough": [],
                "may_be_missing_but_not_blocking": ["Additional supporting authority may still be needed later."],
            },
            "missing_source_flags": ["Possible missing source on the legal consequence or result side of the paper."],
            "abstract_seed": "This paper examines a legal problem surfaced in the lecture materials and argues for a clearer doctrinal or institutional treatment.",
        }
        system = """
Build a first article starter for a busy law lecturer.
Return JSON with:
starter_summary
outline (4 to 6 section titles)
support_map {supports_main_point, related_but_not_yet_enough, may_be_missing_but_not_blocking}
missing_source_flags
abstract_seed
Keep it simple and usable.
Do not build a heavy journal or literature architecture step here.
"""
        user = f"""
Materials summary: {get_answer('materials_materials_summary','')}
Main legal point result: {json.dumps(anchor, ensure_ascii=False)}
Authorities already mentioned: {get_answer('materials_authorities_mentioned',[])}
"""
        with st.spinner("Building your article starter..."):
            result = call_model_json(system, user, fallback, "article_starter")
        for k, v in result.items():
            set_answer(f"starter_{k}", v)
        for flag in result.get("missing_source_flags", []):
            add_flag(flag)
        advance_step()

    if get_answer("starter_starter_summary"):
        st.markdown("### Your first article package")
        st.write(get_answer("starter_starter_summary"))
        st.write("**Rough outline**")
        for i, item in enumerate(get_answer("starter_outline", []), 1):
            st.markdown(f"{i}. {item}")
        st.write("**Support map**")
        smap = get_answer("starter_support_map", {})
        labels = [
            ("supports_main_point", "Already supporting your main point"),
            ("related_but_not_yet_enough", "Related but not enough yet"),
            ("may_be_missing_but_not_blocking", "Possibly missing, but not blocking"),
        ]
        for key, label in labels:
            st.markdown(f"**{label}**")
            vals = smap.get(key, []) if isinstance(smap, dict) else []
            if vals:
                for v in vals:
                    st.markdown(f"- {v}")
            else:
                st.caption("None identified yet.")

# STEP 5 Add to your paper
elif step == 4:
    st.markdown("## Step 4 — Add to Your Paper")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'To add to your ideas to the paper, here are further questions that might be useful to be answered. '
        'Answer only what helps. This stage is for strengthening what you already have, not for stopping you from moving forward.</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns(2)
    with left:
        st.markdown("### Left side — what the law, rule, or doctrine is doing")
        st.markdown(
            '<div class="instruction-box">Write what clearly belongs inside the paper. This can be the doctrine, statutory requirement, interpretive question, or legal process that the paper must directly address.</div>',
            unsafe_allow_html=True,
        )
        scope_in = st.text_area(
            "What should clearly be inside the paper?",
            value=get_answer("scope_in", ""),
            height=110,
            placeholder="Example: the doctrine, statutory requirement, rule, or legal process that the paper must directly address",
        )
        st.markdown(
            '<div class="instruction-box">If the paper still feels under-supported, name one law, case, issuance, or doctrinal line that would strengthen it. If you do not have anything to add yet, you may leave this blank and proceed.</div>',
            unsafe_allow_html=True,
        )
        support_gap = st.text_area(
            "Which supporting authority still feels missing?",
            value=get_answer("support_gap", ""),
            height=110,
            placeholder="Example: one case, statutory basis, agency issuance, or doctrinal line that would strengthen the paper",
        )
    with right:
        st.markdown("### Right side — what legal result or consequence you want to show")
        st.markdown(
            '<div class="instruction-box">Write what should stay outside the paper for now. This helps keep the draft manageable for a busy lecturer.</div>',
            unsafe_allow_html=True,
        )
        scope_out = st.text_area(
            "What should stay outside the paper for now?",
            value=get_answer("scope_out", ""),
            height=110,
            placeholder="Example: a policy debate, a comparator jurisdiction, or a side issue that is interesting but not needed yet",
        )
        st.markdown(
            '<div class="instruction-box">Name the biggest weakness or uncertainty in the paper so far. This will become a carry-forward note, not a blocker.</div>',
            unsafe_allow_html=True,
        )
        weakness = st.text_area(
            "What is the biggest weakness or uncertainty in the paper so far?",
            value=get_answer("weakness", ""),
            height=110,
            placeholder="Example: the legal consequence is still under-supported, or the claim may be too broad",
        )

    if st.button("Add these ideas", type="primary"):
        set_answer("scope_in", scope_in)
        set_answer("scope_out", scope_out)
        set_answer("support_gap", support_gap)
        set_answer("weakness", weakness)
        if support_gap:
            add_flag(f"Possible missing authority: {support_gap}")
        if weakness:
            add_flag(f"Known weakness: {weakness}")
        fallback = {
            "strengthened_summary": get_answer("starter_starter_summary", ""),
            "refined_outline": get_answer("starter_outline", []),
            "new_flags": [x for x in [support_gap, weakness] if x],
        }
        system = """
Strengthen the article starter without making it heavy.
Return JSON with:
strengthened_summary
refined_outline
new_flags
Keep it practical for a busy lecturer.
"""
        user = f"""
Current summary: {get_answer('starter_starter_summary','')}
Current outline: {get_answer('starter_outline',[])}
Inside the paper: {scope_in}
Outside the paper: {scope_out}
Possible missing authority: {support_gap}
Biggest weakness: {weakness}
"""
        with st.spinner("Adding to your paper..."):
            result = call_model_json(system, user, fallback, "add_to_paper")
        for k, v in result.items():
            set_answer(f"deepen_{k}", v)
        advance_step()

# STEP 6 Writing package
elif step == 5:
    st.markdown("## Step 5 — Start Writing Package")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'This step turns your current article starter into something you can actually write from today: a short abstract seed, an opening move, and section-by-section cues. '
        'To make the paper your own, the package is written as guidance for drafting, not as a finished paper.</div>',
        unsafe_allow_html=True,
    )

    if st.button("Create my writing package", type="primary"):
        outline = get_answer("deepen_refined_outline") or get_answer("starter_outline", [])
        fallback = {
            "abstract_seed": get_answer("starter_abstract_seed", "This paper examines a legal problem surfaced in the lecture materials."),
            "opening_options": [
                "Start with the legal problem in plain terms.",
                "Start with a case, rule, or institutional moment already mentioned in the lecture.",
                "Start with the main legal tension the paper will resolve.",
            ],
            "section_cues": [{"section": x, "cue": f"What do you want to say in '{x}' that your lecture already supports?"} for x in outline],
            "ownership_prompt": "To make the paper your own, write one short paragraph explaining the paper’s main legal point in your own voice.",
        }
        system = """
Create a practical writing package for a busy law lecturer.
Return JSON with:
abstract_seed
opening_options (3)
section_cues (one per section)
ownership_prompt
Keep it practical and drafting-oriented.
"""
        user = f"""
Outline: {outline}
Summary: {get_answer('deepen_strengthened_summary') or get_answer('starter_starter_summary')}
Main legal point: {get_answer('main_point')}
Flags: {st.session_state.project['flags']}
"""
        with st.spinner("Creating your writing package..."):
            result = call_model_json(system, user, fallback, "writing_package")
        set_answer("writing_package", result)
        advance_step()

    pkg = get_answer("writing_package")
    if pkg:
        st.markdown("### Your writing package")
        st.write("**Abstract seed**")
        st.write(pkg.get("abstract_seed", ""))
        st.write("**Opening options**")
        for x in pkg.get("opening_options", []):
            st.markdown(f"- {x}")
        st.write("**Section cues**")
        for item in pkg.get("section_cues", []):
            st.markdown(f"**{item.get('section','')}** — {item.get('cue','')}")
        st.info(pkg.get("ownership_prompt", ""))

# STEP 7 Export
elif step == 6:
    st.markdown("## Step 6 — Review and Export")
    st.markdown(
        '<div class="instruction-box"><strong>Instructions</strong><br>'
        'You already have a workable article starter. This last step gathers everything in one place so you can write, pause, and come back later without losing the thread.</div>',
        unsafe_allow_html=True,
    )
    st.write("### Carry-forward notes")
    if st.session_state.project["flags"]:
        for flag in st.session_state.project["flags"]:
            st.markdown(f'<span class="flag-chip">{flag}</span>', unsafe_allow_html=True)
    else:
        st.caption("No carry-forward notes recorded yet.")

    st.write("### Download everything in one file")
    packet = project_packet()
    st.download_button(
        "Download project + feedback file",
        data=packet,
        file_name=f"write_and_come_back_{APP_VERSION}.json",
        mime="application/json",
        type="primary",
    )

    st.write("### Save this run")
    st.download_button(
        "Download checkpoint",
        data=packet,
        file_name=f"checkpoint_{APP_VERSION}.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded_checkpoint = st.file_uploader("Load a saved checkpoint", type=["json"], key="checkpoint_loader_v8")
    if uploaded_checkpoint is not None and st.button("Load this checkpoint"):
        data = json.load(uploaded_checkpoint)
        st.session_state.project = data
        touch()
        st.success("Checkpoint loaded.")
        st.rerun()
