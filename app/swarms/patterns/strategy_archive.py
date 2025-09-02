"""
Minimal Strategy Archive Pattern for backward compatibility
"""

class StrategyArchivePattern:
    """Minimal implementation to prevent import errors"""

    def __init__(self, archive_path: str = "tmp/strategy_archive.json"):
        self.archive_path = archive_path
        self.patterns = {"problem_types": {}}

    def retrieve_best_pattern(self, problem_type: str):
        """Return None - no archived patterns"""
        return None

    def archive_success(self, problem_type: str, pattern: str, metrics: dict):
        """No-op for now"""
        pass

# Alias for compatibility
StrategyArchive = StrategyArchivePattern
