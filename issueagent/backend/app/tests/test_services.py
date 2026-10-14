from ..services.code_search_service import CodeSearchService


def test_keyword_extraction_is_bounded_and_deduplicated():
    service = CodeSearchService(github=None, settings=type("Settings", (), {})())
    words = service.keywords("Login fails", "Login login password authentication authentication validate_password")
    assert words.count("login") == 1
    assert len(words) <= 18


def test_chunk_limits_source_lines():
    service = CodeSearchService(github=None, settings=type("Settings", (), {})())
    chunk = service.chunk("src/auth.py", "\n".join(f"line {i}" for i in range(300)), 1.0)
    assert chunk["end_line"] <= 140
    assert chunk["language"] == "python"
