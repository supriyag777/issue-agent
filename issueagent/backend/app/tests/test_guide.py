from uuid import uuid4


def test_guide_context_and_builtin_answer(client):
    email = f"guide-{uuid4().hex}@example.com"
    register = client.post("/api/v1/auth/register", json={"name": "Guide User", "email": email, "password": "GuidePassword123!"})
    assert register.status_code == 201
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    context = client.get("/api/v1/guide/context", params={"path": "/repositories"}, headers=headers)
    assert context.status_code == 200
    assert context.json()["provider_mode"] == "built-in"
    assert "repository" in context.json()["answer"].lower()

    answer = client.post("/api/v1/guide/ask", json={"question": "What should Owner contain?", "path": "/repositories"}, headers=headers)
    assert answer.status_code == 200
    assert answer.json()["provider_mode"] == "built-in"
    assert "github" in answer.json()["answer"].lower()
