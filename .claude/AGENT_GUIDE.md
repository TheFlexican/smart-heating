# Agent Development Guide

This guide explains how the Claude Code agent system works and how to customize or extend it.

## How Agents Work

Agents are defined in `.claude/agents/*.md` files with YAML frontmatter and a detailed system prompt.

### Agent File Structure

```markdown
---
name: agent-name
description: Clear description of when Claude should invoke this agent
tools: [Read, Write, Edit, Grep, Glob, Bash, Task, WebSearch, WebFetch]
model: sonnet  # or haiku, opus
---

# Agent Title

You are an expert in [domain]...

[Detailed system prompt with instructions, patterns, examples]
```

### Frontmatter Fields

- **name**: Unique identifier (kebab-case)
- **description**: When Claude should use this agent (be specific!)
- **tools**: Array of tools the agent can access
- **model**: Which Claude model to use (sonnet/haiku/opus)

### Description Best Practices

The `description` field is critical - it's how Claude decides when to invoke your agent.

**Good descriptions (specific, actionable):**
- "Expert code reviewer focusing on async patterns, coordinator usage, and HA compliance"
- "Generates pytest tests with proper fixtures, achieving 80%+ coverage"
- "Scaffolds new coordinators, entities, and API handlers following project patterns"

**Bad descriptions (vague, unclear):**
- "Helps with Home Assistant stuff"
- "Code helper"
- "Testing agent"

## Tools Available to Agents

### File Operations
- **Read**: Read file contents
- **Write**: Create new files
- **Edit**: Modify existing files

### Search & Discovery
- **Grep**: Search file contents (regex)
- **Glob**: Find files by pattern

### Execution
- **Bash**: Run shell commands

### Web Access
- **WebSearch**: Search the internet
- **WebFetch**: Fetch specific URLs

### Coordination
- **Task**: Invoke other agents (for orchestrators)

### Specialized
- **NotebookEdit**: Edit Jupyter notebooks
- **mcp__***: Custom MCP tools (if configured)

## Agent Types in This Project

### 1. Orchestrator (ha-developer)

**Purpose:** Primary entry point, routes to specialists

**Characteristics:**
- Has ALL tools (including Task for delegation)
- Broad description covering all HA development
- Contains workflow patterns for different task types
- Makes routing decisions

**Key patterns:**
```markdown
## Input Analysis Framework
When you receive a request, classify it:
- Bug fix → analyze, fix, review, test
- New feature → research, scaffold, implement, test, review
- Test update → analyze, generate tests
```

### 2. Specialists (ha-code-reviewer, ha-test-generator, etc.)

**Purpose:** Focused expertise in one domain

**Characteristics:**
- Specific tool subset (no Task tool usually)
- Narrow, specific description
- Deep domain knowledge
- Detailed checklists and patterns

**Key patterns:**
```markdown
## Review Checklist
- [ ] Async/await correctness
- [ ] Type hints present
- [ ] Proper error handling
...
```

### 3. Consultants (ha-expert)

**Purpose:** Knowledge base, answer questions

**Characteristics:**
- Read-only tools + WebSearch
- Pattern explanations
- Decision frameworks
- Pros/cons analysis

**Key patterns:**
```markdown
## Common Questions

### Q: When should I use X vs Y?
Answer with reasoning, examples, references
```

## Customizing Agents

### Adding New Patterns

Edit the agent file to add new patterns:

```markdown
### New Pattern: Widget Manager

**Reference:** `smart_heating/widget_manager.py`

```python
class WidgetManager:
    """Pattern explanation..."""
    def __init__(self, hass):
        self.hass = hass
```

**Key Points:**
- Point 1
- Point 2
```

### Adding Checklist Items

For review agents:

```markdown
### Check Name (SEVERITY)

**Check:**
- [ ] New item to check
- [ ] Another item

**Anti-patterns:**
```python
# ❌ BAD
bad_code_example()

# ✅ GOOD
good_code_example()
```
```

### Adding Templates

For scaffolding agents:

```markdown
### New Component Template

```python
"""Module for {ComponentName}."""

# Template code here
```

**Usage:**
When to use this template...
```

## Creating New Agents

### Step 1: Define Purpose

Ask yourself:
- What specific problem does this agent solve?
- When should it be invoked?
- What expertise does it need?

### Step 2: Choose Tools

- **Read-only research?** → Read, Grep, Glob, WebSearch
- **Code generation?** → Read, Write, Edit
- **Testing/execution?** → Read, Bash
- **Orchestration?** → Task (plus others)

### Step 3: Write Agent File

Create `.claude/agents/new-agent.md`:

```markdown
---
name: new-agent
description: Specific description of what this agent does
tools: [Read, Write, Edit]
model: sonnet
---

# Agent Title

You are an expert in...

## Your Role
What you do...

## Patterns to Follow
Specific patterns...

## Examples
Concrete examples...

## Reference Files
Key files to reference...
```

### Step 4: Test the Agent

```bash
claude "Use new-agent to [test task]"
```

Verify:
- Agent is invoked correctly
- Has access to needed tools
- Produces expected output
- Follows project patterns

### Step 5: Document

Add to `.claude/README.md`:
```markdown
### new-agent (Specialist)

Brief description

**When called:** When to use it
```

## Best Practices

### 1. Single Responsibility

