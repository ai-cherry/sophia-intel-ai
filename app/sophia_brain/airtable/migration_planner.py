from __future__ import annotations

from typing import Any, Dict, List


class MigrationPlan(dict):
    def __init__(self) -> None:
        super().__init__(steps=[], rollback=[])

    def add_step(self, name: str, *args, **kwargs) -> None:
        self["steps"].append({"name": name, "args": args, "kwargs": kwargs})

    def add_rollback(self, name: str, *args, **kwargs) -> None:
        self["rollback"].append({"name": name, "args": args, "kwargs": kwargs})


class MigrationPlanner:
    def plan_field_type_change(self, field: Dict[str, Any], new_type: str, unique_values: List[str]) -> MigrationPlan:
        plan = MigrationPlan()
        if field.get("type") == "text" and new_type == "single_select":
            if len(unique_values) <= 50:
                plan.add_step("create_temp_field", {"type": new_type})
                plan.add_step("migrate_data", mapping=self._create_value_mapping(unique_values))
                plan.add_step("swap_fields")
                plan.add_rollback("restore_original_field")
            else:
                plan.add_step("question", text=f"Field has {len(unique_values)} unique values. Continue with select?")
        return plan

    def _create_value_mapping(self, values: List[str]) -> Dict[str, str]:
        # Identity mapping by default; in real usage normalize
        return {v: v for v in values}

