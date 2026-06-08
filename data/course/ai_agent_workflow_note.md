# AI Agent Workflow

AI agents can assist developers by planning, coding, testing, reviewing, and documenting software tasks.

## Typical Workflow

A typical AI-assisted software workflow includes:

1. Human provides high-level requirements.
2. AI helps convert requirements into a design document.
3. AI implements the solution.
4. AI adds tests.
5. AI checks whether tests or CI pass.
6. Human reviews the result.
7. Documentation is updated.

## Agent Management Techniques

Useful techniques include:

1. Agent behavior files, such as CLAUDE.md, AGENTS.md, and cursorrules.
2. Hooks that run scripts before or after tool use.
3. Commands for repeated prompts, such as running tests or preparing commits.
4. Subagents with specialized roles, such as frontend, backend, or security reviewer.

## Risk Control

Developers should checkpoint regularly, label AI-generated diffs, run tests, review security-sensitive changes, and maintain auditability.
