from scripts.tone_filter import enforce

def test_enforce_adds_sections_and_strips_banned():
    out = enforce("This is verbose and kind of fluffy, hope this helps.")
    low = out.lower()
    assert "answer" in low and "actions" in low and "assumptions" in low and "risks / next steps" in low
    assert "hope this helps" not in low