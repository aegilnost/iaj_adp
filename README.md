# Write and Come Back

## Overview

**Write and Come Back** is a GenAI-assisted writing pipeline designed for busy lecturers, practitioners, and professionals who want to convert lecture materials into publishable legal articles.

The system works as a guided “workbook”:
- You provide lecture materials (transcripts, slides, notes)
- The system extracts **legal arguments already present**
- It helps you arrive quickly at a **workable article starter**
- You then refine it only if needed

The philosophy is simple:

> **Write first. Do not stop. Improve later.**

---

## Core Workflow

### Phase 1 — Quick Pass (Required)

This is the main workflow. It is designed to be:
- fast
- linear
- low-friction

Steps:

1. **Welcome**
   - Explains the process
   - Sets expectations (15–25 minutes total)

2. **Read My Materials**
   - Upload lecture materials
   - Extracts:
     - legal arguments
     - laws / cases mentioned
     - possible directions

3. **Choose the Main Legal Point**
   - Select the strongest legal argument
   - This becomes the **starting point of the paper**
   - Automatically generates:
     - working question
     - working title
     - starter outline

4. **Add to Your Paper (Optional)**
   - Light refinement only
   - Identify:
     - what belongs in the paper
     - what result should follow
     - missing support (if any)

5. **Start Writing Package**
   - Generates:
     - abstract seed
     - opening options
     - section-by-section writing cues

6. **Review & Export**
   - Outputs:
     - **.docx** (human-readable pre-writing kit)
     - **.json** (machine-readable checkpoint)
   - You can already start writing at this stage

---

### Phase 2 — Deep Pass (Optional)

Only available **after Quick Pass is complete**

Purpose:
- strengthen what already exists
- not to restart the process

Steps:

1. **Strengthen Support**
   - Add stronger authorities
   - Prioritize sources

2. **Tighten the Argument**
   - Narrow or sharpen the legal claim

3. **Improve the Writing Pack**
   - Improve clarity of:
     - opening
     - structure
     - drafting cues

---

## Key Design Principles

### 1. Write First
The system avoids blocking the user with too many decisions early.

### 2. Lecture-Driven
The AI does not invent content.
It extracts and organizes **what is already in the lecture**.

### 3. Deferred Complexity
Advanced refinement (Deep Pass) happens only after a usable draft exists.

### 4. User Control
The user can:
- revisit earlier steps
- override outputs
- ignore suggestions

### 5. Dual Outputs
- **DOCX** → for actual writing
- **JSON** → for iteration and system reuse

---

## Installation

### Requirements
- Python 3.10+
- pip

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run app.py
```

Then open:

```
http://localhost:8501
```

---

## API Setup (Optional but Recommended)

To enable real AI outputs:

### OpenAI
Set your API key:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

If no API key is set, the app runs in **mock mode**.

---

## File Structure

```
.
├── app.py
├── requirements.txt
├── README.md
├── CHANGELOG.md
```

---

## Versioning

This project uses a **pre-1.0 versioning approach**.

- Versions reflect meaningful UX/workflow changes
- Not strict API compatibility

See `CHANGELOG.md` for full details.

---

## Current Version

**v0.10.0**

Key features:
- Quick Pass → Deep Pass separation
- Reduced cognitive load for users
- Export system (DOCX + JSON)
- Backtracking with downstream warnings

---

## Planned Features

- Journal / Call-for-Papers suggestions at end of workflow
- Flowchart preview at start (dev mode)
- Improved UI polish and navigation
- Literature network visualization (future)

---

## Development Notes

This project is still in **active iteration**.

The workflow is being refined based on:
- real user behavior
- feedback from lecturers
- alignment with academic publishing standards

---

## Contributing (Internal)

For each iteration:

1. Update `CHANGELOG.md`
2. Commit changes clearly:

```bash
git commit -m "feat: add deep pass phase"
```

3. Tag major versions:

```bash
git tag v0.10.0
git push origin main --tags
```

---

## License

Internal / Project Use Only (for now)
