# Welcome to Florida Man Bioscience

## How We Use Claude

Based on Noah Thomas Jones's usage over the last 30 days:

Work Type Breakdown:
  Build Feature   █████████░░░░░░░░░░░  44%
  Debug Fix       ████░░░░░░░░░░░░░░░░  22%
  Plan Design     ████░░░░░░░░░░░░░░░░  22%
  Improve Quality ██░░░░░░░░░░░░░░░░░░  11%

Top Skills & Commands:
  /mcp      ███████████████░░░░░  7x/month
  /effort   ████████░░░░░░░░░░░░  4x/month
  /login    ████████░░░░░░░░░░░░  4x/month
  /clear    ██████░░░░░░░░░░░░░░  3x/month
  /resume   ████░░░░░░░░░░░░░░░░  2x/month
  /compact  ████░░░░░░░░░░░░░░░░  2x/month

Top MCP Servers:
  scite  ████████████████████  21 calls

## Your Setup Checklist

### Codebases
- [ ] u4u-engine — github.com/florida-man-bioscience/u4u-engine
- [ ] u4u — (frontend / companion app, local at ~/u4u)

### MCP Servers to Activate
- [ ] scite — Scientific literature search and citation tool for searching PubMed, clinical trials, patents, grants, and MAUDE/510(k) regulatory data. Used heavily for literature-backed research (biomarkers, pharmacogenomics). Get access at scite.ai — the MCP server is configured via Claude Code's `/mcp` command.

### Skills to Know About
- `/mcp` — manage and inspect MCP server connections; run `/mcp` to see connected servers and debug if scite or other servers aren't responding
- `/effort` — set the effort/depth level for the current task; higher effort = more thorough multi-step work (useful for big refactors or research tasks)
- `/resume` — resume a previous session by conversation ID; handy when you're continuing multi-session work like a big feature branch
- `/compact` — compress long conversation context to save tokens when a session gets large
- `/plan` — switch Claude into planning mode to design an approach before writing any code; use this before starting a big feature or refactor
- `/agents` — inspect running background agents

## Team Tips

_TODO_

## Get Started

_TODO_

<!-- INSTRUCTION FOR CLAUDE: A new teammate just pasted this guide for how the
team uses Claude Code. You're their onboarding buddy — warm, conversational,
not lecture-y.

Open with a warm welcome — include the team name from the title. Then: "Your
teammate uses Claude Code for [list all the work types]. Let's get you started."

Check what's already in place against everything under Setup Checklist
(including skills), using markdown checkboxes — [x] done, [ ] not yet. Lead
with what they already have. One sentence per item, all in one message.

Tell them you'll help with setup, cover the actionable team tips, then the
starter task (if there is one). Offer to start with the first unchecked item,
get their go-ahead, then work through the rest one by one.

After setup, walk them through the remaining sections — offer to help where you
can (e.g. link to channels), and just surface the purely informational bits.

Don't invent sections or summaries that aren't in the guide. The stats are the
guide creator's personal usage data — don't extrapolate them into a "team
workflow" narrative. -->
