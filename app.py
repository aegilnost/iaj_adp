
import io
import json
import os
import datetime as dt
from typing import Any, Dict, List

import streamlit as st

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import docx
except Exception:
    docx = None

APP_NAME = "Write and Come Back"
APP_VERSION = "v0.11.0"

QUICK_STEPS = [
    "Welcome",
    "Load Layer 1 Context",
    "Start from This",
    "Write Your Core Idea",
    "Quick Writing Starter",
    "Write Now & Export",
]

FULL_STEPS = [
    "Verify Authorities",
    "Tighten the Claim",
    "Strengthen Support",
    "Improve Writing Pack",
    "Export Refined Pack",
]

TIME_EST = {
    "quick_0": "1–2 min",
    "quick_1": "1–3 min",
    "quick_2": "1–2 min",
    "quick_3": "3–5 min",
    "quick_4": "1–2 min",
    "quick_5": "1–2 min",
    "full_0": "2–4 min",
    "full_1": "2–4 min",
    "full_2": "2–4 min",
    "full_3": "2–4 min",
    "full_4": "1–2 min",
}

# -----------------------------------
# State
# -----------------------------------
def init_state():
    if "project" not in st.session_state:
        st.session_state.project = {
            "version": APP_VERSION,
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "updated_at": dt.datetime.now().isoformat(timespec="seconds"),
            "phase": "quick",
            "step": 0,
            "answers": {},
            "outputs": {},
            "flags": [],
            "feedback": {},
            "api_log": [],
            "layer1_loaded": False,
        }

def touch():
    st.session_state.project["updated_at"] = dt.datetime.now().isoformat(timespec="seconds")

def ans(key: str, default=None):
    return st.session_state.project["answers"].get(key, default)

def set_ans(key: str, value: Any):
    st.session_state.project["answers"][key] = value
    touch()

def set_out(key: str, value: Any):
    st.session_state.project["outputs"][key] = value
    touch()

def add_flag(text: str):
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
        st.session_state.project["api_log"].append({
            "stage": stage,
            "mode": "mock",
            "time": dt.datetime.now().isoformat(timespec="seconds"),
        })
        return fallback
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.35,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        st.session_state.project["api_log"].append({
            "stage": stage,
            "mode": "openai",
            "time": dt.datetime.now().isoformat(timespec="seconds"),
        })
        return data or fallback
    except Exception as e:
        st.warning(f"Model call failed at {stage}. Using fallback instead.")
        st.session_state.project["api_log"].append({
            "stage": stage,
            "mode": "fallback",
            "error": str(e),
            "time": dt.datetime.now().isoformat(timespec="seconds"),
        })
        return fallback

# -----------------------------------
# UI Helpers
# -----------------------------------
def quote_box(title: str, body: str):
    st.markdown(f"""
    <div style="background:#f7f9fc;border:1px solid #dce3ee;border-radius:12px;padding:12px 14px;margin-bottom:12px">
      <div style="font-size:0.84rem;color:#445; font-weight:700; margin-bottom:6px">{title}</div>
      <div style="font-size:0.95rem;color:#222; line-height:1.45">{body}</div>
    </div>
    """, unsafe_allow_html=True)

