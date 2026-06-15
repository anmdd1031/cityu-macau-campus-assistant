# Easy Installation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the repository into a beginner-friendly knowledge package whose default China-region workflow is downloading and uploading one Markdown file.

**Architecture:** Keep the source knowledge files authoritative and generate a deterministic distribution file from them. Add platform-neutral build scripts, a verification script, a corrected MCP template, a concise root README, and a detailed China installation guide.

**Tech Stack:** Markdown, PowerShell, POSIX shell, JSON, GitHub.

---

### Task 1: Package verification

**Files:**
- Create: `tests/verify-package.ps1`

- [ ] Write checks that fail while generated files and templates are absent.
- [ ] Run `pwsh -NoProfile -File tests/verify-package.ps1` and confirm failure.

### Task 2: Knowledge package builders

**Files:**
- Create: `scripts/build-knowledge.ps1`
- Create: `scripts/build-knowledge.sh`
- Create: `dist/cityu-campus-assistant.md`

- [ ] Implement deterministic UTF-8 concatenation in PowerShell.
- [ ] Implement equivalent POSIX shell generation.
- [ ] Generate the distribution file.
- [ ] Verify required sections and source markers.

### Task 3: MCP template

**Files:**
- Create: `config/mcp.filesystem.example.json`

- [ ] Add valid JSON using `@modelcontextprotocol/server-filesystem`.
- [ ] Restrict the example to the repository directory.
- [ ] Verify JSON parsing.

### Task 4: User documentation

**Files:**
- Modify: `README.md`
- Create: `docs/INSTALL_CN.md`

- [ ] Replace the current Claude-first README with a three-step China-first workflow.
- [ ] Document direct upload, knowledge platforms, local models, MCP, troubleshooting, privacy, and acceptance questions.
- [ ] Cite official upstream documentation for region availability and third-party installation behavior.
- [ ] Verify all repository-relative links.

### Task 5: Verification and publication

**Files:**
- Modify as needed based on verification findings.

- [ ] Run the PowerShell builder twice and confirm a clean diff.
- [ ] Run the package verification script.
- [ ] Inspect `git diff --check` and repository status.
- [ ] Commit the scoped files.
- [ ] Push the feature branch and create a pull request.
