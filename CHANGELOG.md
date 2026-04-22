# Changelog

All notable changes to **Write and Come Back** will be documented in this file.

This project follows a lightweight adaptation of **Keep a Changelog** and uses a **pre-1.0 versioning style**. While the app is still experimental, version numbers reflect meaningful workflow and UX changes rather than strict API guarantees.

## How to read this file

- `Added` for new features
- `Changed` for behavior or UX changes
- `Removed` for features or flows taken out
- `Fixed` for corrections
- `Planned` for agreed items not yet implemented

---

## [0.10.0] - 2026-04-22

### Added
- Introduced a clear **two-phase flow**:
  - **Quick Pass** first
  - **Deep Pass** only after Quick Pass is completed
- Added dedicated Deep Pass stages:
  - Strengthen Support
  - Tighten the Argument
  - Improve the Writing Pack
- Added a separate Deep Pass progression flow in the app.
- Added phase-aware progress display for Quick Pass and Deep Pass.
- Added export support for:
  - human-readable `.docx` pre-writing kit
  - machine-readable `.json` checkpoint

### Changed
- Moved Deep Pass **out of the individual Quick Pass steps** to reduce user confusion.
- Reframed the app around the principle:
  - **Write first, then improve**
- Kept the quick path more linear and easier for busy lecturers to complete.
- Preserved revisit/backtrack behavior, but clarified that downstream outputs should be rebuilt if earlier steps are changed.

### Removed
- Removed in-step Deep Pass choices during Quick Pass.

### Planned
- Add journal suggestion / call-for-papers search near the end of Step 6.
- Show the SVG flowchart at the start of the app in dev mode only.

---

## [0.9.0] - 2026-04-22

### Added
- Added revisit/backtrack support for earlier steps.
- Added warnings that changing earlier steps may invalidate downstream outputs.
- Added clearer `Required` vs `Optional` distinctions.
- Added indicative time estimates for Quick Pass steps.
- Added end-of-flow guidance on what to do after the final step.
- Added dual export logic:
  - human-readable pre-writing kit
  - machine-readable checkpoint

### Changed
- Merged **Build the Article Starter** into **Choose the Main Legal Point**.
- Shifted instructions to appear **above** the fields instead of after input boxes.
- Clarified that the main legal point is the **starting point of the paper** and may still be revised later.
- Reframed Step 4 around:
  - “To add to your ideas to the paper, here are further questions that might be useful to be answered.”

### Fixed
- Reduced unnecessary friction in the middle of the workflow by removing a standalone “article starter” button-only step.

---

## [0.8.0] - 2026-04-22

### Added
- Added checkpoint export capturing:
  - answers
  - outputs
  - flags
  - feedback
  - API log
- Added stage-specific user feedback capture:
  - what worked
  - what was confusing
  - what felt too much
  - what was missing
  - notes
- Added API logging for model-assisted stages.

### Changed
- Strengthened material extraction around lecture-driven legal issues.
- Began surfacing ranked legal points and article directions from uploaded materials.
- Improved legal-argument-first framing.

### Fixed
- Improved consistency of generated starter outputs across material-based runs.

---

## [0.7.0] - 2026-04-22

### Added
- Added richer multi-stage app structure.
- Added top progress navigation.
- Added plain-language UX around workflow stages.
- Added intake support for:
  - uploaded materials
  - optional bionote / CV
  - legal materials input
- Added publication-fit / journal suggestion scaffolding.
- Added cumulative in-app testing notes.

### Changed
- Reworked the app from a thin prototype into a fuller workflow-driven interface.
- Improved wording to reduce technical friction.
- Shifted emphasis toward:
  - busy lecturers
  - article direction from source materials
  - structured outputs without overloading the user too early

### Fixed
- Restored richer app behavior after an overly simplified API-wired build.

---

## [0.6.0] - 2026-04-22

### Added
- Added governance-oriented framing to explain how the platform works.
- Added explainability concepts and trust-building content at the start.
- Added early alignment ideas inspired by:
  - authorship integrity
  - journal policy sensitivity
  - disclosure thinking

### Changed
- Reframed the app as a governed writing platform rather than a raw prompt shell.

### Removed
- Later iterations moved some of this upfront governance weight into lighter language to avoid slowing users down too early.

---

## [0.5.0] - 2026-04-22

### Added
- Initial functional Streamlit prototype.
- Basic OpenAI integration.
- Early multi-step workbook structure.
- First model-assisted outputs for starter article development.

### Changed
- Established the basic direction of the system:
  - lecture materials in
  - article starter out

### Known limitations at this stage
- Flow was still too rigid.
- UX was too abstract in places.
- Persistence and export logic were still immature.

---

## [0.4.0] - 2026-04-22

### Added
- Early field-level guidance for:
  - intake
  - research question
  - lens and method
- Added examples directly in the UI.

### Changed
- Replaced vague academic prompts with more user-friendly, example-driven language.

### Fixed
- Reduced confusion in abstract fields such as “lens” and “method.”

---

## [0.3.0] - 2026-04-22

### Added
- Added app-level version control.
- Added checkpoint version control and migration awareness.
- Added sidebar version display and changelog access.
- Added version tags to outputs and AI-use records.

### Changed
- Treated the app as an evolving product rather than a one-off prototype.

---

## [0.2.0] - 2026-04-22

### Added
- Added 4-screen prototype.
- Added basic structured output generation.
- Added mock and early API testing path.

### Changed
- Established the first end-to-end demonstrable concept for bosses and internal review.

---

## [0.1.0] - 2026-04-22

### Added
- Initial concept prototype.
- Manual input flow.
- Early proof-of-doability structure.

---

## Repository best practice

For this project, the recommended minimum is:

- `README.md` → what the app is, how to run it, how to test it
- `CHANGELOG.md` → version-by-version record of changes
- tagged commits or release notes for major milestone builds

### Suggested commit style
Use clear, conventional commit messages where possible:

- `feat: separate quick pass and deep pass`
- `fix: merge article starter into legal point step`
- `docs: update changelog for v0.10.0`
- `refactor: simplify step flow for busy lecturers`

### Recommended release practice
For each meaningful iteration:
1. Update `CHANGELOG.md`
2. Commit the working code
3. Tag the version if it is a milestone build

Example:

```bash
git add .
git commit -m "feat: introduce deep pass after quick pass"
git tag v0.10.0
git push origin main --tags
```

### Practical note for this project
Because the app is still evolving quickly, it is fine to keep:
- one main `CHANGELOG.md` for repo history
- and optionally a separate internal design note later if workflow reasoning becomes too long for the changelog

For now, **`CHANGELOG.md` is the best practice and the best single file to upload to your GitHub repo**.