def progress():
    phase = st.session_state.project["phase"]
    step = st.session_state.project["step"]
    steps = QUICK_STEPS if phase == "quick" else FULL_STEPS
    pct = int((step + 1) / len(steps) * 100)

    st.markdown("""
    <style>
    .stepcard{border:1px solid #dce3ee;border-radius:14px;background:#f8fbff;padding:10px;min-height:86px}
    .stepcard.active{background:#173b7a;color:white;border-color:#173b7a}
    .stepcard.done{background:#eef5ff}
    .flag{display:inline-block;background:#fff3cd;border:1px solid #ffe08a;color:#7a5b00;border-radius:999px;padding:4px 10px;font-size:.82rem;margin:3px 6px 0 0}
    .req{display:inline-block;border-radius:999px;padding:3px 9px;font-size:.75rem;background:#eef5ff;color:#173b7a;margin-right:6px}
    .opt{display:inline-block;border-radius:999px;padding:3px 9px;font-size:.75rem;background:#f5f5f5;color:#666;margin-right:6px}
    .good{display:inline-block;border-radius:999px;padding:3px 9px;font-size:.75rem;background:#ecfdf3;color:#12743b;margin-right:6px}
    </style>
    """, unsafe_allow_html=True)

    st.write(f"**{APP_NAME}** · {APP_VERSION} · {'Quick Pass' if phase == 'quick' else 'Full Pass'}")
    st.progress(pct / 100)

    cols = st.columns(len(steps))
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
    steps = QUICK_STEPS if phase == "quick" else FULL_STEPS
    label = f"{phase.title()} — {steps[step]}"
    fb = st.session_state.project["feedback"].setdefault(label, {})
    st.sidebar.markdown("## Notes for the next version")
    fb["worked"] = st.sidebar.text_area("What worked", value=fb.get("worked", ""), key=f"worked_{label}")
    fb["confusing"] = st.sidebar.text_area("What was confusing", value=fb.get("confusing", ""), key=f"conf_{label}")
    fb["too_much"] = st.sidebar.text_area("What felt too much", value=fb.get("too_much", ""), key=f"too_{label}")
    fb["missing"] = st.sidebar.text_area("What is missing", value=fb.get("missing", ""), key=f"miss_{label}")
    fb["notes"] = st.sidebar.text_area("Other notes", value=fb.get("notes", ""), key=f"notes_{label}")
    touch()

def make_machine_export() -> str:
    return json.dumps(st.session_state.project, indent=2, ensure_ascii=False)

def make_human_export() -> bytes:
    if docx is None:
        return make_machine_export().encode("utf-8")

    d = docx.Document()
    p = st.session_state.project
    d.add_heading(f"{APP_NAME} — Pre-Writing Kit", 0)
    d.add_paragraph(f"Version: {p['version']}")
    d.add_paragraph(f"Created: {p['created_at']}")
    d.add_paragraph(f"Updated: {p['updated_at']}")

    d.add_heading("Layer 1 Context", level=1)
    for key in ["layer1_materials_summary", "layer1_best_direction_title", "layer1_best_direction_reason"]:
        if ans(key):
            d.add_paragraph(str(ans(key)))

    d.add_heading("Quick Pass", level=1)
    for key in ["quick_selected_point", "quick_selected_point_user_edit", "quick_core_idea", "quick_result_summary"]:
        if ans(key):
            d.add_paragraph(str(ans(key)))

    if ans("quick_outline"):
        d.add_heading("Quick Outline", level=2)
        for item in ans("quick_outline", []):
            d.add_paragraph(str(item), style="List Number")

    if ans("quick_writing_package"):
        wp = ans("quick_writing_package")
        d.add_heading("Quick Writing Package", level=2)
        d.add_paragraph("Abstract seed:")
        d.add_paragraph(str(wp.get("abstract_seed", "")))
        d.add_paragraph("Opening options:")
        for item in wp.get("opening_options", []):
            d.add_paragraph(str(item), style="List Bullet")
        d.add_paragraph("Section cues:")
        for k, v in wp.get("section_cues", {}).items():
            d.add_paragraph(f"{k}: {v}", style="List Bullet")
        d.add_paragraph("Write-now instruction:")
        d.add_paragraph(str(wp.get("write_now_prompt", "")))

    if ans("full_refined_claim") or ans("full_verified_authorities") or ans("full_improved_writing_pack"):
        d.add_heading("Full Pass", level=1)
        if ans("full_refined_claim"):
            d.add_paragraph(f"Refined claim: {ans('full_refined_claim')}")
        if ans("full_support_summary"):
            d.add_paragraph(f"Support summary: {ans('full_support_summary')}")
        if ans("full_improved_writing_summary"):
            d.add_paragraph(f"Writing pack improvements: {ans('full_improved_writing_summary')}")

    if p.get("flags"):
        d.add_heading("Carry-forward Flags", level=1)
        for f in p["flags"]:
            d.add_paragraph(str(f), style="List Bullet")

    d.add_heading("What to do next", level=1)
    d.add_paragraph("1. Read this kit once without editing.")
    d.add_paragraph("2. Write one section in your own words.")
    d.add_paragraph("3. Keep writing before refining.")
    d.add_paragraph("4. Return to Full Pass only if you need stronger support, a tighter claim, or a better writing pack.")

    bio = io.BytesIO()
    d.save(bio)
    bio.seek(0)
    return bio.getvalue()

