# Interview questions and answers

1. **Why FastAPI?** Typed request validation, async provider calls, and concise dependency injection fit the workflow.
2. **Why SQLAlchemy?** It keeps provider-independent persistence testable and maps cleanly to PostgreSQL.
3. **Why JWT?** The requested app needs stateless API authentication; signing and database lookup protect ownership.
4. **How are passwords stored?** Argon2 hashes through `pwdlib`; plaintext is never persisted.
5. **How are PATs protected?** Sealed before persistence, omitted from schemas, and excluded from logs.
6. **Why not send the whole repository to the model?** Cost, privacy, and prompt-injection risk; code search and chunking bound context.
7. **How is AI output trusted?** It is untrusted until JSON parsing and Pydantic validation succeed.
8. **Can the AI execute code?** No. It produces data only; application endpoints own all side effects.
9. **How is prompt injection handled?** Source and issue text are delimitable untrusted evidence, and the system prompt rejects embedded instructions/tools.
10. **How is default-branch safety enforced?** State-gated endpoints generate a new branch and reject default-branch mutation.
11. **Why a draft PR?** Human review remains mandatory and merge is intentionally outside the product.
12. **How are paths validated?** Absolute paths, traversal, NUL bytes, `.git`, workflow-control files, and oversized patches are rejected.
13. **How do live/demo modes differ?** Demo is explicit in configuration and UI; live mode requires real provider credentials and never falls back silently.
14. **How are provider errors surfaced?** Dedicated exceptions become visible 502/503 responses with stable state.
15. **How would you scale analysis?** Move long analysis/test work to a queue and persist idempotency keys.
16. **How would you run tests safely?** Isolated ephemeral workers with limits; the current app requires an explicit worktree/command.
17. **Why PostgreSQL?** Durable relational workflow state, constraints, and production Docker parity.
18. **How would you add OAuth?** Add GitHub OAuth token exchange while retaining the provider service boundary and secret policy.
19. **What is the hardest invariant?** No repository write can happen before user approval and a non-default branch.
20. **What would you improve next?** Background jobs, webhook sync, richer patch application, OAuth, and isolated test execution.
