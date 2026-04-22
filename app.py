import os
import io
import json
import re
import datetime as dt
from typing import Any, Dict, List, Tuple

import streamlit as st
import networkx as nx
import plotly.graph_objects as go

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

try:
    from pptx import Presentation
except Exception:
    Presentation = None

APP_NAME = "Article Development Workspace"
APP_VERSION = "v0.6.0"
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
STEP_ORDER = [
    "welcome",
    "intake",
    "fit",
    "argument",
    "plan",
    "sources",
    "launch",
    "export",
]
STEP_TITLES = {
    "welcome": "Step 1 · How this workspace works",
    "intake": "Step 2 · Materials and starting point",
    "fit": "Step 3 · Publication fit",
    "argument": "Step 4 · Main argument",
    "plan": "Step 5 · Research plan",
    "sources": "Step 6 · Sources and literature",
    "launch": "Step 7 · Writing launch",
    "export": "Step 8 · Export and next iteration",
}
STEP_SHORT = {
    "welcome": "Welcome",
    "intake": "Materials",
    "fit": "Fit",
    "argument": "Argument",
    "plan": "Plan",
    "sources": "Sources",
    "launch": "Launch",
    "export": "Export",
}
MODULE_VERSIONS = {
    "welcome": "v0.6.0",
    "intake": "v0.6.0",
    "fit": "v0.6.0",
    "argument": "v0.6.0",
    "plan": "v0.6.0",
    "sources": "v0.6.0",
    "launch": "v0.6.0",
    "export": "v0.6.0",
}
CHANGELOG = {
    "v0.6.0": [
        "Restored rich multi-stage workspace with OpenAI integration in core generation stages.",
        "Added top progress navigation, plain-language labels, and per-stage Lean/Deep toggles.",
        "Added journal recommendation and policy context stage after direction becomes clear.",
        "Improved scoping questions and integrated cumulative testing sidebar export.",
    ],
    "v0.5.0": [
        "Richer prototype with governance layer, intake, adaptive modules, checkpointing, and feedback export.",
    ],
}

LAW_SUGGESTIONS = {
    "data privacy act": [
        ("Republic Act No. 10173 (Data Privacy Act of 2012)", "Official Gazette", "https://www.officialgazette.gov.ph/2012/08/15/republic-act-no-10173/"),
        ("Republic Act No. 10173 (mirror)", "Lawphil", "https://lawphil.net/statutes/repacts/ra2012/ra_10173_2012.html"),
    ],
    "anti-red tape": [
        ("Republic Act No. 11032 (Ease of Doing Business and Efficient Government Service Delivery Act of 2018)", "Official Gazette", "https://www.officialgazette.gov.ph/2018/05/28/republic-act-no-11032/"),
        ("Republic Act No. 11032 (mirror)", "Lawphil", "https://lawphil.net/statutes/repacts/ra2018/ra_11032_2018.html"),
    ],
    "revised penal code": [
        ("Act No. 3815 (Revised Penal Code)", "Official Gazette", "https://www.officialgazette.gov.ph/1930/12/08/act-no-3815/"),
        ("Act No. 3815 (mirror)", "Lawphil", "https://lawphil.net/statutes/acts/act_3815_1930.html"),
    ],
    "rules of court": [
        ("Rules of Court", "Supreme Court of the Philippines", "https://sc.judiciary.gov.ph/rules-of-court/"),
        ("Rules of Court (mirror)", "ChanRobles", "https://chanrobles.com/rulesofcourt.htm"),
    ],
    "constitution": [
        ("1987 Constitution of the Republic of the Philippines", "Official Gazette", "https://www.officialgazette.gov.ph/constitutions/1987-constitution/"),
        ("1987 Constitution (mirror)", "ChanRobles", "https://www.chanrobles.com/article1.htm"),
    ],
    "anti-graft": [
        ("Republic Act No. 3019 (Anti-Graft and Corrupt Practices Act)", "Official Gazette", "https://www.officialgazette.gov.ph/1960/08/17/republic-act-no-3019/"),
        ("Republic Act No. 3019 (mirror)", "Lawphil", "https://lawphil.net/statutes/repacts/ra1960/ra_3019_1960.html"),
    ],
}

OPENAI_JSON_SYSTEM = """
You are assisting inside a proprietary article development workspace for legal scholarship.
You are not the author. Do not fabricate authorities, statutes, cases, journals, CFPs, or policies.
When specific authorities or journal policies are uncertain, say so explicitly and recommend verification.
Return compact JSON only.
""".strip()

CSS = """
<style>
:root {
  --ink: #1a1612;
  --paper: #f5f0e8;
  --cream: #ede8dc;
  --rule: #c8b99a;
  --accent: #8b1a1a;
  --accent-light: #b84040;
  --muted: #6f6458;
  --success: #2d6a4f;
}
.stApp {background: var(--paper);} 
.block-container {padding-top: 1.1rem; max-width: 1100px;}
.top-progress {position: sticky; top: 0; z-index: 99; background: var(--paper); padding: 0.4rem 0 0.9rem 0; border-bottom: 1px solid var(--rule);}
.top-progress-row {display: grid; grid-template-columns: repeat(8, 1fr); gap: 8px;}
.step-chip {border: 1px solid var(--rule); border-radius: 10px; padding: 10px 8px; text-align: center; font-size: 0.78rem; background: white; color: var(--muted);}
.step-chip.active {background: var(--ink); color: #fff; border-color: var(--ink);} 
.step-chip.done {background: #e8f2ec; border-color: var(--success); color: var(--success);} 
.progress-track {margin-top: 10px; height: 8px; background: #ddd3c3; border-radius: 999px; overflow: hidden;}
.progress-fill {height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-light));}
.section-card {background: rgba(255,255,255,0.78); border: 1px solid var(--rule); padding: 18px; border-radius: 14px; margin-bottom: 18px;}
.helper {font-size: 0.92rem; color: var(--muted); margin: 0.15rem 0 0.55rem 0;}
.mini {font-size: 0.82rem; color: var(--muted);}
.kicker {font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent); margin-bottom: 0.2rem;}
.trust-strip {border-left: 4px solid var(--accent); background: #fffaf7; padding: 14px 16px; border-radius: 10px; margin-bottom: 16px;}
.output-box {background: white; border: 1px solid var(--rule); border-left: 4px solid var(--accent); padding: 16px; border-radius: 10px; margin-top: 12px;}
</style>
"""


