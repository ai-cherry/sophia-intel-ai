from app.observability.otel_config import setup_tracing


def test_setup_tracing():
    assert setup_tracing() is None
