"""
Verification script for Sophia AI core system imports and startup orchestrator
"""
import sys
import traceback

def sophia_import(module_path, symbol=None):
    try:
        if symbol:
            exec(f"from {module_path} import {symbol}")
        else:
            exec(f"import {module_path}")
        print(f"✅ Import OK: {module_path}{f'.{symbol}' if symbol else ''}")
        return True
    except Exception as e:
        print(f"❌ Import FAILED: {module_path}{f'.{symbol}' if symbol else ''}")
        traceback.print_exc()
        return False

def main():
    results = []
    results.append(sophia_import(
        'core.memory.enhanced_mem0_system', 'EnhancedMem0System'))
    results.append(sophia_import('core.hives.hive_orchestrator', 'HiveOrchestrator'))
    results.append(sophia_import('core.hives.hive_orchestrator', 'HiveType'))
    results.append(sophia_import(
        'core.framework.pure_langroid_lambda_orchestrator', 'get_orchestrator'))
    results.append(sophia_import(
        'core.framework.langroid_base_agent', 'SophiaAgentConfig'))
    results.append(sophia_import(
        'core.infrastructure.lambda_labs_gpu_manager', 'get_gpu_manager'))
    results.append(sophia_import('startup_orchestrator'))

    # Startup orchestrator instantiation
    try:
        import startup_orchestrator
        print("✅ startup_orchestrator imported successfully")
        if hasattr(startup_orchestrator, 'StartupOrchestrator'):
            orchestrator = startup_orchestrator.StartupOrchestrator()
            print("✅ StartupOrchestrator instantiated successfully")
        else:
            print("ℹ️ startup_orchestrator does not define StartupOrchestrator class")
    except Exception as e:
        print("❌ Failed to import or instantiate startup_orchestrator")
        traceback.print_exc()

    if all(results):
        print("\n🎉 All core system imports succeeded!")
    else:
        print("\n⚠️ Some core system imports failed. See above for details.")

if __name__ == "__main__":
    main()
    main()
