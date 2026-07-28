# Agent Configuration & Usage

## Available Agents

This document describes the agents configured for NexChain and when to use them.

### Default Agent: Claude Code Guide
Used for general Claude Code questions and documentation.

**When to use:**
- Questions about Claude Code features
- How to use Claude Agent SDK
- Claude API reference questions
- IDE integration help

**How to invoke:**
```
/agent claude-code-guide
```

### Explore Agent
Fast read-only search agent for locating code patterns.

**When to use:**
- Finding files by pattern (e.g., `src/components/**/*.tsx`)
- Searching for symbols or keywords (e.g., "API endpoints")
- Answering "where is X defined" or "which files reference Y"

**When NOT to use:**
- Code review or design audits
- Cross-file consistency checks
- Open-ended analysis

**How to invoke:**
```
/agent Explore
```

**Search breadth options:**
- `quick` - Single targeted lookup
- `medium` - Moderate exploration
- `very thorough` - Multiple locations and naming conventions

### Plan Agent
Software architect agent for designing implementation plans.

**When to use:**
- Planning implementation strategy for tasks
- Designing complex features
- Architectural trade-off analysis
- Step-by-step implementation breakdown

**How to invoke:**
```
/agent Plan
```

**Output:**
- Step-by-step plans
- Critical files identification
- Architectural considerations

### General-Purpose Agent
Catch-all for multi-step tasks and complex research.

**When to use:**
- Research complex questions
- Multi-step implementation tasks
- Cross-cutting concerns
- Tasks spanning multiple files/systems

**How to invoke:**
```
/agent claude
```

## Custom Agent Configuration

To use a different agent or add new agents:

1. **Check available agents** via Claude Code settings
2. **Set default agent** in `.claude/settings.json`:
```json
{
  "agents": {
    "default": "claude"
  }
}
```

3. **Agent-specific tools:**
   - Explore: Read, Bash, WebFetch
   - Plan: All tools except Agent, Artifact, ExitPlanMode
   - General-purpose: All tools

## Agent Selection Guidelines

### For This Project (NexChain)

| Task | Recommended Agent | Reason |
|------|-------------------|--------|
| Find where API endpoints are defined | Explore | Code search |
| Design database schema changes | Plan | Architectural decision |
| Add new feature to frontend | Plan → Claude | Design first, then implement |
| Fix bug in backend | Claude | Direct code fix |
| Research supply chain algorithms | General-purpose | Multi-file research |
| Audit security | Security Review skill | Dedicated security review |
| Code quality review | Simplify/Code Review skill | Dedicated review tools |

## Using Agents for This Project

### Example: Feature Implementation
```
1. Use Plan agent to design the feature
   /agent Plan
   "Design: Add real-time supply chain alerts"

2. Follow the plan and implement:
   Use Claude or Explore agents as needed
```

### Example: Debugging
```
1. Use Explore to locate error:
   /agent Explore
   "Find error handling in ai_service/"

2. Use Claude for direct fix
   Then run tests to verify
```

### Example: Architecture Decision
```
Use Plan agent to weigh options:
/agent Plan
"Should we cache supply chain data in Redis or use PostgreSQL?"
```

## Agent Best Practices

1. **Parallel work:** Launch multiple independent agents in one message
2. **Sequential work:** Use SendMessage to continue agent conversation
3. **Check running agents:** Don't spawn duplicates if one is already running
4. **Results handling:**
   - Foreground agents (run_in_background: false) - results needed immediately
   - Background agents (default) - notified when complete

## Configuration Files

### `.claude/settings.json`
Project-level Claude Code settings:
- Default agent
- Tool permissions
- Environment variables
- Hooks for automated actions

### `.claude/settings.local.json`
Local overrides (not committed to git):
- Personal preferences
- Local API keys
- Development environment variables

## Switching Agents

To try a different agent temporarily:
```
# In Claude Code slash command
/agent <agent-name>

# Or specify in task prompt
"Help me with X (use Explore agent)"
```

## When NOT to Use Agents

- Simple questions or edits (use direct Claude interaction)
- Quick file reads/writes (use direct commands)
- Tasks requiring immediate feedback loop

## Troubleshooting Agent Issues

**Agent not responding:**
- Check if it's running in background
- Verify permissions are granted
- Try a simpler task first

**Wrong agent selected:**
- Match agent type to task type
- Check agent descriptions
- Review guidelines above

**Performance issues:**
- Use `quick` search scope for Explore
- Break large tasks into smaller subtasks
- Avoid spawning too many agents at once

## Future Agent Additions

As the project evolves, additional agents might be added for:
- Supply chain specific analysis
- Custom LLM evaluation
- Integration testing
- Performance profiling

Update this file when new agents are introduced.
