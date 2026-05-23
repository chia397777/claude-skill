# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **Claude Code custom skills repository**. It stores skill definition files (`.md`) that are loaded by Claude Code to provide specialized, domain-specific behavior when users invoke them.

## Skill File Format

Each skill is a Markdown file with a YAML frontmatter block followed by the skill's instruction content:

```markdown
---
name: skill-name
description: "Trigger description used by Claude to decide when to activate this skill"
---

# Skill Title
...instructions...
```

- `name`: The slash-command name users type to invoke the skill (e.g., `/legal-case-analysis`)
- `description`: A natural-language description Claude uses to determine when to auto-activate the skill. Should cover all trigger phrases in the user's language.

## Current Skills

### `legal-case-analysis.md`
A Traditional Chinese (Taiwan) legal case analysis skill (`法律案情分析`). It implements a structured 4-step workflow:
1. **資料查詢** – Dual-role (professor + attorney) research across Taiwan legal databases
2. **IRAC 論證 + 視覺化** – Issue/Rule/Application/Conclusion analysis + HTML Artifact output with CSS flowcharts and tab navigation
3. **判決分析** – Judgment document analysis (case number, parties, rulings, evidence, sentencing)
4. **書狀撰寫** – Legal brief drafting (appeals, answers, petitions, etc.)

Key conventions in this skill:
- Step-by-step confirmation gates: each step ends with a user confirmation prompt before proceeding
- Citations use **Bluebook** format with Traditional Chinese annotations
- Visual output is an HTML Artifact with pure CSS flowcharts (no Mermaid library) and JS tab switching
- Trigger keywords (`不懂`, `Ultrathink`, `提供原文`, `續`, `結束`) each map to specific behaviors
- Independent reasoning principle: present both sides before concluding

## Adding New Skills

Create a new `.md` file in the root with the YAML frontmatter above. The `description` field is critical — it determines when Claude auto-invokes the skill without an explicit slash command, so it should include all expected user trigger phrases.