def get_openai_api_key() -> str:
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.getenv("OPENAI_API_KEY", "")


def get_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("The openai package is not installed.")
    key = get_openai_api_key()
    if not key:
        raise RuntimeError("OpenAI API key not found. Add OPENAI_API_KEY to .streamlit/secrets.toml or your environment.")
    return OpenAI(api_key=key)


def call_openai_json(task: str, payload: Dict[str, Any], model: str = DEFAULT_MODEL) -> Dict[str, Any]:
    client = get_client()
    resp = client.responses.create(
        model=model,
        input=[
            {"role": "system", "content": OPENAI_JSON_SYSTEM},
            {"role": "user", "content": json.dumps({"task": task, "payload": payload}, ensure_ascii=False)}
        ],
        text={"format": {"type": "json_object"}},
    )
    return json.loads(resp.output_text)


def now_iso() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def init_state():
    if "project" not in st.session_state:
        st.session_state.project = {
            "version": APP_VERSION,
            "created_at": now_iso(),
            "last_updated": now_iso(),
            "current_step": "welcome",
            "mode": "Strict",
            "stage_depth": {k: "Lean" for k in STEP_ORDER},
            "answers": {},
            "outputs": {},
            "feedback": {},
            "governance_log": [],
            "ai_logs": [],
            "module_versions": {k: MODULE_VERSIONS[k] for k in MODULE_VERSIONS},
            "module_history": [],
            "journal_context": {},
            "materials": [],
            "checkpoint_loaded": False,
        }
    if "loaded_checkpoint" not in st.session_state:
        st.session_state.loaded_checkpoint = None


def mark_module_touch(step: str, note: str = ""):
    st.session_state.project["last_updated"] = now_iso()
    st.session_state.project["module_history"].append({
        "step": step,
        "time": now_iso(),
        "version": MODULE_VERSIONS.get(step, APP_VERSION),
        "note": note,
    })


def set_step(step: str):
    st.session_state.project["current_step"] = step
    mark_module_touch(step, "entered")


def progress_index(step: str) -> int:
    return STEP_ORDER.index(step) + 1


def render_progress():
    step = st.session_state.project["current_step"]
    idx = progress_index(step)
    pct = int((idx - 1) / (len(STEP_ORDER) - 1) * 100)
    html = ["<div class='top-progress'>", "<div class='top-progress-row'>"]
    for s in STEP_ORDER:
        cls = "step-chip"
        if progress_index(s) < idx:
            cls += " done"
        if s == step:
            cls += " active"
        html.append(f"<div class='{cls}'>{STEP_SHORT[s]}</div>")
    html.append("</div>")
    html.append(f"<div class='progress-track'><div class='progress-fill' style='width:{pct}%'></div></div>")
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def save_answer(key: str, value: Any):
    st.session_state.project["answers"][key] = value
    st.session_state.project["last_updated"] = now_iso()


def save_output(key: str, value: Any, action: str):
    st.session_state.project["outputs"][key] = value
    st.session_state.project["ai_logs"].append({
        "time": now_iso(),
        "step": st.session_state.project["current_step"],
        "action": action,
        "version": APP_VERSION,
    })
    st.session_state.project["last_updated"] = now_iso()


def blank_selectbox(label: str, options: List[str], key: str, help_text: str = "") -> str:
    opts = [""] + options
    if help_text:
        st.markdown(f"<div class='helper'>{help_text}</div>", unsafe_allow_html=True)
    val = st.selectbox(label, opts, key=key, format_func=lambda x: "Select one" if x == "" else x)
    return val


def parse_uploaded_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    data = uploaded_file.getvalue()
    if name.endswith(".txt") or name.endswith(".md"):
        try:
            return data.decode("utf-8")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    if name.endswith(".pdf") and PdfReader:
        reader = PdfReader(io.BytesIO(data))
        text = []
        for p in reader.pages[:25]:
            try:
                text.append(p.extract_text() or "")
            except Exception:
                pass
        return "\n".join(text)
    if name.endswith(".docx") and docx:
        d = docx.Document(io.BytesIO(data))
        return "\n".join(p.text for p in d.paragraphs)
    if name.endswith(".pptx") and Presentation:
        prs = Presentation(io.BytesIO(data))
        text = []
        for slide in prs.slides[:20]:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return "\n".join(text)
    return ""


def material_summary_block(materials: List[Dict[str, Any]]) -> str:
    chunks = []
    for m in materials:
        excerpt = (m.get("text") or "")[:1800]
        chunks.append(f"FILE: {m['name']}\nTYPE: {m['kind']}\nEXCERPT:\n{excerpt}")
    return "\n\n".join(chunks)


def suggest_law_links(raw_terms: str) -> List[Dict[str, str]]:
    suggestions = []
    terms = [t.strip() for t in re.split(r"[,;\n]", raw_terms.lower()) if t.strip()]
    seen = set()
    for term in terms:
        for key, entries in LAW_SUGGESTIONS.items():
            if key in term or term in key:
                for title, source, url in entries:
                    tag = f"{title}|{url}"
                    if tag not in seen:
                        suggestions.append({"term": term, "title": title, "source": source, "url": url})
                        seen.add(tag)
    return suggestions


def mock_intake_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    text = payload.get("materials_text", "")
    direction = payload.get("direction_hint") or ""
    return {
        "inventory": payload.get("inventory", []),
        "route": "Transcript-led" if "transcript" in text.lower() else "Mixed",
        "themes": [
            {"label": "Possible core issue", "quote": (text[:180] or "No quote found")[:180], "source": payload.get("inventory", [{}])[0].get("name", "materials") if payload.get("inventory") else "materials"},
            {"label": "Possible tension", "quote": "No clear quote surfaced in mock mode.", "source": "Mock"},
        ],
        "candidate_directions": [
            "A doctrinal article centered on a specific legal ambiguity.",
            "A reform-oriented article identifying a practical legal gap.",
            f"A direction aligned with your hint: {direction}" if direction else "A comparative or context-setting article if stronger sources emerge.",
        ],
        "notes": [
            "Mock mode does not verify quotations or source relationships.",
            "Use this as a flow test, not as a final scholarly extraction."
        ]
    }


