# OpenClaw Linear Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a project-level OpenClaw Linear skill that uses the official `plugin-linear-linear` MCP integration and update approval workflows to use it instead of the custom shell script.

**Architecture:** Add one concise skill under `skills/linear/` that covers both manual ticket creation requests and the automatic approval-to-Linear workflow. Update `AGENTS.md` so future agents create issues through the official Linear MCP tools with the project's naming convention and fallback behavior when auth or team context is missing.

**Tech Stack:** Markdown skill files, project instructions in `AGENTS.md`, official `plugin-linear-linear` MCP tools such as `list_teams`, `get_user`, and `save_issue`

---

### Task 1: Add the OpenClaw Linear skill

**Files:**
- Create: `skills/linear/SKILL.md`

**Step 1: Write the skill frontmatter**

Create a new skill named `linear` with a description that makes it trigger for:
- manual ticket creation requests
- approval workflows that need a Linear issue
- questions about OpenClaw's Linear integration

**Step 2: Write the core workflow**

Document the required flow:
- inspect the relevant Linear MCP tool schemas before use
- discover the correct team with `list_teams` when needed
- resolve assignee with `get_user` when useful
- create the issue with `save_issue`
- prefer the title format `Implement Grok Suggestion #N - <title>` for approved suggestions

**Step 3: Document fallback behavior**

State that if the Linear MCP integration is not authenticated or the team cannot be determined, the agent should explain what is missing instead of falling back to `tools/linear-ticket.sh`.

### Task 2: Update the approval workflow

**Files:**
- Modify: `AGENTS.md`

**Step 1: Replace the shell-script instruction**

Update the approval workflow so it tells the agent to use the OpenClaw Linear skill and the official `plugin-linear-linear` MCP tools instead of `./tools/linear-ticket.sh`.

**Step 2: Preserve the current operator behavior**

Keep the existing constraints:
- do not implement approved work directly
- create a Linear ticket
- reply in the same Slack thread with the ticket URL
- explain missing Linear configuration if the integration is not ready

### Task 3: Verify the change

**Files:**
- Check: `skills/linear/SKILL.md`
- Check: `AGENTS.md`

**Step 1: Review for consistency**

Verify the skill is concise, the description is specific enough to trigger correctly, and the approval workflow now points to the official Linear integration.

**Step 2: Run lightweight validation**

Use workspace lint/diagnostic checks on the edited markdown files if available. Confirm there are no obvious formatting problems.
