# Architecture

## Components

The React/Vite frontend owns navigation, query caching, authenticated presentation, diff review, and explicit action buttons. FastAPI owns authentication, provider calls, ownership checks, workflow transitions, patch validation, and non-secret error envelopes. SQLAlchemy owns durable workflow state. GitHubService and AIService isolate provider protocols so the API layer does not contain HTTP details.

```text
Operator
  ↓
React + TanStack Query
  ↓ Bearer JWT / JSON
FastAPI API routers
  ├─ auth + ownership dependencies
  ├─ repository/issue/dashboard reads
  ├─ analysis orchestration
  └─ approved change state machine
       ├─ GitHub REST API
       ├─ OpenAI API
       └─ SQLAlchemy → PostgreSQL
```

## Workflow state machine

`proposed → approved → branch_created → validated → committed → pr_created`

A proposed change may be rejected. Each transition is enforced by the backend, not only by frontend button visibility. The default branch is read as the analysis base but is never accepted as a write target. There is no merge transition.

## Data boundaries

- PATs enter only the backend connection endpoint and are sealed before persistence.
- OpenAI keys are read only by the backend.
- Issue text and code are treated as untrusted data in the AI prompt.
- AI output is parsed as JSON and validated by Pydantic before it becomes a change proposal.
- Only bounded code chunks are sent to the model.
- Logs contain request IDs and operation status, never credentials.
