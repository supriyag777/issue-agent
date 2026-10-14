def test_complete_demo_workflow(client):
    register = client.post("/api/v1/auth/register", json={"name": "Test Operator", "email": "operator@example.com", "password": "correct-horse-battery"})
    assert register.status_code == 201, register.text
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    connected = client.post("/api/v1/repositories/connect", headers=headers, json={"owner": "demo", "name": "issueagent", "demo_mode": True})
    assert connected.status_code == 201, connected.text
    repo_id = connected.json()["id"]
    assert connected.json()["provider_mode"] == "demo"

    issues = client.get(f"/api/v1/repositories/{repo_id}/issues?state=open", headers=headers)
    assert issues.status_code == 200, issues.text
    issue_id = issues.json()[0]["id"]

    analysis = client.post(f"/api/v1/issues/{issue_id}/analyze", headers=headers)
    assert analysis.status_code == 201, analysis.text
    analysis_id = analysis.json()["id"]
    assert analysis.json()["result"]["affected_files"]

    change = client.get(f"/api/v1/analyses/{analysis_id}/change", headers=headers)
    assert change.status_code == 200, change.text
    change_id = change.json()["id"]
    assert change.json()["status"] == "proposed"

    approved = client.post(f"/api/v1/changes/{change_id}/approve", headers=headers, json={"approved": True})
    assert approved.status_code == 200
    branch = client.post(f"/api/v1/changes/{change_id}/branch", headers=headers)
    assert branch.status_code == 200
    assert branch.json()["branch_name"].startswith("ai-issue/")

    validated = client.post(f"/api/v1/changes/{change_id}/validate", headers=headers)
    assert validated.status_code == 200, validated.text
    assert validated.json()["passed"] is True

    committed = client.post(f"/api/v1/changes/{change_id}/commit", headers=headers)
    assert committed.status_code == 200, committed.text
    draft_pr = client.post(f"/api/v1/changes/{change_id}/draft-pr", headers=headers)
    assert draft_pr.status_code == 200, draft_pr.text
    assert draft_pr.json()["pull_request"]["draft"] is True


def test_protected_route_rejects_missing_token(client):
    assert client.get("/api/v1/repositories").status_code == 401
