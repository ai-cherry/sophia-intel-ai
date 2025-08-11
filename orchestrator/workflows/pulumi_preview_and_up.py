import asyncio
from temporalio import workflow
from datetime import timedelta
from services.sandbox import Sandbox, SandboxResult
from services.approvals_github import GitHubApprovalService

# Import activities from other services
# For example:
# from services.pulumi_conn import run_pulumi_preview, run_pulumi_up

@workflow.activity
async def run_sandbox_tests() -> SandboxResult:
    # In a real scenario, this would be a more complex activity
    sandbox = Sandbox()
    return await sandbox.run(["pytest", "tests/"])

@workflow.activity
async def run_pulumi_preview_activity(stack: str) -> str:
    # This would use the pulumi_conn service
    # For now, returning a placeholder
    return f"Pulumi preview for stack: {stack}\n...plan..."

@workflow.activity
async def run_pulumi_up_activity(stack: str) -> str:
    # This would use the pulumi_conn service
    return f"Pulumi up for stack: {stack}\n...success..."

@workflow.activity
async def create_approval_gate(sha: str, action_id: str) -> int:
    # This would use the approvals_github service
    # For now, returning a placeholder check_run_id
    return 12345

@workflow.activity
async def update_approval_gate(check_run_id: int, approved: bool):
    # This would use the approvals_github service
    print(f"Updating approval gate {check_run_id} to approved={approved}")

@workflow.define
class PulumiPreviewAndUpWorkflow:
    @workflow.run
    async def run(self, sha: str, stack: str) -> str:
        # 1. Run tests in sandbox
        test_result = await workflow.execute_activity(
            run_sandbox_tests,
            start_to_close_timeout=timedelta(minutes=5),
        )
        if test_result.exit_code != 0:
            return f"Sandbox tests failed:\n{test_result.stderr}"

        # 2. Run pulumi preview
        preview = await workflow.execute_activity(
            run_pulumi_preview_activity,
            args=[stack],
            start_to_close_timeout=timedelta(minutes=10),
        )
        workflow.logger.info(f"Pulumi preview:\n{preview}")

        # 3. Create approval gate
        action_id = f"pulumi-up-{stack}"
        check_run_id = await workflow.execute_activity(
            create_approval_gate,
            args=[sha, action_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        # 4. Wait for approval
        try:
            await workflow.wait_for_signal("approval_received", timeout=timedelta(hours=24))
            approved = True
        except asyncio.TimeoutError:
            approved = False

        # 5. Update approval gate and execute pulumi up if approved
        await workflow.execute_activity(
            update_approval_gate,
            args=[check_run_id, approved],
            start_to_close_timeout=timedelta(seconds=30),
        )

        if approved:
            result = await workflow.execute_activity(
                run_pulumi_up_activity,
                args=[stack],
                start_to_close_timeout=timedelta(minutes=15),
            )
            return result
        else:
            return "Approval timed out or was rejected."