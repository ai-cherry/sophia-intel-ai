#!/usr/bin/env python3
"""
SOPHIA Intelligence Platform - Roo Force Alignment Script
Automatically configures and validates Roo environment for custom modes.
"""

import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
import time
import yaml

class RooForceAlignment:
    def __init__(self):
        self.workspace = Path("/workspaces/sophia-intel")
        self.venv_python = self.workspace / "venv" / "bin" / "python"
        self.errors = []
        self.warnings = []
        self.fixes_applied = []
        
    def log(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def error(self, message):
        self.errors.append(message)
        self.log(message, "ERROR")
        
    def warning(self, message):
        self.warnings.append(message)
        self.log(message, "WARN")
        
    def success(self, message):
        self.fixes_applied.append(message)
        self.log(message, "SUCCESS")
        
    def run_command(self, cmd, capture=True):
        """Run command and return result"""
        try:
            if capture:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.workspace)
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(cmd, shell=True, cwd=self.workspace)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)
            
    def validate_environment(self):
        """Validate Python environment and workspace"""
        self.log("=== Environment Validation ===")
        
        # Check workspace directory
        if not self.workspace.exists():
            self.error(f"Workspace directory not found: {self.workspace}")
            return False
            
        # Check virtual environment
        if not self.venv_python.exists():
            self.error(f"Virtual environment Python not found: {self.venv_python}")
            return False
            
        # Check Python version
        success, stdout, stderr = self.run_command(f'"{self.venv_python}" --version')
        if success and "3.11.13" in stdout:
            self.success(f"Python version validated: {stdout}")
        else:
            self.warning(f"Python version mismatch: {stdout}")
            
        return True
        
    def validate_roomodes_file(self):
        """Validate .roomodes file structure"""
        self.log("=== Validating .roomodes File ===")
        
        roomodes_path = self.workspace / ".roomodes"
        if not roomodes_path.exists():
            self.error(".roomodes file not found")
            return False
            
        try:
            with open(roomodes_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                
            if not isinstance(content, dict) or 'customModes' not in content:
                self.error(".roomodes file missing 'customModes' key")
                return False
                
            modes = content['customModes']
            if not isinstance(modes, list) or len(modes) == 0:
                self.error(".roomodes file has no custom modes defined")
                return False
                
            mode_count = len(modes)
            self.success(f".roomodes file validated: {mode_count} custom modes found")
            
            # List found modes
            for mode in modes:
                if isinstance(mode, dict) and 'name' in mode and 'slug' in mode:
                    self.log(f"  - {mode['name']} ({mode['slug']})")
                    
            return True
            
        except yaml.YAMLError as e:
            self.error(f".roomodes YAML parsing error: {e}")
            return False
        except Exception as e:
            self.error(f".roomodes file validation error: {e}")
            return False
            
    def create_roo_config(self):
        """Create/update .roo/config.json with proper settings"""
        self.log("=== Creating Roo Configuration ===")
        
        roo_dir = self.workspace / ".roo"
        roo_dir.mkdir(exist_ok=True)
        
        config = {
            "customModes": {
                "file": ".roomodes",
                "format": "yaml",
                "enabled": True,
                "autoLoad": True
            },
            "workspace": str(self.workspace),
            "python": {
                "interpreter": str(self.venv_python),
                "virtualEnv": str(self.workspace / "venv")
            },
            "terminal": {
                "shellIntegration": False,
                "useInlineTerminal": True,
                "commandDelay": "50ms"
            },
            "validation": {
                "enforceEnvironment": True,
                "validateOnStartup": True,
                "rulesFile": ".roo/rules/rules.json"
            }
        }
        
        config_path = roo_dir / "config.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
            
        self.success(f"Roo configuration created: {config_path}")
        return True
        
    def clear_vscode_caches(self):
        """Clear VSCode extension caches"""
        self.log("=== Clearing VSCode Caches ===")
        
        # Common VSCode cache locations
        cache_dirs = [
            Path.home() / ".vscode" / "extensions",
            Path.home() / ".vscode-server" / "extensions",
            self.workspace / ".vscode"
        ]
        
        cleared_count = 0
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    # Don't actually delete, just clear Roo-specific caches
                    if "extensions" in str(cache_dir):
                        for ext_dir in cache_dir.glob("*roo*"):
                            if ext_dir.is_dir():
                                cache_files = list(ext_dir.glob("**/*.cache"))
                                for cache_file in cache_files:
                                    cache_file.unlink()
                                    cleared_count += 1
                except Exception as e:
                    self.warning(f"Could not clear cache {cache_dir}: {e}")
        
        # Also clear any temp VSCode caches
        try:
            import glob
            temp_caches = glob.glob("/tmp/vscode-*")
            for temp_cache in temp_caches:
                temp_path = Path(temp_cache)
                if temp_path.is_dir():
                    for cache_file in temp_path.glob("**/*roo*.cache"):
                        cache_file.unlink()
                        cleared_count += 1
        except Exception as e:
            self.warning(f"Could not clear temp caches: {e}")
                    
        if cleared_count > 0:
            self.success(f"Cleared {cleared_count} cache files")
        else:
            self.log("No cache files found to clear")
            
        return True
        
    def apply_shell_integration_fix(self):
        """Apply shell integration fix"""
        self.log("=== Applying Shell Integration Fix ===")
        
        fix_script = self.workspace / "scripts" / "roo_shell_integration_fix.sh"
        if fix_script.exists():
            success, stdout, stderr = self.run_command(f"bash {fix_script}")
            if success:
                self.success("Shell integration fix applied")
            else:
                self.warning(f"Shell integration fix failed: {stderr}")
        else:
            self.warning("Shell integration fix script not found")
            
        return True
        
    def create_startup_validation_hook(self):
        """Create a startup validation hook"""
        self.log("=== Creating Startup Validation Hook ===")
        
        hook_content = f"""#!/usr/bin/env python3
# Auto-generated Roo startup validation hook
import os
import sys
import json
from pathlib import Path

def validate_roo_startup():
    workspace = Path("{self.workspace}")
    venv_python = Path("{self.venv_python}")
    
    # Validate environment
    if not venv_python.exists():
        print("ERROR: Virtual environment Python not found")
        return False
        
    # Validate .roomodes
    roomodes_path = workspace / ".roomodes"
    if not roomodes_path.exists():
        print("ERROR: .roomodes file not found")
        return False
        
    # Set environment variables for Roo
    os.environ["ROO_WORKSPACE"] = str(workspace)
    os.environ["ROO_PYTHON"] = str(venv_python)
    os.environ["ROO_CUSTOM_MODES"] = str(roomodes_path)
    
    print("SUCCESS: Roo startup validation passed")
    return True

if __name__ == "__main__":
    success = validate_roo_startup()
    sys.exit(0 if success else 1)
"""
        
        hook_path = self.workspace / ".roo" / "startup_hook.py"
        with open(hook_path, 'w', encoding='utf-8') as f:
            f.write(hook_content)
            
        # Make executable
        os.chmod(hook_path, 0o755)
        
        self.success(f"Startup validation hook created: {hook_path}")
        return True
        
    def create_force_modes_script(self):
        """Create a script to force-load custom modes"""
        self.log("=== Creating Force Modes Script ===")
        
        script_content = """#!/usr/bin/env python3
# Force load Roo custom modes
import json
import os
import time
from pathlib import Path

def force_load_modes():
    workspace = Path("/workspaces/sophia-intel")
    roomodes_path = workspace / ".roomodes"
    
    if not roomodes_path.exists():
        print("ERROR: .roomodes file not found")
        return False
        
    # Create temporary config to force mode loading
    temp_config = {
        "forceReload": True,
        "timestamp": int(time.time()),
        "customModes": {
            "file": ".roomodes",
            "format": "yaml",
            "enabled": True,
            "forceLoad": True
        }
    }
    
    temp_config_path = workspace / ".roo" / "force_load.json"
    with open(temp_config_path, 'w') as f:
        json.dump(temp_config, f, indent=2)
        
    print(f"Force load configuration created: {temp_config_path}")
    print("Please restart VSCode to apply changes.")
    return True

if __name__ == "__main__":
    force_load_modes()
"""
        
        script_path = self.workspace / "force_load_modes.py"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        os.chmod(script_path, 0o755)
        
        self.success(f"Force modes script created: {script_path}")
        return True
        
    def run_validation_tests(self):
        """Run all validation scripts"""
        self.log("=== Running Validation Tests ===")
        
        validation_scripts = [
            "validate_roo_env.py",
            "validate_shell_integration.py",
            "scripts/validate_roomodes.py --json"
        ]
        
        for script in validation_scripts:
            self.log(f"Running: {script}")
            success, stdout, stderr = self.run_command(f'"{self.venv_python}" {script}')
            if success:
                self.success(f"✓ {script} passed")
                if stdout:
                    print(f"  Output: {stdout}")
            else:
                self.warning(f"✗ {script} failed")
                if stderr:
                    print(f"  Error: {stderr}")
                    
        return True
        
    def generate_final_report(self):
        """Generate final status report"""
        self.log("=== Final Status Report ===")
        
        print(f"\n{'='*60}")
        print("SOPHIA ROO FORCE ALIGNMENT RESULTS")
        print(f"{'='*60}")
        
        if self.fixes_applied:
            print(f"\n✅ FIXES APPLIED ({len(self.fixes_applied)}):")
            for fix in self.fixes_applied:
                print(f"  • {fix}")
                
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
                
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        else:
            print("\n✅ NO CRITICAL ERRORS FOUND")
            
        print(f"\n{'='*60}")
        print("MANUAL STEPS REQUIRED:")
        print("1. Restart VSCode: Ctrl+Shift+P → 'Developer: Reload Window'")
        print("2. Check Roo mode selector for custom modes")
        print("3. If modes still not visible, run: python force_load_modes.py")
        print(f"{'='*60}")
        
        return len(self.errors) == 0
        
    def run_full_alignment(self):
        """Run complete force alignment process"""
        self.log("STARTING SOPHIA ROO FORCE ALIGNMENT")
        
        try:
            # Step 1: Environment validation
            if not self.validate_environment():
                return False
                
            # Step 2: Validate .roomodes file
            if not self.validate_roomodes_file():
                return False
                
            # Step 3: Create/update Roo configuration
            self.create_roo_config()
            
            # Step 4: Clear caches
            self.clear_vscode_caches()
            
            # Step 5: Apply shell integration fix
            self.apply_shell_integration_fix()
            
            # Step 6: Create startup validation hook
            self.create_startup_validation_hook()
            
            # Step 7: Create force modes script
            self.create_force_modes_script()
            
            # Step 8: Run validation tests
            self.run_validation_tests()
            
            # Step 9: Generate final report
            return self.generate_final_report()
            
        except Exception as e:
            self.error(f"Force alignment failed: {e}")
            return False

def main():
    """Main entry point"""
    aligner = RooForceAlignment()
    success = aligner.run_full_alignment()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()