def run_intake_analysis() -> Dict[str, Any]:
    project = st.session_state.project
    payload = {
        "inventory": [{"name": m["name"], "kind": m["kind"]} for m in project["materials"]],
        "materials_text": material_summary_block(project["materials"]),
        "priority_material": project["answers"].get("priority_material", ""),
        "caution_material": project["answers"].get("caution_material", ""),
        "direction_hint": project["answers"].get("initial_direction", ""),
        "writer_note": project["answers"].get("intake_note", ""),
    }
    if project["answers"].get("provider") == "OpenAI":
        task = "intake_analysis"
        prompt_payload = {
            **payload,
            "instructions": {
                "return_keys": ["inventory", "route", "themes", "candidate_directions", "notes"],
                "theme_rule": "Each theme must include label, quote, and source. If no quote is available, say so clearly.",
                "grounding_rule": "Do not fabricate quotes. Use only uploaded material excerpts."
            }
        }
        try:
            return call_openai_json(task, prompt_payload)
        except Exception as e:
            return {"inventory": payload["inventory"], "route": "Fallback", "themes": [], "candidate_directions": [], "notes": [str(e)]}
    return mock_intake_analysis(payload)


def run_publication_fit() -> Dict[str, Any]:
    project = st.session_state.project
    payload = {
        "topic": project["answers"].get("topic", ""),
        "jurisdiction": project["answers"].get("jurisdiction", "Philippines"),
        "main_argument": project["answers"].get("main_argument", ""),
        "article_goal": project["answers"].get("article_goal", ""),
        "cfp_context": project["answers"].get("cfp_context", ""),
        "lean_or_deep": project["stage_depth"].get("fit", "Lean"),
    }
    if project["answers"].get("provider") == "OpenAI":
        task = "journal_and_policy_match"
        prompt_payload = {
            **payload,
            "instructions": {
                "return_keys": ["journal_options", "recommended_mode", "policy_notes", "cfp_notes"],
                "journal_options_schema": {"name": "", "why_fit": "", "policy_context": "", "caution": ""},
                "verification_rule": "If the journal AI policy may have changed, explicitly say verification needed. Do not invent current CFP details."
            }
        }
        try:
            return call_openai_json(task, prompt_payload)
        except Exception as e:
            return {"journal_options": [], "recommended_mode": "Strict", "policy_notes": [str(e)], "cfp_notes": []}
    return {
        "journal_options": [
            {"name": "AI & Society", "why_fit": "Useful if the project emphasizes governance, ethics, and social implications.", "policy_context": "Likely disclosure-friendly, but verify current policy.", "caution": "Check whether the article is doctrinal enough for the outlet."},
            {"name": "AI & Law", "why_fit": "Useful if the project squarely addresses law, institutions, and AI-related legal questions.", "policy_context": "Likely allows some disclosed assistance, but verify.", "caution": "The article may need clearer legal framing."},
            {"name": "A Philippine or regional law journal", "why_fit": "Useful if the article is highly local and practice-facing.", "policy_context": "Policies can be stricter or less explicit; verify directly.", "caution": "Local doctrinal fit may be strong, but AI policies vary widely."},
        ],
        "recommended_mode": "Strict",
        "policy_notes": ["Start in Strict mode unless the target journal clearly permits more assistance with disclosure."],
        "cfp_notes": ["No CFP verification in mock mode."]
    }


def run_argument_shaper() -> Dict[str, Any]:
    project = st.session_state.project
    payload = {
        "intake_analysis": project["outputs"].get("intake_analysis", {}),
        "topic": project["answers"].get("topic", ""),
        "what_to_argue": project["answers"].get("main_argument", ""),
        "article_goal": project["answers"].get("article_goal", ""),
        "scoping": project["answers"].get("scoping", {}),
        "depth": project["stage_depth"].get("argument", "Lean"),
    }
    if project["answers"].get("provider") == "OpenAI":
        task = "argument_and_question_shaping"
        prompt_payload = {
            **payload,
            "instructions": {
                "return_keys": ["summary", "question_options", "iv_candidates", "dv_candidates", "classification", "followups"],
                "classification_rule": "Return Strong, Moderate, or Weak based on clarity, arguability, scope, and contribution signal."
            }
        }
        try:
            return call_openai_json(task, prompt_payload)
        except Exception as e:
            return {"summary": str(e), "question_options": [], "iv_candidates": [], "dv_candidates": [], "classification": "Moderate", "followups": []}
    return {
        "summary": "The project appears to center on a concrete legal issue that can be sharpened into one main research question.",
        "question_options": [
            "How should the identified legal issue be analyzed within the selected jurisdiction?",
            "To what extent does the current legal framework adequately address the problem identified in the materials?",
            "What reform or clarification would best resolve the tension identified in the materials?",
        ],
        "iv_candidates": ["the legal rule or framework under examination", "institutional or doctrinal setting"],
        "dv_candidates": ["the legal consequence or effect being evaluated", "the rights, duties, or outcomes produced"],
        "classification": "Moderate",
        "followups": [
            "Clarify what exactly is being examined on the law side of the question.",
            "Clarify the legal or practical consequence you want to assess.",
        ],
    }


def run_sources_and_literature() -> Dict[str, Any]:
    project = st.session_state.project
    payload = {
        "topic": project["answers"].get("topic", ""),
        "question": project["answers"].get("confirmed_question", "") or project["answers"].get("main_argument", ""),
        "laws_confirmed": project["answers"].get("confirmed_laws", []),
        "sources_known": project["answers"].get("known_sources", ""),
        "depth": project["stage_depth"].get("sources", "Lean"),
    }
    if project["answers"].get("provider") == "OpenAI":
        task = "sources_and_literature_map"
        prompt_payload = {
            **payload,
            "instructions": {
                "return_keys": ["themes", "legal_sources", "gap_notes", "graph_nodes", "graph_edges"],
                "graph_rule": "Each node needs id, label, cluster; each edge needs source, target, relation."
            }
        }
        try:
            return call_openai_json(task, prompt_payload)
        except Exception as e:
            return {"themes": [], "legal_sources": [], "gap_notes": [str(e)], "graph_nodes": [], "graph_edges": []}
    return {
        "themes": [
            {"title": "Core doctrinal issue", "what_it_covers": "The main legal problem or rule that anchors the article."},
            {"title": "Institutional or policy tension", "what_it_covers": "The practical or structural issue that makes the article worth writing."},
            {"title": "Comparative or forward-looking implication", "what_it_covers": "Where the article could move beyond pure description."},
        ],
        "legal_sources": payload["laws_confirmed"],
        "gap_notes": ["Use this map as a planning guide. Confirm every authority independently."],
        "graph_nodes": [
            {"id": "n1", "label": "Core issue", "cluster": "Theme 1"},
            {"id": "n2", "label": "Policy tension", "cluster": "Theme 2"},
            {"id": "n3", "label": "Comparative angle", "cluster": "Theme 3"},
        ],
        "graph_edges": [
            {"source": "n1", "target": "n2", "relation": "supports"},
            {"source": "n2", "target": "n3", "relation": "extends"},
        ],
    }