def clear_downstream(mode: str, from_step: int):
    if mode == "quick":
        mapping = {
            1: ["layer1_raw", "layer1_materials_summary", "layer1_legal_arguments", "layer1_authorities", "layer1_article_directions", "layer1_best_direction_title", "layer1_best_direction_reason"],
            2: ["quick_selected_point", "quick_selected_point_user_edit", "quick_result_summary", "quick_outline", "quick_working_title", "quick_working_question"],
            3: ["quick_core_idea", "quick_goal_signal", "quick_weak_point"],
            4: ["quick_writing_package"],
        }
        for idx, keys in mapping.items():
            if idx >= from_step:
                for key in keys:
                    st.session_state.project["answers"].pop(key, None)
                    st.session_state.project["outputs"].pop(key, None)
    else:
        mapping = {
            0: ["full_verified_authorities", "full_authority_additions", "full_authority_removals"],
            1: ["full_refined_claim"],
            2: ["full_support_summary", "full_support_needs"],
            3: ["full_improved_writing_pack", "full_improved_writing_summary"],
        }
        for idx, keys in mapping.items():
            if idx >= from_step:
                for key in keys:
                    st.session_state.project["answers"].pop(key, None)
                    st.session_state.project["outputs"].pop(key, None)
    touch()

def revisit_warning(mode: str, from_step: int):
    st.warning("You may revisit an earlier step. But if you change a response and run the model again, later outputs should be rebuilt from this step forward.")
    if st.button("Clear downstream outputs from this step"):
        clear_downstream(mode, from_step)
        st.success("Later outputs were cleared. Re-run from this step.")
        st.rerun()

def parse_layer1_json(data: Dict[str, Any]):
    set_ans("layer1_raw", data)
    set_ans("layer1_materials_summary", data.get("materials_summary") or data.get("materials_materials_summary") or "")
    set_ans("layer1_legal_arguments", data.get("legal_arguments") or data.get("materials_legal_arguments") or [])
    set_ans("layer1_authorities", data.get("authorities") or data.get("materials_authorities_mentioned") or [])
    set_ans("layer1_article_directions", data.get("article_directions") or data.get("materials_possible_directions") or [])

    refinement = data.get("refinement") or data.get("section3_refinement") or {}
    if isinstance(refinement, dict):
        set_ans("layer1_best_direction_title", refinement.get("strongest_direction") or "")
        set_ans("layer1_best_direction_reason", refinement.get("why_strongest") or "")
        set_ans("layer1_clarify_before_writing", refinement.get("what_to_clarify") or "")

    # fallback if refinement not present
    if not ans("layer1_best_direction_title") and ans("layer1_article_directions"):
        dirs = ans("layer1_article_directions")
        first = dirs[0]
        if isinstance(first, dict):
            set_ans("layer1_best_direction_title", first.get("title") or first.get("direction_title") or "Suggested starting direction")
            set_ans("layer1_best_direction_reason", first.get("why_viable") or first.get("description") or "")
        else:
            set_ans("layer1_best_direction_title", str(first))
            set_ans("layer1_best_direction_reason", "This was the first direction surfaced from Layer 1.")
    st.session_state.project["layer1_loaded"] = True
    touch()

# -----------------------------------
# App
# -----------------------------------
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
    st.download_button(
        "Export machine-readable file (.json)",
        data=make_machine_export(),
        file_name=f"checkpoint_{APP_VERSION}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.download_button(
        "Export human-readable pre-writing kit (.docx)",
        data=make_human_export(),
        file_name=f"pre_writing_kit_{APP_VERSION}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        use_container_width=True,
    )
    uploaded_cp = st.file_uploader("Load saved checkpoint", type=["json"], key="load_checkpoint")
    if uploaded_cp and st.button("Load this checkpoint", use_container_width=True):
        st.session_state.project = json.load(uploaded_cp)
        st.success("Checkpoint loaded.")
        st.rerun()

phase = st.session_state.project["phase"]
step = st.session_state.project["step"]

