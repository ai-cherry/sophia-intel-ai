import os


def pytest_ignore_collect(path, config):
    p = str(path)
    # Ignore top-level test_*.py files outside the tests/ directory to avoid legacy scripts disrupting collection
    if p.endswith('.py') and os.path.basename(p).startswith('test_') and f"{os.sep}tests{os.sep}" not in p:
        return True
    return False

