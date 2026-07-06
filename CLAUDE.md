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

---

## 使用者背景資料（User Context）

### 公司資訊
- **公司名稱**：元太國際開發有限公司
- **統一編號**：59221893
- **代表人**：李政家
- **登記地址**：高雄市前金區大同二路81之1號1樓（郵遞區號：80143）
- **公司電話**：+886-7-2818772
- **聯絡 Email**：chia397777@gmail.com / chia969171@yahoo.com.tw
- **公司網站**：yt8772.com（目前為 HTTP，尚未加 SSL）

### App 專案：法寶貝
- **前身名稱**：LEXIPASS（因商標已被他人登記而改名）
- **開發語言**：Flutter（跨平台，同時出 Android APK 與 iOS）
- **專案路徑（Windows）**：`D:\lexipass\`
- **備份路徑（H 槽隨身碟）**：`H:\lexipass_20260705_0152\`（2026/07/05 備份）
- **最新版本**：v1.27.1（APK 已備份至 H 槽）
- **Windows 開發電腦帳號**：Acer

### Apple Developer Program（蘋果開發者計畫）申請進度
- **目標**：Organization（公司）帳號，$99/年
- **D-U-N-S Number（鄧白氏編碼）**：**658126410**（2026/07/03 核發，D&B iResearch Case #10579761）
- **下一步**：前往 developer.apple.com/programs/enroll/ 完成 Organization 帳號申請

### Google Play Console（Google 應用程式商店後台）申請進度
- **狀態**：✅ **已完成**（2026/07/06）
- **帳號類型**：Organization（公司）帳號
- **註冊費**：$25 美元（一次性，已扣款）
- **付款卡**：Visa •••• 7327
- **收據寄至**：chia397777@gmail.com
- **後台網址**：play.google.com/console/

### 對話語言規則
- 以**繁體中文**與使用者對話
- 專有名詞保留原文，旁邊附繁體中文說明（例：App Store（應用程式商店））