def run_launch_builder() -> Dict[str, Any]:
    project = st.session_state.project
    payload = {
        "topic": project["answers"].get("topic", ""),
        "main_argument": project["answers"].get("main_argument", ""),
        "confirmed_question": project["answers"].get("confirmed_question", ""),
        "ivs": project["answers"].get("selected_ivs", []),
        "dvs": project["answers"].get("selected_dvs", []),
        "scope": project["answers"].get("scoping", {}),
        "journal_fit": project["outputs"].get("journal_fit", {}),
        "literature": project["outputs"].get("literature_map", {}),
    }
    if project["answers"].get("provider") == "OpenAI":
        task = "writing_launch_pack"
        prompt_payload = {
            **payload,
            "instructions": {
                "return_keys": ["project_brief", "section_map", "writing_pack", "review_questions"],
                "warning_rule": "No final article prose. Structure and prompts only."
            }
        }
        try:
            return call_openai_json(task, prompt_payload)
        except Exception as e:
            return {"project_brief": {"warning": str(e)}, "section_map": [], "writing_pack": {}, "review_questions": []}
    return {
        "project_brief": {
            "topic": payload["topic"],
            "main_argument": payload["main_argument"],
            "confirmed_question": payload["confirmed_question"],
            "scope": payload["scope"],
        },
        "section_map": [
            {"section": "Introduction", "purpose": "Frame the legal problem and state the article's question."},
            {"section": "Legal background", "purpose": "Explain the key rules, authorities, or legal context."},
            {"section": "Analysis", "purpose": "Develop the core argument and answer the question."},
            {"section": "Implications", "purpose": "Explain why the answer matters for law, practice, or policy."},
        ],
        "writing_pack": {
            "abstract_fields": ["Context", "Question", "Approach", "Claim", "Why it matters"],
            "starter_prompts": [
                "What is the sharpest doctrinal or practical problem that opens this article?",
                "What exactly is your answer to the main question?",
                "What should the reader understand by the end that is not obvious at the start?",
            ],
        },
        "review_questions": [
            "Does each section clearly move the argument forward?",
            "Have you personally checked every authority you plan to rely on?",
            "Does the piece still sound like your own thinking?",
        ],
    }


def build_network_figure(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
    if not nodes:
        return None
    G = nx.Graph()
    for node in nodes:
        G.add_node(node["id"], label=node.get("label", node["id"]), cluster=node.get("cluster", "Other"))
    for edge in edges:
        if edge.get("source") in G.nodes and edge.get("target") in G.nodes:
            G.add_edge(edge["source"], edge["target"], relation=edge.get("relation", "related"))
    pos = nx.spring_layout(G, seed=11)
    edge_x, edge_y = [], []
    for a, b in G.edges():
        x0, y0 = pos[a]
        x1, y1 = pos[b]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(width=1, color="#bcae96"), hoverinfo="none")
    node_x, node_y, text, colors = [], [], [], []
    palette = {"Theme 1": "#8b1a1a", "Theme 2": "#2d6a4f", "Theme 3": "#275dad", "Other": "#6f6458"}
    for n, attrs in G.nodes(data=True):
        x, y = pos[n]
        node_x.append(x)
        node_y.append(y)
        text.append(f"{attrs['label']}<br><span style='font-size:10px'>{attrs['cluster']}</span>")
        colors.append(palette.get(attrs.get("cluster", "Other"), "#6f6458"))
    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text", hovertext=text, text=[attrs["label"] for _, attrs in G.nodes(data=True)],
        textposition="top center", marker=dict(size=18, color=colors, line=dict(width=1, color="#fff")), hoverinfo="text"
    )
    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False), plot_bgcolor="#fff", paper_bgcolor="#fff")
    return fig


def refresh_from(step: str):
    start = STEP_ORDER.index(step)
    for later in STEP_ORDER[start+1:]:
        st.session_state.project["outputs"].pop(later + "_cache", None)
    # targeted clears
    mapping = {
        "intake": ["intake_analysis", "journal_fit", "argument_shape", "literature_map", "launch_pack"],
        "fit": ["journal_fit", "launch_pack"],
        "argument": ["argument_shape", "literature_map", "launch_pack"],
        "plan": ["literature_map", "launch_pack"],
        "sources": ["literature_map", "launch_pack"],
        "launch": ["launch_pack"],
    }
    for k in mapping.get(step, []):
        st.session_state.project["outputs"].pop(k, None)
    mark_module_touch(step, "refreshed downstream")


