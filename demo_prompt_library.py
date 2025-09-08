#!/usr/bin/env python3
"""
Prompt Library System Demo
Demonstrates the key features of the mythology agent prompt library
"""

import asyncio
from datetime import datetime, timezone

from app.prompts import MythologyPromptManager, PromptLibrary
from app.prompts.mythology_prompts import BusinessContext


async def main():
    print("🎭 Mythology Agent Prompt Library Demo")
    print("=" * 50)

    # Initialize the system
    print("\n1. 🚀 Initializing Prompt Library...")
    library = PromptLibrary()
    manager = MythologyPromptManager(library)
    print(
        f"✅ Library initialized with {sum(len(versions) for versions in library.prompts.values())} prompt versions"
    )

    # Show available prompts
    print("\n2. 📋 Available Mythology Prompts:")
    for prompt_id, versions in library.prompts.items():
        if versions:
            latest = versions[0]  # Most recent first
            print(f"   📝 {prompt_id}")
            print(f"      Agent: {latest.metadata.agent_name}")
            print(f"      Domain: {latest.metadata.domain}")
            print(f"      Tags: {', '.join(latest.metadata.performance_tags or [])}")
            print(f"      Contexts: {', '.join(latest.metadata.business_context or [])}")

    # Demonstrate context-aware prompt retrieval
    print("\n3. 🎯 Context-Aware Prompt Retrieval:")
    hermes_market_prompt = manager.get_prompt_for_context(
        agent_name="hermes",
        task_type="market_analysis",
        business_context=BusinessContext.PAY_READY,
        variables={
            "business_context": "PayReady embedded payments platform expansion",
            "analysis_focus": "Competitive positioning in fintech partnerships",
            "market_segment": "Enterprise B2B embedded payments",
        },
    )

    if hermes_market_prompt:
        print("✅ Retrieved contextualized Hermes market analysis prompt")
        print("📄 Prompt preview (first 200 chars):")
        print(f"   {hermes_market_prompt[:200]}...")

    # Demonstrate version control
    print("\n4. 🔄 Version Control Operations:")

    # Find a prompt to work with
    if library.prompts:
        sample_prompt_id = list(library.prompts.keys())[0]
        print(f"Working with prompt: {sample_prompt_id}")

        # Create a branch
        branch = library.create_branch(
            prompt_id=sample_prompt_id,
            branch_name="payready-optimization",
            from_branch="main",
            description="Optimizing for PayReady specific use cases",
        )
        print(f"✅ Created branch: {branch.name}")

        # Create a variant
        try:
            variant_id = manager.create_business_context_variant(
                base_prompt_id=sample_prompt_id,
                business_context=BusinessContext.PAY_READY,
                context_modifications="""
**PayReady Context Enhancement:**
- Focus on embedded payment solutions and B2B fintech partnerships
- Emphasize scalability and enterprise integration capabilities
- Consider regulatory compliance in financial services
- Analyze competitive landscape in embedded payments space
                """,
            )
            print(f"✅ Created PayReady context variant: {variant_id}")
        except Exception as e:
            print(f"⚠️  Could not create variant: {e}")

        # Show branch information
        branches = library.get_branches(sample_prompt_id)
        print(f"📊 Branches for {sample_prompt_id}:")
        for branch in branches:
            status = "🔀 merged" if branch.is_merged else "🌿 active"
            print(f"   {status} {branch.name} - {branch.description or 'No description'}")

    # Demonstrate performance tracking
    print("\n5. 📈 Performance Analytics:")

    # Simulate updating metrics for a prompt version
    if library.prompts:
        sample_versions = list(library.prompts.values())[0]
        if sample_versions:
            sample_version = sample_versions[0]

            # Update performance metrics
            library.update_performance_metrics(
                sample_version.id,
                {
                    "success_rate": 0.87,
                    "response_quality": 8.5,
                    "user_satisfaction": 4.2,
                    "execution_time": 1.3,
                },
            )
            print(f"✅ Updated metrics for version {sample_version.id}")

    # Show performance leaderboard
    leaderboard = library.get_performance_leaderboard(domain="sophia", limit=5)
    if leaderboard:
        print("🏆 Top Performing Prompts:")
        for i, (prompt_version, score) in enumerate(leaderboard, 1):
            print(
                f"   {i}. {prompt_version.metadata.agent_name} - {prompt_version.metadata.task_type}"
            )
            print(f"      Score: {score:.2f} | Domain: {prompt_version.metadata.domain}")
    else:
        print("📊 No performance data available yet")

    # Demonstrate A/B testing setup
    print("\n6. 🧪 A/B Testing Framework:")
    from app.prompts.prompt_library import ABTestConfig

    if len(library.prompts) > 0:
        # Get sample prompt versions for A/B test
        sample_prompt_versions = list(library.prompts.values())[0]
        if len(sample_prompt_versions) >= 1:
            control_version = sample_prompt_versions[0].id

            # Create A/B test configuration
            test_config = ABTestConfig(
                test_id=f"test_hermes_market_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name="Hermes Market Analysis Optimization",
                description="Testing improved market analysis prompts for PayReady context",
                control_version=control_version,
                test_versions=[control_version],  # In real scenario, would have different versions
                traffic_split={control_version: 1.0},
                success_metrics=["success_rate", "response_quality"],
                start_time=datetime.now(timezone.utc),
                minimum_sample_size=50,
            )

            test_id = library.start_ab_test(test_config)
            print(f"✅ Started A/B test: {test_id}")

            # Simulate recording test results
            library.record_ab_test_result(
                test_id, control_version, True, {"success_rate": 0.92, "response_quality": 8.7}
            )
            print("✅ Recorded test result")

            # Get test results
            results = library.get_ab_test_results(test_id)
            if results:
                for version_id, result in results.items():
                    print(
                        f"📊 Version {version_id[:8]}... - Success Rate: {result.success_rate:.1%}"
                    )

    # Show optimization suggestions
    print("\n7. 💡 Optimization Suggestions:")
    if library.prompts:
        sample_prompt_id = list(library.prompts.keys())[0]
        suggestions = manager.suggest_optimizations(sample_prompt_id)
        print(f"🔍 Suggestions for {sample_prompt_id}:")
        for suggestion in suggestions:
            print(f"   💡 {suggestion}")

    # Export/Import demonstration
    print("\n8. 📦 Export/Import Capabilities:")
    export_data = library.export_prompts()
    prompt_count = len(export_data.get("prompts", {}))
    branch_count = len(export_data.get("branches", {}))
    print(f"✅ Export created: {prompt_count} prompts, {branch_count} branch sets")
    print(f"📁 Export timestamp: {export_data.get('export_timestamp')}")

    # Health check
    print("\n9. 🏥 System Health:")
    total_versions = sum(len(versions) for versions in library.prompts.values())
    total_branches = sum(len(branches) for branches in library.branches.values())
    total_tests = len(library.ab_tests)

    print("📊 System Status:")
    print(f"   📝 Total prompt versions: {total_versions}")
    print(f"   🌿 Total branches: {total_branches}")
    print(f"   🧪 Active A/B tests: {total_tests}")
    print(f"   💾 Storage path: {library.storage_path}")

    print("\n🎉 Demo completed successfully!")
    print("\nNext steps:")
    print("- Access the web UI at /api/v1/prompts/health")
    print("- Use the React dashboard for visual prompt management")
    print("- Integrate with mythology agents for dynamic prompt loading")
    print("- Set up A/B testing for prompt optimization")


if __name__ == "__main__":
    asyncio.run(main())