Each agent should have one clear purpose:
- ✅ ha-code-reviewer: Only reviews code
- ✅ ha-test-generator: Only generates tests
- ❌ ha-everything: Does review, tests, scaffolding, and more

### 2. Appropriate Tool Access

Grant only necessary tools:
- Code reviewer doesn't need Write (read-only)
- Test generator needs Write (creates files)
- Orchestrator needs Task (delegates)

### 3. Detailed Prompts

Include in agent prompts:
- Role and responsibilities
- Patterns and anti-patterns
- Code examples (good and bad)
- Reference files from the project
- Output format expectations

### 4. Reference Real Code

Always reference smart_heating files:
```markdown
**Reference:** `/Users/ralf/git/smart_heating/smart_heating/coordinator.py:22-86`
```

Users can then read the actual implementation.

### 5. Clear Output Format

Specify how agents should format output:
```markdown
## Output Format

```markdown
## Review Results

### Critical Issues
- [ ] file.py:42 - Issue description
  ```python
  # Fix code
  ```

### Summary
- X critical, Y warnings, Z suggestions
```
```

## Agent Coordination

### How Delegation Works

The orchestrator uses the **Task tool**:

```markdown
I'm going to consult the ha-expert for guidance.

[Tool call: Task with subagent_type="ha-expert" and prompt="When should I use a coordinator?"]

Based on the expert's recommendation, I'll now implement...
```

### Delegation Pattern

```markdown
1. Analyze user request
2. Determine which specialist(s) needed
3. Provide context to specialist
4. Receive specialist output
5. Act on recommendations
6. Report to user
```

### Chaining Specialists

```markdown
User: "Add new feature X"

ha-developer:
  1. [Task → ha-expert] Architecture guidance
  2. [WebSearch] Research similar integrations
  3. [Task → ha-scaffolder] Generate boilerplate
  4. [Implement code]
  5. [Task → ha-test-generator] Create tests
  6. [Task → ha-code-reviewer] Review implementation
  7. [Run tests]
  8. [Report completion]
```

## Maintenance

### Updating Patterns

When project patterns change:

1. **Identify affected agents**
   - Review agents: Update checklist
   - Test generators: Update fixtures/patterns
   - Scaffolders: Update templates
   - Expert: Update Q&A

2. **Update agent files**
   - Edit `.claude/agents/[agent].md`
   - Add new patterns
   - Update examples
   - Reference new files

3. **Test changes**
   - Run example requests
   - Verify new patterns followed
   - Check delegation still works

4. **Update documentation**
   - Update `.claude/README.md` if needed
   - Update `.claude/EXAMPLES.md` with new cases

### Adding Smart_heating Features

When adding features to smart_heating:

1. **Implement feature** normally
2. **Update ha-scaffolder** with new templates if reusable
3. **Update ha-code-reviewer** if new patterns introduced
4. **Update ha-expert** with new Q&A if needed
5. **Add examples** to `.claude/EXAMPLES.md`

### Version Control

**Do** commit agent files:
```bash
git add .claude/
git commit -m "Add HA specialist agents"
```

**Why:** Share agents with your team!

### Performance Tuning

**Model selection:**
- **haiku**: Fast, cheap (simple tasks)
- **sonnet**: Balanced (most agents)
- **opus**: Slow, expensive (complex reasoning)

**Current setup:** All agents use **sonnet** (good balance)

**To change:**
Edit agent frontmatter:
```yaml
model: haiku  # For faster, simpler agents
```

## Common Patterns

### Pattern: Knowledge Base

For expert/consultant agents:

```markdown
## Common Questions

### Q: Specific question?
**Answer:** Detailed answer with reasoning

**Example:**
```python
code_example()
```

**References:**
- smart_heating file
- HA docs link
```

### Pattern: Checklist Reviewer

For review agents:

```markdown
## Review Checklist

### 1. Category (SEVERITY)
- [ ] Item to check
- [ ] Another item

**Good:**
```python
good_code()
```

**Bad:**
```python
bad_code()
```
```

### Pattern: Template Generator

For scaffolding agents:

```markdown
### Template Name

**When to use:** Description

```python
"""Template code."""

def template_{name}():
    # TODO: Implement
    pass
```

**Customization:**
- Replace {name}
- Add specific logic
```

## Troubleshooting

### Agent not being invoked?

**Check:**
1. Description is specific enough
2. Description matches user's request
3. Agent file is in `.claude/agents/`
4. YAML frontmatter is valid

**Fix:**
Make description more specific or add examples to agent prompt.

### Agent has wrong tools?

**Check:**
Frontmatter `tools:` array

**Fix:**
```yaml
tools: [Read, Write, Edit, Bash]  # Add needed tools
```

### Agent not following patterns?

**Check:**
1. Patterns clearly explained in prompt
2. Examples provided (good and bad)
3. Reference files specified

**Fix:**
Add more examples and references to agent prompt.

### Delegation not working?

**Check:**
1. Orchestrator has `Task` tool
2. Agent name matches exactly
3. Task prompt provides context

**Fix:**
```markdown
[Task tool with subagent_type="ha-expert" prompt="Detailed question with context"]
```

## Resources

- **Claude Code Docs:** https://code.claude.com/docs
- **Agent SDK:** https://platform.claude.com/docs/agent-sdk
- **Smart_heating Repo:** This project!
- **HA Developer Docs:** https://developers.home-assistant.io/

---

**Remember:** Agents are tools to help you work faster and better. Customize them to match your workflow!