def export_feedback_markdown() -> str:
    p = st.session_state.project
    lines = [f"# {APP_NAME} refinement packet", "", f"Version: {p['version']}", f"Generated: {now_iso()}", ""]
    lines.append("## Current answers")
    lines.append("```json")
    lines.append(json.dumps(p.get("answers", {}), indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    lines.append("## Outputs")
    lines.append("```json")
    lines.append(json.dumps(p.get("outputs", {}), indent=2, ensure_ascii=False))
    lines.append("```")
    lines.append("")
    lines.append("## Test feedback")
    for step, fb in p.get("feedback", {}).items():
        lines.append(f"### {STEP_TITLES.get(step, step)}")
        for k, v in fb.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    return "\n".join(lines)


def record_feedback(step: str, worked: str, confusing: str, too_much: str, missing: str, notes: str):
    st.session_state.project["feedback"][step] = {
        "Worked": worked,
        "Confusing": confusing,
        "Too much": too_much,
        "Missing": missing,
        "Notes": notes,
    }
    st.session_state.project["last_updated"] = now_iso()


def render_testing_sidebar():
    st.sidebar.markdown("---")
    st.sidebar.subheader("Iteration notes")
    step = st.session_state.project["current_step"]
    prior = st.session_state.project["feedback"].get(step, {})
    worked = st.sidebar.text_area("Worked", value=prior.get("Worked", ""), key=f"fb_worked_{step}")
    confusing = st.sidebar.text_area("Confusing", value=prior.get("Confusing", ""), key=f"fb_confusing_{step}")
    too_much = st.sidebar.text_area("Too much", value=prior.get("Too much", ""), key=f"fb_toomuch_{step}")
    missing = st.sidebar.text_area("Missing", value=prior.get("Missing", ""), key=f"fb_missing_{step}")
    notes = st.sidebar.text_area("Notes", value=prior.get("Notes", ""), key=f"fb_notes_{step}")
    if st.sidebar.button("Save notes for this step"):
        record_feedback(step, worked, confusing, too_much, missing, notes)
        st.sidebar.success("Saved")
    packet = export_feedback_markdown()
    st.sidebar.download_button("Export full refinement packet", data=packet, file_name=f"refinement_packet_{APP_VERSION}.md", mime="text/markdown")


def render_governance_strip():
    mode = st.session_state.project["answers"].get("mode_label", "Strict")
    st.markdown(f"<div class='trust-strip'><strong>How this workspace is helping</strong><br>This workspace helps you organize and test your article plan. It is set to <strong>{mode}</strong> mode, which means the platform should help you structure and review your thinking without taking authorship away from you.</div>", unsafe_allow_html=True)


def render_welcome():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Start here</div>", unsafe_allow_html=True)
    st.header("Build your article step by step")
    st.write("This workspace turns a lecture, presentation, or developing idea into a publishable article plan. You stay in control of the argument. The workspace helps you surface the issue, shape the question, map the sources, and prepare to draft.")
    mode = blank_selectbox(
        "How much direct help do you want to start with?",
        ["Strict — structure and review only", "Standard — structure plus stronger suggestions", "Enhanced — more drafting support where journal policy clearly allows it"],
        key="mode_choice",
        help_text="Start in Strict unless you already know the target journal clearly allows more assistance. You can stay light overall and still open a deeper path in specific stages later."
    )
    provider = blank_selectbox(
        "Model connection",
        ["Mock", "OpenAI"],
        key="provider_choice",
        help_text="Use Mock if you want to test the flow only. Use OpenAI when you want richer responses in the intake, publication fit, argument, sources, and launch stages."
    )
    if mode:
        save_answer("mode_label", mode.split(" — ")[0])
    if provider:
        save_answer("provider", provider)
    with st.expander("More information about how this workspace works"):
        st.write("At each stage, the workspace either helps you confirm what is already clear or asks for only the next clarifying details needed to move the article forward. Some stages can be kept light. Other stages can be opened in a deeper mode if you want more guidance. The goal is efficiency without losing your control over the argument.")
        st.write("You can also view how a result was formed, revise the workspace’s interpretation, and export all your testing notes in one file for the next iteration.")
    st.markdown("</div>", unsafe_allow_html=True)
    cols = st.columns([1,1,2])
    if cols[0].button("Continue"):
        set_step("intake")
    if cols[1].button("Load checkpoint"):
        st.session_state.show_checkpoint_loader = True


def render_checkpoint_loader():
    up = st.file_uploader("Load a saved checkpoint (.json)", type=["json"], key="checkpoint_uploader")
    if up is not None:
        try:
            data = json.loads(up.getvalue().decode("utf-8"))
            st.session_state.loaded_checkpoint = data
            st.success("Checkpoint file ready to load.")
            if st.button("Load imported checkpoint now"):
                st.session_state.project = data
                st.session_state.project["version"] = APP_VERSION
                st.session_state.project["checkpoint_loaded"] = True
                st.success("Checkpoint loaded.")
                st.rerun()
        except Exception as e:
            st.error(f"Could not load checkpoint: {e}")


def render_intake():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Materials and context</div>", unsafe_allow_html=True)
    st.header("Tell the workspace what you already have")
    topic = st.text_input("Working topic", value=st.session_state.project["answers"].get("topic", ""))
    st.markdown("<div class='helper'>Use a plain working label. This can change later.</div>", unsafe_allow_html=True)
    jurisdiction = st.text_input("Main jurisdiction", value=st.session_state.project["answers"].get("jurisdiction", "Philippines"))
    st.markdown("<div class='helper'>Name the main legal system or setting you expect the article to focus on.</div>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload materials", type=["pdf", "txt", "md", "docx", "pptx"], accept_multiple_files=True)
    st.markdown("<div class='helper'>For now, use PDF for laws or formal legal texts. You can also upload a transcript, slide deck, notes, or a draft. If you have a bionote or CV and want the workspace to understand your subject-matter background better, include it here.</div>", unsafe_allow_html=True)
    inventory = []
    parsed_materials = []
    if uploaded:
        for f in uploaded:
            text = parse_uploaded_file(f)
            kind = "PDF" if f.name.lower().endswith(".pdf") else ("Transcript / text" if f.name.lower().endswith((".txt", ".md")) else "Document / slides")
            inventory.append({"name": f.name, "kind": kind})
            parsed_materials.append({"name": f.name, "kind": kind, "text": text})
        st.session_state.project["materials"] = parsed_materials
        st.caption(f"Loaded {len(parsed_materials)} file(s).")
    priority_material = st.text_input("Which material best reflects your thinking right now?", value=st.session_state.project["answers"].get("priority_material", ""))
    st.markdown("<div class='helper'>Example: transcript, final slide deck, draft note, or a specific PDF law.</div>", unsafe_allow_html=True)
    caution_material = st.text_input("Is there any material the workspace should treat cautiously?", value=st.session_state.project["answers"].get("caution_material", ""))
    st.markdown("<div class='helper'>Example: old draft, incomplete transcript, speaking notes that no longer reflect your actual view.</div>", unsafe_allow_html=True)
    raw_law_terms = st.text_area("Relevant laws, cases, or doctrines you already have in mind", value=st.session_state.project["answers"].get("raw_law_terms", ""), height=100)
    st.markdown("<div class='helper'>List them in plain language if needed. The workspace will suggest likely source links and ask you to confirm what is actually relevant.</div>", unsafe_allow_html=True)
    suggestions = suggest_law_links(raw_law_terms)
    confirmed_laws = []
    if suggestions:
        st.subheader("Suggested legal materials to confirm")
        for i, s in enumerate(suggestions):
            check = st.checkbox(f"Use: {s['title']} · {s['source']}", key=f"law_confirm_{i}")
            st.markdown(f"[{s['url']}]({s['url']})")
            if check:
                confirmed_laws.append(s)
    initial_direction = st.text_area("What are you hoping this article will become, if you already have a sense?", value=st.session_state.project["answers"].get("initial_direction", ""), height=100)
    st.markdown("<div class='helper'>You can keep this rough. Example: a doctrinal clarification, a reform proposal, or a critique of current practice.</div>", unsafe_allow_html=True)
    intake_note = st.text_area("Anything else the workspace should know before it reads your materials?", value=st.session_state.project["answers"].get("intake_note", ""), height=80)
    depth = blank_selectbox("How much engagement do you want at this stage?", ["Lean", "Deep"], key="intake_depth", help_text="Lean asks for less and tries to move quickly. Deep opens a fuller reading of your materials and more follow-up help.")
    if depth:
        st.session_state.project["stage_depth"]["intake"] = depth
    col1, col2 = st.columns([1,1])
    if col1.button("Read my materials"):
        save_answer("topic", topic)
        save_answer("jurisdiction", jurisdiction)
        save_answer("priority_material", priority_material)
        save_answer("caution_material", caution_material)
        save_answer("raw_law_terms", raw_law_terms)
        save_answer("confirmed_laws", confirmed_laws)
        save_answer("initial_direction", initial_direction)
        save_answer("intake_note", intake_note)
        result = run_intake_analysis()
        save_output("intake_analysis", result, "materials mapping")
    if col2.button("Refresh later stages from here"):
        refresh_from("intake")
        st.success("Later stages cleared for refresh.")
    result = st.session_state.project["outputs"].get("intake_analysis")
    if result:
        st.markdown("<div class='output-box'>", unsafe_allow_html=True)
        st.subheader("What the workspace sees so far")
        st.write(f"**Reading path:** {result.get('route', 'Not set')}" )
        if result.get("themes"):
            st.write("**Grounded themes**")
            for t in result["themes"]:
                st.markdown(f"- **{t.get('label','Theme')}** — “{t.get('quote','No quote found')}” ({t.get('source','source not identified')})")
        if result.get("candidate_directions"):
            st.write("**Possible directions**")
            for d in result["candidate_directions"]:
                st.markdown(f"- {d}")
        if result.get("notes"):
            st.write("**Notes**")
            for n in result["notes"]:
                st.markdown(f"- {n}")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Continue to publication fit"):
            set_step("fit")
    st.markdown("</div>", unsafe_allow_html=True)


def render_fit():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Where this piece could go</div>", unsafe_allow_html=True)
    st.header("Publication fit")
    article_goal = st.text_area("What do you want this article to do?", value=st.session_state.project["answers"].get("article_goal", ""), height=100)
    st.markdown("<div class='helper'>Example: clarify doctrine, challenge a common assumption, propose reform, or build a practical framework.</div>", unsafe_allow_html=True)
    cfp_context = st.text_area("If you know of a call for papers or themed issue, put it here", value=st.session_state.project["answers"].get("cfp_context", ""), height=80)
    st.markdown("<div class='helper'>You do not need to know the target journal yet. The workspace can still suggest likely homes for the article.</div>", unsafe_allow_html=True)
    depth = blank_selectbox("How much engagement do you want at this stage?", ["Lean", "Deep"], key="fit_depth", help_text="Lean gives a fast shortlist. Deep gives a fuller recommendation set and stronger cautions.")
    if depth:
        st.session_state.project["stage_depth"]["fit"] = depth
    c1, c2 = st.columns([1,1])
    if c1.button("Suggest publication paths"):
        save_answer("article_goal", article_goal)
        save_answer("cfp_context", cfp_context)
        result = run_publication_fit()
        save_output("journal_fit", result, "publication fit")
    if c2.button("Refresh later stages from here"):
        refresh_from("fit")
        st.success("Later stages cleared for refresh.")
    result = st.session_state.project["outputs"].get("journal_fit")
    if result:
        st.markdown("<div class='output-box'>", unsafe_allow_html=True)
        st.subheader("Likely publication paths")
        for i, j in enumerate(result.get("journal_options", []), start=1):
            st.markdown(f"**{i}. {j.get('name','Journal')}**")
            st.markdown(f"- Why it may fit: {j.get('why_fit','')}" )
            st.markdown(f"- Policy context: {j.get('policy_context','')}" )
            st.markdown(f"- Caution: {j.get('caution','')}" )
        st.markdown(f"**Recommended working mode:** {result.get('recommended_mode','Strict')}" )
        for note in result.get("policy_notes", []):
            st.markdown(f"- {note}")
        for note in result.get("cfp_notes", []):
            st.markdown(f"- {note}")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Continue to main argument"):
            set_step("argument")
    st.markdown("</div>", unsafe_allow_html=True)


def render_argument():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>What you want to argue</div>", unsafe_allow_html=True)
    st.header("Main argument")
    main_argument = st.text_area("What do you want to argue for this article?", value=st.session_state.project["answers"].get("main_argument", ""), height=140)
    st.markdown("<div class='helper'>State the claim in ordinary language first. You do not need a polished journal sentence yet. Example: current doctrine is unclear in a way that harms due process, or this legal framework should be rethought because it produces a specific problem.</div>", unsafe_allow_html=True)
    if st.checkbox("Show how this stage is being read", key="arg_explain_toggle"):
        st.info("The workspace uses your materials, your publication goal, and your current claim to estimate whether the article direction is already clear, partly clear, or still too broad. If it is already clear, the next stage should ask less. If it is weak, the next stage should ask only for the missing pieces.")
    depth = blank_selectbox("How much engagement do you want at this stage?", ["Lean", "Deep"], key="arg_depth", help_text="Lean helps you get to one usable article direction quickly. Deep opens more alternatives and a stronger check on scope and contribution.")
    if depth:
        st.session_state.project["stage_depth"]["argument"] = depth
    c1, c2 = st.columns([1,1])
    if c1.button("Shape the article question"):
        save_answer("main_argument", main_argument)
        result = run_argument_shaper()
        save_output("argument_shape", result, "argument shaping")
    if c2.button("Refresh later stages from here"):
        refresh_from("argument")
        st.success("Later stages cleared for refresh.")
    result = st.session_state.project["outputs"].get("argument_shape")
    if result:
        st.markdown("<div class='output-box'>", unsafe_allow_html=True)
        st.write(f"**Current read:** {result.get('classification','Moderate')}" )
        st.write(result.get("summary", ""))
        if result.get("question_options"):
            st.write("**Question options**")
            for q in result["question_options"]:
                st.markdown(f"- {q}")
        st.write("**Possible law-side anchors**")
        for iv in result.get("iv_candidates", []):
            st.markdown(f"- {iv}")
        st.write("**Possible consequence-side anchors**")
        for dv in result.get("dv_candidates", []):
            st.markdown(f"- {dv}")
        for f in result.get("followups", []):
            st.markdown(f"- {f}")
        st.markdown("</div>", unsafe_allow_html=True)
        confirmed_question = st.text_area("Which question are you carrying forward right now?", value=st.session_state.project["answers"].get("confirmed_question", ""), height=100)
        st.markdown("<div class='helper'>You may choose one of the suggested questions, revise one, or write your own better version.</div>", unsafe_allow_html=True)
        if st.button("Save this question and continue"):
            save_answer("confirmed_question", confirmed_question)
            set_step("plan")
    st.markdown("</div>", unsafe_allow_html=True)


def render_plan():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Boundaries, shape, and contribution</div>", unsafe_allow_html=True)
    st.header("Research plan")
    st.write("Use this stage to decide what the article covers, what kind of claim it is making, and how ambitious it should be. This is the point where the article becomes manageable.")
    st.markdown("**Law side of the question**")
    left, right = st.columns(2)
    with left:
        iv_text = st.text_area("What is the main legal rule, doctrine, or legal setting you are examining?", value=st.session_state.project["answers"].get("iv_text", ""), height=120)
        st.markdown("<div class='helper'>Example: a statute, doctrine, procedural rule, institutional arrangement, or legal standard.</div>", unsafe_allow_html=True)
    with right:
        dv_text = st.text_area("What legal or practical consequence are you trying to assess?", value=st.session_state.project["answers"].get("dv_text", ""), height=120)
        st.markdown("<div class='helper'>Example: rights protection, legal certainty, accountability, access to justice, compliance, or institutional effect.</div>", unsafe_allow_html=True)
    st.markdown("**Boundaries**")
    q1 = st.text_input("What belongs inside the article on the law side?", value=st.session_state.project["answers"].get("scope_q1", ""))
    st.markdown("<div class='helper'>State what counts as within scope for the legal issue or framework.</div>", unsafe_allow_html=True)
    q2 = st.text_input("What belongs inside the article on the consequence side?", value=st.session_state.project["answers"].get("scope_q2", ""))
    st.markdown("<div class='helper'>State the outcome or consequence you will actually evaluate, not every possible effect.</div>", unsafe_allow_html=True)
    q3 = st.text_input("Which comparator jurisdictions matter, if any, and what role do they play?", value=st.session_state.project["answers"].get("scope_q3", ""))
    st.markdown("<div class='helper'>Example: none; brief support only; one serious comparison; a model to test against the Philippine setting.</div>", unsafe_allow_html=True)
    q4 = st.text_input("What will you deliberately exclude?", value=st.session_state.project["answers"].get("scope_q4", ""))
    st.markdown("<div class='helper'>Say what the article is not trying to do.</div>", unsafe_allow_html=True)
    posture = blank_selectbox("What kind of claim is this article making?", ["Descriptive or clarifying", "Critical", "Reform-oriented"], key="posture_select", help_text="Choose the dominant posture, even if the article does more than one thing.")
    claim_strength = blank_selectbox("How ambitious is the claim?", ["Narrow and precise", "Moderate and generalizable", "Ambitious and system-level"], key="strength_select", help_text="Choose the smallest honest version of the claim that you can actually defend.")
    contribution = blank_selectbox("What is the main contribution?", ["Clarifying doctrine", "Resolving ambiguity", "Proposing reform", "Building a framework"], key="contrib_select", help_text="This helps the workspace decide what kind of structure the article needs later on.")
    evidence = blank_selectbox("How ready are your supporting legal materials?", ["Mostly in hand", "Partly in hand", "I still need a lot of source work"], key="evidence_select", help_text="Answer honestly. This is about execution, not confidence.")
    weakness = st.text_area("What is the biggest weakness or uncertainty in the article right now?", value=st.session_state.project["answers"].get("weakness", ""), height=90)
    st.markdown("<div class='helper'>This helps the workspace anticipate what later stages should focus on.</div>", unsafe_allow_html=True)
    depth = blank_selectbox("How much engagement do you want at this stage?", ["Lean", "Deep"], key="plan_depth", help_text="Lean keeps this fast. Deep should make later stages smarter by giving the workspace more to work with now.")
    if depth:
        st.session_state.project["stage_depth"]["plan"] = depth
    c1, c2 = st.columns([1,1])
    if c1.button("Save this plan"):
        scoping = {
            "law_side_boundary": q1,
            "consequence_boundary": q2,
            "comparators": q3,
            "exclusions": q4,
            "posture": posture,
            "claim_strength": claim_strength,
            "contribution_type": contribution,
            "evidence_ready": evidence,
            "weakness": weakness,
        }
        save_answer("iv_text", iv_text)
        save_answer("dv_text", dv_text)
        save_answer("selected_ivs", [iv_text] if iv_text else [])
        save_answer("selected_dvs", [dv_text] if dv_text else [])
        save_answer("scoping", scoping)
        if st.button:
            pass
        set_step("sources")
    if c2.button("Refresh later stages from here"):
        save_answer("scoping", {
            "law_side_boundary": q1,
            "consequence_boundary": q2,
            "comparators": q3,
            "exclusions": q4,
            "posture": posture,
            "claim_strength": claim_strength,
            "contribution_type": contribution,
            "evidence_ready": evidence,
            "weakness": weakness,
        })
        refresh_from("plan")
        st.success("Later stages cleared for refresh.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_sources():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Legal materials and literature map</div>", unsafe_allow_html=True)
    st.header("Sources and literature")
    st.write("Bring together the confirmed legal materials and the wider literature picture. This stage should show where the article sits and what kinds of source clusters it may need.")
    known_sources = st.text_area("What authorities, authors, or materials do you already know you will likely use?", value=st.session_state.project["answers"].get("known_sources", ""), height=100)
    st.markdown("<div class='helper'>List anything you already trust: cases, statutes, textbooks, articles, agency issuances, treaties, or recurring authorities.</div>", unsafe_allow_html=True)
    depth = blank_selectbox("How much engagement do you want at this stage?", ["Lean", "Deep"], key="sources_depth", help_text="Lean gives a quicker map. Deep gives a fuller cluster view and more gap notes.")
    if depth:
        st.session_state.project["stage_depth"]["sources"] = depth
    c1, c2 = st.columns([1,1])
    if c1.button("Build source map"):
        save_answer("known_sources", known_sources)
        result = run_sources_and_literature()
        save_output("literature_map", result, "sources and literature")
    if c2.button("Refresh later stages from here"):
        refresh_from("sources")
        st.success("Later stages cleared for refresh.")
    result = st.session_state.project["outputs"].get("literature_map")
    if result:
        st.markdown("<div class='output-box'>", unsafe_allow_html=True)
        st.subheader("Article map")
        if result.get("legal_sources"):
            st.write("**Legal materials already in play**")
            for s in result["legal_sources"]:
                if isinstance(s, dict):
                    st.markdown(f"- {s.get('title','')} · {s.get('source','')} · {s.get('url','')}" )
                else:
                    st.markdown(f"- {s}")
        if result.get("themes"):
            st.write("**Literature themes**")
            for t in result["themes"]:
                st.markdown(f"- **{t.get('title','Theme')}** — {t.get('what_it_covers','')}" )
        if result.get("gap_notes"):
            st.write("**Gap or caution notes**")
            for g in result["gap_notes"]:
                st.markdown(f"- {g}")
        fig = build_network_figure(result.get("graph_nodes", []), result.get("graph_edges", []))
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Click and drag to inspect the map. Treat the connections as planning guidance, not as verified citation relationships.")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Continue to writing launch"):
            set_step("launch")
    st.markdown("</div>", unsafe_allow_html=True)


def render_launch():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Make the paper your own</div>", unsafe_allow_html=True)
    st.header("Writing launch")
    ownership = st.text_area("To make the paper your own, state the article’s core argument in one paragraph", value=st.session_state.project["answers"].get("ownership_paragraph", ""), height=140)
    st.markdown("<div class='helper'>Write this in your own voice. The goal is to see whether the article direction still holds together once you say it directly yourself.</div>", unsafe_allow_html=True)
    if st.checkbox("Show how this stage is helping", key="launch_explain"):
        st.info("This stage does not write the paper for you. It pulls your materials, question, scope, source map, and publication fit together into a drafting plan so you can start writing with stronger ownership and less uncertainty.")
    if st.button("Build writing launch pack"):
        save_answer("ownership_paragraph", ownership)
        result = run_launch_builder()
        save_output("launch_pack", result, "writing launch")
    result = st.session_state.project["outputs"].get("launch_pack")
    if result:
        st.markdown("<div class='output-box'>", unsafe_allow_html=True)
        st.subheader("Writing launch pack")
        st.write("**Project brief**")
        st.json(result.get("project_brief", {}))
        st.write("**Section map**")
        for s in result.get("section_map", []):
            st.markdown(f"- **{s.get('section','Section')}** — {s.get('purpose','')}" )
        pack = result.get("writing_pack", {})
        if pack:
            st.write("**Writing prompts**")
            for p in pack.get("starter_prompts", []):
                st.markdown(f"- {p}")
        st.write("**Review questions before drafting**")
        for q in result.get("review_questions", []):
            st.markdown(f"- {q}")
        st.markdown("</div>", unsafe_allow_html=True)
        if st.button("Continue to export"):
            set_step("export")
    st.markdown("</div>", unsafe_allow_html=True)


def render_export():
    render_governance_strip()
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.markdown("<div class='kicker'>Save and refine</div>", unsafe_allow_html=True)
    st.header("Export and next iteration")
    st.write("Export your current project state, your cumulative testing notes, and the current outputs in one file for further refinement.")
    checkpoint = json.dumps(st.session_state.project, indent=2, ensure_ascii=False)
    st.download_button("Download checkpoint (.json)", data=checkpoint, file_name=f"workspace_checkpoint_{APP_VERSION}.json", mime="application/json")
    packet = export_feedback_markdown()
    st.download_button("Download refinement packet (.md)", data=packet, file_name=f"refinement_packet_{APP_VERSION}.md", mime="text/markdown")
    st.text_area("Refinement packet preview", value=packet[:8000], height=300)
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    init_state()
    render_progress()
    st.title(APP_NAME)
    st.caption(f"Version {APP_VERSION}")
    st.sidebar.title(APP_NAME)
    st.sidebar.caption(f"Version {APP_VERSION}")
    provider = st.session_state.project["answers"].get("provider", "Mock")
    st.sidebar.markdown(f"**Provider:** {provider}")
    st.sidebar.markdown(f"**Model:** `{DEFAULT_MODEL}`")
    if get_openai_api_key():
        st.sidebar.success("OpenAI key detected")
    else:
        st.sidebar.warning("No OpenAI key detected")
    with st.sidebar.expander("How to connect OpenAI"):
        st.code('OPENAI_API_KEY = "your_key_here"', language="toml")
        st.markdown("Place this in `.streamlit/secrets.toml`, or export `OPENAI_API_KEY` in your terminal before running the app.")
    with st.sidebar.expander("Changelog"):
        for ver, items in CHANGELOG.items():
            st.markdown(f"**{ver}**")
            for item in items:
                st.markdown(f"- {item}")
    render_testing_sidebar()
    if st.session_state.get("show_checkpoint_loader"):
        render_checkpoint_loader()
    step = st.session_state.project["current_step"]
    if step == "welcome":
        render_welcome()
    elif step == "intake":
        render_intake()
    elif step == "fit":
        render_fit()
    elif step == "argument":
        render_argument()
    elif step == "plan":
        render_plan()
    elif step == "sources":
        render_sources()
    elif step == "launch":
        render_launch()
    elif step == "export":
        render_export()


if __name__ == "__main__":
    main()
