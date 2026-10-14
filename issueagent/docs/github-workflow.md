# GitHub workflow

## Connection

The user enters owner, repository name, and a Personal Access Token. The backend validates `GET /repos/{owner}/{repo}` before storing connection metadata. Fine-grained PAT permissions should be limited to the selected repository. Read-only analysis requires metadata, issues, contents, and code-search access; branch/commit/draft-PR requires the corresponding contents and pull-request write permissions.

## Reads

Issue lists, issue details/comments, repository metadata, code search, file contents, and the default branch SHA are retrieved through GitHub REST API calls in `GitHubService`. The browser never calls GitHub directly.

## Writes

After explicit approval, the backend creates `ai-issue/<issue>-<random>` from the default branch SHA. It applies validated complete file contents on that branch, records the commit SHA, and creates a draft pull request against the default branch. The API never merges, force-pushes, or writes to the default branch.

If a provider call fails, the state remains at the last safe transition and the UI shows an actionable error. Demo mode returns a clearly labeled deterministic provider response without claiming to have modified GitHub.
