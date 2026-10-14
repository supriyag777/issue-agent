# AI GitHub Issue Agent — Complete Windows Run Guide

This guide explains how to run the application locally on Windows using PowerShell.

## Application architecture

The application uses two local services:

| Service | Purpose | Address |
|---|---|---|
| FastAPI backend | Authentication, database, GitHub API, AI workflow | `http://127.0.0.1:8000` |
| Vite frontend | Browser interface | Vite prints the actual port, commonly `3000`, `3001`, or `3002` |

Keep the backend and frontend in separate PowerShell terminals.

## Prerequisites

Install:

- Python 3.13 standard build, preferably `Python 3.13` rather than `3.13t`.
- Node.js 22 or later.
- npm.
- GitHub account only if using live repository mode.

Check installed versions:

```powershell
py --list
node --version
npm --version
```

## First-time backend setup

Open **PowerShell window 1**:

```powershell
cd "C:\Users\Lenovo\Downloads\issueagent"
```

If a previous virtual environment is broken, recreate it:

```powershell
if (Test-Path .venv) {
    Remove-Item -Recurse -Force .venv
}

py -3.13 -m venv .venv
```

Activate it:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

The PostgreSQL driver is installed for production/Docker support. Local demo mode uses SQLite.

## Start the backend in the foreground

In PowerShell window 1:

```powershell
cd "C:\Users\Lenovo\Downloads\issueagent"

.\.venv\Scripts\Activate.ps1

$env:APP_ENV="development"
$env:DATABASE_URL="sqlite:///./issueagent.db"
$env:DEMO_MODE="true"
$env:JWT_SECRET="local-development-secret-change-this"

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

A successful startup displays:

```text
Uvicorn running on http://127.0.0.1:8000
```

Keep this terminal open. A running server does not return to the PowerShell prompt.

Verify the backend from another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected values include:

```text
status   : ok
database : connected
```

## Start the backend in the background

Use this method if the foreground server closes unexpectedly or you prefer to reuse the terminal:

```powershell
cd "C:\Users\Lenovo\Downloads\issueagent"

$env:APP_ENV="development"
$env:DATABASE_URL="sqlite:///./issueagent.db"
$env:DEMO_MODE="true"
$env:JWT_SECRET="local-development-secret-change-this"

$python = (Resolve-Path ".\.venv\Scripts\python.exe").Path

Remove-Item .\backend-start.log, .\backend-start-error.log -ErrorAction SilentlyContinue

$p = Start-Process `
  -FilePath $python `
  -ArgumentList "-m","uvicorn","backend.app.main:app","--host","127.0.0.1","--port","8000" `
  -WorkingDirectory (Get-Location) `
  -RedirectStandardOutput (Join-Path (Get-Location) "backend-start.log") `
  -RedirectStandardError (Join-Path (Get-Location) "backend-start-error.log") `
  -PassThru