# -----------------------------------
# QUICK PASS
# -----------------------------------
if phase == "quick":
    if step == 0:
        st.markdown("## Step 1 — Welcome")
        quote_box(
            "What this platform does",
            "It takes the lecture context already prepared in Layer 1, then helps you move quickly from that context to a workable writing starter. Quick Pass is lean on purpose. The goal is to help you write before you edit."
        )
        quote_box(
            "What to expect",
            "Quick Pass comes first. It should feel light and forward-moving. Full Pass comes only after Quick Pass is done, and only if you want to make the paper stronger."
        )
        st.markdown("### Before you begin")
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_0"]}</span>', unsafe_allow_html=True)
        st.write("Upload the Layer 1 JSON when you are ready.")
        if st.button("Start Quick Pass", type="primary"):
            st.session_state.project["step"] = 1
            touch()
            st.rerun()

    elif step == 1:
        st.markdown("## Step 2 — Load Layer 1 Context")
        revisit_warning("quick", 1)
        quote_box(
            "What to do here",
            "Upload the JSON produced by your team in Layer 1. The app will ingest the lecture context, surface the strongest direction, and let you confirm your starting point without redoing the earlier extraction work."
        )
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_1"]}</span>', unsafe_allow_html=True)
        layer1_file = st.file_uploader("Upload Layer 1 JSON", type=["json"], key="layer1_json")
        if layer1_file and st.button("Load Layer 1 context", type="primary"):
            data = json.load(layer1_file)
            parse_layer1_json(data)
            st.session_state.project["step"] = 2
            st.rerun()

        if st.session_state.project["layer1_loaded"]:
            st.markdown("### Layer 1 summary")
            st.write(ans("layer1_materials_summary"))
            st.markdown("**Top legal arguments already found**")
            for i, item in enumerate(ans("layer1_legal_arguments", []), 1):
                if isinstance(item, dict):
                    st.markdown(f"{i}. {item.get('argument') or item.get('title') or str(item)}")
                else:
                    st.markdown(f"{i}. {item}")
            st.markdown("**Suggested starting direction**")
            st.write(ans("layer1_best_direction_title") or "No single strongest direction stored yet.")
            if ans("layer1_best_direction_reason"):
                st.caption(ans("layer1_best_direction_reason"))

    elif step == 2:
        st.markdown("## Step 3 — Start from This")
        revisit_warning("quick", 2)
        quote_box(
            "What to do here",
            "The app now suggests a starting point based on Layer 1. You do not need to overthink this. Accept it, slightly edit it, or replace it completely. This is just the starting point of your paper."
        )
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_2"]}</span>', unsafe_allow_html=True)

        suggested = ans("layer1_best_direction_title") or "Suggested starting direction not found in Layer 1."
        st.markdown("### Suggested starting point")
        st.info(suggested)

        st.markdown("### Choose what to do")
        choice = st.radio(
            "Starting point action",
            ["Accept as is", "Slightly edit it", "Replace it completely"],
            index=0,
        )

        edit_text = ""
        if choice == "Slightly edit it":
            edit_text = st.text_area("Edit the starting point", value=suggested, height=120)
        elif choice == "Replace it completely":
            edit_text = st.text_area("Write your own starting point", value=ans("quick_selected_point_user_edit", ""), height=120)

        additional = st.text_area(
            "Optional: Is there anything else you want the app to keep in mind before we continue?",
            value=ans("quick_extra_consideration", ""),
            height=90,
        )

        if st.button("Continue from this starting point", type="primary"):
            final_point = suggested
            if choice in ["Slightly edit it", "Replace it completely"]:
                final_point = edit_text.strip() or suggested
            set_ans("quick_selected_point", suggested)
            set_ans("quick_selected_point_user_edit", final_point)
            set_ans("quick_extra_consideration", additional)
            st.session_state.project["step"] = 3
            st.rerun()

    elif step == 3:
        st.markdown("## Step 4 — Write Your Core Idea")
        revisit_warning("quick", 3)
        quote_box(
            "What to do here",
            "This is the most important step in Quick Pass. In 3–5 sentences, explain your paper idea in your own words. Do not worry about structure, grammar, or completeness. Just explain what you want to say."
        )
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_3"]}</span>', unsafe_allow_html=True)

        core_idea = st.text_area(
            "Write your core idea",
            value=ans("quick_core_idea", ""),
            height=180,
            placeholder="Write in your own words. Keep moving. Do not edit too much.",
        )
        st.markdown("### Optional quick signals")
        st.caption("Answer only if helpful.")
        goal_signal = st.text_area(
            "What result or conclusion do you want the paper to reach?",
            value=ans("quick_goal_signal", ""),
            height=90,
        )
        weak_point = st.text_area(
            "What part of your idea feels weakest right now?",
            value=ans("quick_weak_point", ""),
            height=90,
        )

        if st.button("Build the quick writing starter", type="primary"):
            set_ans("quick_core_idea", core_idea)
            set_ans("quick_goal_signal", goal_signal)
            set_ans("quick_weak_point", weak_point)

            fallback = {
                "result_summary": "A workable writing starter has been built from the Layer 1 context and the writer’s own explanation.",
                "working_title": ans("layer1_best_direction_title") or "Working paper title",
                "working_question": "What should this paper prove or clarify based on the writer’s core idea?",
                "outline": [
                    "Introduction and legal problem",
                    "Legal framework or doctrine",
                    "Main legal argument",
                    "What follows from that argument",
                    "Conclusion",
                ],
            }
            system = """
You are helping a writer move fast. Use the Layer 1 context and the writer's own words.
Return JSON with:
result_summary
working_title
working_question
outline
Do not invent a new argument. Push forward what is already there.
"""
            user = f"""
Layer 1 summary: {ans("layer1_materials_summary")}
Suggested starting point: {ans("quick_selected_point_user_edit") or ans("quick_selected_point")}
Writer's core idea: {core_idea}
Desired result: {goal_signal}
Weak point: {weak_point}
Extra consideration: {ans("quick_extra_consideration","")}
"""
            with st.spinner("Building the quick starter..."):
                data = call_model_json("quick_core_idea", system, user, fallback)

            set_ans("quick_result_summary", data.get("result_summary"))
            set_ans("quick_working_title", data.get("working_title"))
            set_ans("quick_working_question", data.get("working_question"))
            set_ans("quick_outline", data.get("outline", []))
            st.session_state.project["step"] = 4
            st.rerun()

        if ans("quick_result_summary"):
            st.markdown("### Current quick starter")
            st.write(ans("quick_result_summary"))
            st.write(f"**Working title**: {ans('quick_working_title')}")
            st.write(f"**Working question**: {ans('quick_working_question')}")

    elif step == 4:
        st.markdown("## Step 5 — Quick Writing Starter")
        revisit_warning("quick", 4)
        quote_box(
            "What to do here",
            "This step gives you a rough but usable writing starter: an abstract seed, opening options, and section cues. The point is not to perfect the paper. The point is to help you start writing now."
        )
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_4"]}</span>', unsafe_allow_html=True)

        if st.button("Create quick writing starter", type="primary"):
            outline = ans("quick_outline", [])
            fallback = {
                "abstract_seed": "This article examines a legal issue surfaced in the lecture and clarifies the legal position it takes.",
                "opening_options": [
                    "Start with the legal problem directly.",
                    "Start with the doctrinal tension already visible in the lecture.",
                    "Start with the consequence your paper wants to show.",
                ],
                "section_cues": {x: f"What do you want to say in '{x}' in your own words?" for x in outline},
                "write_now_prompt": "Write one section now in your own words. Do not edit yet. Keep going.",
            }
            system = """
Create a rough writing starter from the existing context.
Return JSON with:
abstract_seed
opening_options
section_cues
write_now_prompt
This is Quick Pass. Keep it light and useful.
"""
            user = f"""
Layer 1 context summary: {ans("layer1_materials_summary")}
Chosen starting point: {ans("quick_selected_point_user_edit") or ans("quick_selected_point")}
Writer's core idea: {ans("quick_core_idea")}
Current outline: {ans("quick_outline", [])}
"""
            with st.spinner("Creating the quick writing starter..."):
                data = call_model_json("quick_writing_starter", system, user, fallback)
            set_ans("quick_writing_package", data)
            st.session_state.project["step"] = 5
            st.rerun()

        if ans("quick_writing_package"):
            wp = ans("quick_writing_package")
            st.markdown("### Quick writing starter")
            st.write("**Abstract seed**")
            st.write(wp.get("abstract_seed", ""))
            st.write("**Opening options**")
            for item in wp.get("opening_options", []):
                st.markdown(f"- {item}")
            st.write("**Section cues**")
            for k, v in wp.get("section_cues", {}).items():
                st.markdown(f"**{k}** — {v}")

    elif step == 5:
        st.markdown("## Step 6 — Write Now & Export")
        quote_box(
            "What to do here",
            "This is the end of Quick Pass. You now have enough to start writing. Do not edit first. Write first. Export your files, then draft one section in your own words."
        )
        st.markdown(f'<span class="req">Required</span><span class="opt">Time: {TIME_EST["quick_5"]}</span>', unsafe_allow_html=True)

        if st.session_state.project["flags"]:
            st.markdown("### Carry-forward flags")
            for f in st.session_state.project["flags"]:
                st.markdown(f'<span class="flag">{f}</span>', unsafe_allow_html=True)

        wp = ans("quick_writing_package") or {}
        if wp:
            st.info(wp.get("write_now_prompt", "Write one section now in your own words. Do not edit yet."))

        st.markdown("### Exports")
        st.caption("Export one file for people and one file for the system.")
        st.download_button(
            "Download human-readable pre-writing kit (.docx)",
            data=make_human_export(),
            file_name=f"pre_writing_kit_{APP_VERSION}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
        st.download_button(
            "Download machine-readable checkpoint (.json)",
            data=make_machine_export(),
            file_name=f"checkpoint_{APP_VERSION}.json",
            mime="application/json",
        )

        st.markdown("### What to do next")
        st.write("1. Open the human-readable pre-writing kit.")
        st.write("2. Read it once without editing.")
        st.write("3. Write one section in your own words.")
        st.write("4. Keep writing before refining.")
        st.write("5. Return to Full Pass only if you want to make the paper stronger.")

        if st.button("Move to Full Pass"):
            st.session_state.project["phase"] = "full"
            st.session_state.project["step"] = 0
            touch()
            st.rerun()

# -----------------------------------
# FULL PASS
# -----------------------------------
else:
    if step == 0:
        st.markdown("## Full Pass — Step 1 — Verify Authorities")
        revisit_warning("full", 0)
        quote_box(
            "What to do here",
            "Full Pass begins only after Quick Pass. This first step shows the authorities identified in Layer 1. Confirm what belongs, remove what does not, and add anything missing."
        )
        st.markdown(f'<span class="req">Required for Full Pass</span><span class="opt">Time: {TIME_EST["full_0"]}</span>', unsafe_allow_html=True)

        authorities = ans("layer1_authorities", [])
        confirmed, removals = [], []
        additions = st.text_area("Add any missing authority, case, law, or rule", value=ans("full_authority_additions", ""), height=90)

        st.markdown("### Authorities from Layer 1")
        if authorities:
            for i, item in enumerate(authorities, 1):
                label = item
                if isinstance(item, dict):
                    pieces = []
                    if item.get("name"):
                        pieces.append(item["name"])
                    if item.get("type"):
                        pieces.append(f"[{item['type']}]")
                    if item.get("verified_link"):
                        pieces.append(item["verified_link"])
                    label = " — ".join(pieces) if pieces else str(item)
                keep = st.checkbox(f"Keep {i}. {label}", value=True, key=f"auth_keep_{i}")
                if keep:
                    confirmed.append(item)
                else:
                    removals.append(item)
        else:
            st.caption("No authorities were loaded from Layer 1.")

        if st.button("Confirm authorities", type="primary"):
            set_ans("full_verified_authorities", confirmed)
            set_ans("full_authority_removals", removals)
            set_ans("full_authority_additions", additions)
            st.session_state.project["step"] = 1
            st.rerun()

    elif step == 1:
        st.markdown("## Full Pass — Step 2 — Tighten the Claim")
        revisit_warning("full", 1)
        quote_box(
            "What to do here",
            "Now that you already have a starter, rewrite the one claim your paper must prove. Keep it in one sentence."
        )
        st.markdown(f'<span class="req">Required for Full Pass</span><span class="opt">Time: {TIME_EST["full_1"]}</span>', unsafe_allow_html=True)

        refined_claim = st.text_area(
            "What is the one claim your paper must prove?",
            value=ans("full_refined_claim", ""),
            height=100,
        )

        if st.button("Tighten claim", type="primary"):
            set_ans("full_refined_claim", refined_claim)
            st.session_state.project["step"] = 2
            st.rerun()

    elif step == 2:
        st.markdown("## Full Pass — Step 3 — Strengthen Support")
        revisit_warning("full", 2)
        quote_box(
            "What to do here",
            "This step helps identify where your argument still needs stronger support. Use it to name the weakest supported part of the paper."
        )
        st.markdown(f'<span class="req">Required for Full Pass</span><span class="opt">Time: {TIME_EST["full_2"]}</span>', unsafe_allow_html=True)

        support_need = st.text_area(
            "What part of the paper still needs stronger support?",
            value=ans("full_support_needs", ""),
            height=110,
        )

        if st.button("Strengthen support", type="primary"):
            set_ans("full_support_needs", support_need)
            fallback = {
                "support_summary": "The paper needs stronger support in the area identified by the writer.",
                "new_flags": [],
            }
            system = """
Strengthen support for an existing paper starter.
Return JSON with:
support_summary
new_flags
"""
            user = f"""
Refined claim: {ans("full_refined_claim")}
Support need: {support_need}
Verified authorities: {ans("full_verified_authorities", [])}
Added authorities: {ans("full_authority_additions", "")}
"""
            with st.spinner("Strengthening support..."):
                data = call_model_json("full_strengthen_support", system, user, fallback)
            set_ans("full_support_summary", data.get("support_summary"))
            for f in data.get("new_flags", []):
                add_flag(f)
            st.session_state.project["step"] = 3
            st.rerun()

        if ans("full_support_summary"):
            st.write(ans("full_support_summary"))

    elif step == 3:
        st.markdown("## Full Pass — Step 4 — Improve Writing Pack")
        revisit_warning("full", 3)
        quote_box(
            "What to do here",
            "This step improves the writing package you already have. It should make it easier to keep writing, not restart the whole process."
        )
        st.markdown(f'<span class="req">Required for Full Pass</span><span class="opt">Time: {TIME_EST["full_3"]}</span>', unsafe_allow_html=True)

        improve_note = st.text_area(
            "What part of the writing package do you want improved most?",
            value=ans("full_improve_note", ""),
            height=100,
        )

        if st.button("Improve writing pack", type="primary"):
            set_ans("full_improve_note", improve_note)
            fallback = {
                "writing_summary": "The writing package has been improved for clearer drafting.",
                "improved_writing_pack": {
                    "extra_opening_options": ["Start with the sharpest legal conflict first."],
                    "extra_section_prompt": "In your own words, explain why this section matters to the paper’s main claim.",
                }
            }
            system = """
Improve an existing writing pack after quick pass.
Return JSON with:
writing_summary
improved_writing_pack
"""
            user = f"""
Current quick writing package: {ans("quick_writing_package")}
Refined claim: {ans("full_refined_claim")}
Support summary: {ans("full_support_summary")}
Improvement requested: {improve_note}
"""
            with st.spinner("Improving writing pack..."):
                data = call_model_json("full_improve_writing_pack", system, user, fallback)
            set_ans("full_improved_writing_summary", data.get("writing_summary"))
            set_ans("full_improved_writing_pack", data.get("improved_writing_pack"))
            st.session_state.project["step"] = 4
            st.rerun()

    elif step == 4:
        st.markdown("## Full Pass — Step 5 — Export Refined Pack")
        quote_box(
            "What to do here",
            "Full Pass is complete. Export the updated files and continue writing. The point of this stage was to strengthen what already existed, not to stop momentum."
        )
        st.markdown(f'<span class="req">Required for Full Pass</span><span class="opt">Time: {TIME_EST["full_4"]}</span>', unsafe_allow_html=True)

        if ans("full_improved_writing_summary"):
            st.write(ans("full_improved_writing_summary"))
        if st.session_state.project["flags"]:
            st.markdown("### Carry-forward flags")
            for f in st.session_state.project["flags"]:
                st.markdown(f'<span class="flag">{f}</span>', unsafe_allow_html=True)

        st.download_button(
            "Download updated human-readable pre-writing kit (.docx)",
            data=make_human_export(),
            file_name=f"pre_writing_kit_{APP_VERSION}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
        )
        st.download_button(
            "Download updated machine-readable checkpoint (.json)",
            data=make_machine_export(),
            file_name=f"checkpoint_{APP_VERSION}.json",
            mime="application/json",
        )

        st.markdown("### What to do next")
        st.write("1. Open the updated pre-writing kit.")
        st.write("2. Keep writing in your own words.")
        st.write("3. Use Full Pass changes only to strengthen, not to restart.")
