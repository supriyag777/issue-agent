# AI workflow

1. **Understand issue:** title, body, labels, comments, and repository metadata are normalized.
2. **Extract keywords:** a bounded keyword list removes common stop words and duplicates.
3. **Identify files:** GitHub code search is queried for likely functions, classes, errors, routes, models, and issue terms.
4. **Retrieve code:** the service fetches only a small number of relevant files and truncates each chunk by line and total character budget.
5. **Analyze root cause:** OpenAI receives JSON context plus a system instruction that issue/code text is untrusted.
6. **Generate solution:** the model returns summary, severity, root cause, files/functions, plan, risk, tests, and file changes.
7. **Validate schema:** Pydantic rejects missing or malformed structured output.
8. **Generate diff:** the patch service validates paths and renders a reviewable unified diff.
9. **Human review:** only explicit approval can advance the state machine.

Provider credentials are optional for preview. With `DEMO_MODE=true` and no OpenAI key, the UI shows a demo provider badge and a deterministic sample analysis. With demo mode disabled and no key, analysis fails clearly with an unavailable state rather than fabricating a live result.