Write-Host "Backend process ID: $($p.Id)"
Start-Sleep -Seconds 3
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object LocalAddress, LocalPort, OwningProcess
```

Check the logs:

```powershell
Get-Content .\backend-start.log -Tail 80
Get-Content .\backend-start-error.log -Tail 80
```

A healthy background process includes:

```text
Uvicorn running on http://127.0.0.1:8000
GET /health HTTP/1.1 200 OK
```

## Start the frontend

Open **PowerShell window 2**:

```powershell
cd "C:\Users\Lenovo\Downloads\issueagent\frontend"
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```

Vite may report that port `3000` is in use and automatically select another port:

```text
Port 3000 is in use, trying another one...
Local: http://127.0.0.1:3001/
```

Use the exact URL printed by Vite. For example:

```text
http://127.0.0.1:3001
```

If `3001` is also occupied, Vite may use `3002`.

## Use the application in demo mode

1. Open the Vite URL.
2. Select **Create workspace**.
3. Register an account.
4. Open **Repositories**.
5. Leave the demo-mode checkbox enabled.
6. Connect the demo repository.
7. Open an issue.
8. Select **Analyze with AI**.
9. Review the summary, source context, plan, and proposed diff.
10. Approve the proposed patch.
11. Create the guarded branch.
12. Validate the change.
13. Commit the branch change.
14. Create the draft PR.

Demo mode is clearly labeled and does not claim to modify GitHub.

## Connect a real GitHub repository

### Repository fields

If the repository URL is:

```text
https://github.com/supriyag777/pizza-sales
```

enter:

```text
Owner: supriyag777
Name: pizza-sales
```

Do not enter the full URL, `.git`, or your email address.

### Create a GitHub Personal Access Token

1. Open GitHub **Settings**.
2. Select **Developer settings**.
3. Select **Personal access tokens** → **Fine-grained tokens**.
4. Generate a token for only the repository you want to inspect.
5. For analysis, grant read permissions for metadata, contents, issues, and pull requests.
6. For branch, commit, and draft-PR operations, grant contents and pull-request write permission.
7. Copy the token once and keep it private.

### Connect in the application

1. Open **Repositories**.
2. Disable the demo-mode checkbox.
3. Enter the owner and repository name.
4. Paste the token into the GitHub token field.
5. Select **Validate & connect GitHub**.

The token must never be sent through chat or committed to a file.

## Common errors

### `No module named uvicorn`

The virtual environment is missing dependencies:

```powershell
cd "C:\Users\Lenovo\Downloads\issueagent"
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

### `TcpTestSucceeded : False`

Nothing is listening on port `8000`. Start the backend and keep it running.

### `WinError 10048`

Port `8000` is already occupied. Check it:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object OwningProcess
```

Check the owning process, replacing `14236` with the actual PID:

```powershell
Get-Process -Id 14236
```

If it is an old backend process, stop it:

```powershell
Stop-Process -Id 14236 -Force
```

Then start Uvicorn again.

### Vite says a port is in use

This is safe. Use the URL that Vite prints. The frontend may run on `3001`, `3002`, or another free port.

### `GitHub returned 404`

Check that:

- Owner is the username or organization from the repository URL.
- Name is only the repository name.
- The token belongs to the correct GitHub account.
- The exact private repository was selected in the fine-grained token.
- Organization SSO authorization is complete if applicable.

GitHub may return 404 for a private repository when the token cannot access it.

### `Unexpected server error`

Check the backend terminal or logs immediately after retrying:

```powershell
Get-Content .\backend-error.log -Tail 80
Get-Content .\backend-start-error.log -Tail 80
```

In development mode, the backend reports the actionable exception. Never include a GitHub token when sharing logs.

### `sqlite3.ProgrammingError: type 'dict' is not supported`

Update to the latest project source. This was caused by GitHub returning the repository owner as an object; the backend now extracts `owner.login` before saving.

If your folder is a ZIP and is not a Git repository, manually update `backend\app\api\repositories.py` so this line:

```python
repository.owner = info.get("owner", payload.owner)
```

becomes:

```python
owner_info = info.get("owner")
owner_name = owner_info.get("login") if isinstance(owner_info, dict) else owner_info
repository.owner = owner_name or payload.owner
```

### Generic browser `Request failed`

Confirm the backend is reachable first:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Then refresh the frontend using the current Vite URL.

## Stop the services

### Foreground services

Press `Ctrl+C` in the terminal running Uvicorn or Vite.

### Background backend

Find the process:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen |
  Select-Object OwningProcess
```

Stop it using the displayed PID:

```powershell
Stop-Process -Id 14236 -Force
```

Replace `14236` with the actual process ID.

## Important safety notes

- Do not commit `.env`, `git-token.txt`, or any file containing a GitHub token.
- If a token was accidentally saved in a file or committed, revoke it on GitHub immediately and create a replacement.
- Demo mode is safe for trying the UI without provider credentials.
- Live mode reads repository data through the backend and requires explicit approval before branch, commit, and draft-PR operations.
- The application does not automatically merge pull requests or silently modify the default branch.
