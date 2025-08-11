import json
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class Guardrails:
    max_budget: float
    path_allowlist: List[str]
    json_only: bool = True

    def check_request(self, request_data: Dict[str, Any], current_spend: float) -> bool:
        """
        Checks if a request is compliant with the defined guardrails.
        """
        if self.json_only and not self._is_json_serializable(request_data):
            print("Guardrail check failed: Request data is not JSON serializable.")
            return False

        if current_spend > self.max_budget:
            print(
                f"Guardrail check failed: Budget exceeded ({current_spend} > {self.max_budget})."
            )
            return False

        # This is a simplified check. A real implementation would be more robust.
        if "path" in request_data and not self._is_path_allowed(request_data["path"]):
            print(
                f"Guardrail check failed: Path '{request_data['path']}' is not in the allowlist."
            )
            return False

        return True

    def _is_json_serializable(self, data: Any) -> bool:
        try:
            json.dumps(data)
            return True
        except (TypeError, OverflowError):
            return False

    def _is_path_allowed(self, path: str) -> bool:
        # A simple startswith check for now.
        # A more robust implementation might use regex or glob patterns.
        for allowed_path in self.path_allowlist:
            if path.startswith(allowed_path):
                return True
        return False


def load_guardrails_from_config(config: Dict[str, Any]) -> Guardrails:
    """
    Loads guardrails from a configuration dictionary.
    """
    # In a real app, this config would come from a secure source.
    guardrails_config = config.get("guardrails", {})
    return Guardrails(
        max_budget=guardrails_config.get("max_budget", 100.0),
        path_allowlist=guardrails_config.get(
            "path_allowlist", ["/workspaces/sophia-intel/"]
        ),
        json_only=guardrails_config.get("json_only", True),
    )


if __name__ == "__main__":
    # Example usage
    mock_config = {
        "guardrails": {
            "max_budget": 50.0,
            "path_allowlist": ["/safe/path/", "/another/safe/path/"],
            "json_only": True,
        }
    }
    guardrails = load_guardrails_from_config(mock_config)

    # Test cases
    print("Running guardrail checks...")
    compliant_request = {"action": "read", "path": "/safe/path/file.txt"}
    assert guardrails.check_request(compliant_request, 25.0)

    non_json_request = {"data": {1, 2, 3}}  # A set is not JSON serializable
    assert not guardrails.check_request(non_json_request, 25.0)

    budget_exceeded_request = {"action": "write"}
    assert not guardrails.check_request(budget_exceeded_request, 60.0)

    disallowed_path_request = {"action": "read", "path": "/unsafe/path/file.txt"}
    assert not guardrails.check_request(disallowed_path_request, 25.0)

    print("Guardrail checks completed.")
