# API documentation

All `/api/v1` routes except `/status` require `Authorization: Bearer <JWT>`. 

## Workflow guide

- `GET /api/v1/guide/context?path=/repositories` returns contextual built-in next-step guidance for the authenticated user.
- `POST /api/v1/guide/ask` accepts `{ "question": "...", "path": "/repositories" }` and returns a safe guide answer. When `OPENAI_API_KEY` is configured, the answer uses OpenAI; otherwise the built-in guide responds. Provider failures fall back to built-in guidance.

Guide prompts are bounded, treated as untrusted input, never receive or repeat credentials, and cannot bypass human approval or default-branch protections.

## Public

- `GET /health` — non-secret application/database/provider status.
- `GET /api/v1/status` — runtime mode and provider configuration flags.
- `POST /api/v1/auth/register` — create account and return JWT.
- `POST /api/v1/auth/login` — authenticate and return JWT.

## Authenticated reads

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `GET /api/v1/repositories`
- `GET /api/v1/repositories/{repository_id}`
- `GET /api/v1/repositories/{repository_id}/dashboard`
- `GET /api/v1/repositories/{repository_id}/issues?state=open|closed|all&search=...`
- `GET /api/v1/issues/{issue_id}`
- `GET /api/v1/analyses/{analysis_id}`
- `GET /api/v1/analyses/{analysis_id}/change`

## Provider and analysis actions

- `POST /api/v1/repositories/connect` with `{github_token?, owner, name, demo_mode}`.
- `POST /api/v1/issues/{issue_id}/analyze` — code search + structured AI analysis.

## Human-approved change actions

- `POST /api/v1/changes/{change_id}/approve` with `{approved:true}`.
- `POST /api/v1/changes/{change_id}/branch` — only from `approved`.
- `POST /api/v1/changes/{change_id}/validate` — only from `branch_created`.
- `POST /api/v1/changes/{change_id}/commit` — only from `validated` with passing validation.
- `POST /api/v1/changes/{change_id}/draft-pr` — only from `committed`; always sends `draft: true`.

Error responses use a `detail` string or structured message. Provider failures use 502/503, ownership failures return 404 to avoid leaking resources, and invalid workflow transitions return 409/422.
