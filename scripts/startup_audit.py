#!/usr/bin/env python3
"""
Comprehensive Environment, Shell & Startup Audit Tool
Identifies all potential triggers, configurations, and startup mechanisms
"""

import os
import sys
import json
import subprocess
import glob
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import plistlib

class StartupAuditor:
    def __init__(self):
        self.results = {
            'audit_timestamp': datetime.now().isoformat(),
            'system_info': {},
            'shell_configs': {},
            'launch_agents': {},
            'executable_scripts': {},
            'environment_vars': {},
            'running_processes': {},
            'suspicious_files': [],
            'security_issues': [],
            'recommendations': []
        }
        self.home_dir = Path.home()
        self.current_dir = Path.cwd()
        
    def audit_system_info(self):
        """Gather basic system information"""
        try:
            self.results['system_info'] = {
                'platform': subprocess.check_output(['uname', '-s']).decode().strip(),
                'version': subprocess.check_output(['uname', '-r']).decode().strip(),
                'architecture': subprocess.check_output(['uname', '-m']).decode().strip(),
                'hostname': subprocess.check_output(['hostname']).decode().strip(),
                'current_shell': os.environ.get('SHELL', 'unknown'),
                'current_user': os.environ.get('USER', 'unknown'),
                'home_directory': str(self.home_dir),
                'current_directory': str(self.current_dir)
            }
        except Exception as e:
            self.results['system_info'] = {'error': str(e)}
    
    def audit_shell_configs(self):
        """Audit all shell configuration files"""
        shell_files = [
            '.bashrc', '.bash_profile', '.bash_login', '.profile',
            '.zshrc', '.zshenv', '.zprofile', '.zlogin',
            '.cshrc', '.tcshrc', '.kshrc', '.fishrc'
        ]
        
        config_results = {}
        
        # Check home directory
        for filename in shell_files:
            filepath = self.home_dir / filename
            if filepath.exists():
                config_results[str(filepath)] = self._analyze_shell_file(filepath)
        
        # Check for backup files
        for pattern in ['.*rc*', '.*profile*', '.*login*', '.*env*']:
            for filepath in self.home_dir.glob(pattern):
                if filepath.is_file() and str(filepath) not in config_results:
                    config_results[str(filepath)] = self._analyze_shell_file(filepath)
        
        # Check current directory for shell configs
        for pattern in ['.*rc', '.*profile', '.*env*']:
            for filepath in self.current_dir.glob(pattern):
                if filepath.is_file():
                    config_results[str(filepath)] = self._analyze_shell_file(filepath)
        
        self.results['shell_configs'] = config_results
    
    def _analyze_shell_file(self, filepath: Path) -> Dict[str, Any]:
        """Analyze individual shell configuration file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            analysis = {
                'size': filepath.stat().st_size,
                'modified': datetime.fromtimestamp(filepath.stat().st_mtime).isoformat(),
                'permissions': oct(filepath.stat().st_mode)[-3:],
                'contains_aliases': bool(re.search(r'alias\s+\w+', content)),
                'contains_exports': bool(re.search(r'export\s+\w+', content)),
                'contains_functions': bool(re.search(r'function\s+\w+|^\w+\(\)', content, re.MULTILINE)),
                'contains_sourcing': bool(re.search(r'source\s+|\.\ ', content)),
                'suspicious_patterns': [],
                'microphone_refs': [],
                'claude_refs': [],
                'startup_commands': []
            }
            
            # Look for suspicious patterns
            suspicious = [
                (r'curl.*\|\s*sh', 'Remote script execution'),
                (r'wget.*\|\s*sh', 'Remote script execution'),
                (r'chmod\s+\+x', 'Making files executable'),
                (r'nohup.*&', 'Background process spawning'),
                (r'osascript', 'macOS script execution'),
                (r'launchctl', 'macOS service management'),
                (r'sudo.*without.*password', 'Passwordless sudo'),
                (r'🎤|mic|speak|voice', 'Microphone/voice references'),
                (r'claude|anthropic', 'Claude/Anthropic references')
            ]
            
            for pattern, description in suspicious:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    analysis['suspicious_patterns'].append({
                        'pattern': pattern,
                        'description': description,
                        'matches': matches
                    })
            
            # Extract startup commands
            startup_patterns = [
                r'.*\s*&\s*$',  # Background commands
                r'nohup\s+.*',  # No hangup commands
                r'screen\s+-d.*',  # Screen sessions
                r'tmux\s+.*'  # Tmux sessions
            ]
            
            for pattern in startup_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                analysis['startup_commands'].extend(matches)
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def audit_launch_agents(self):
        """Audit macOS LaunchAgents and LaunchDaemons"""
        launch_paths = [
            '/Library/LaunchAgents',
            '/Library/LaunchDaemons',
            '/System/Library/LaunchAgents',
            '/System/Library/LaunchDaemons',
            self.home_dir / 'Library' / 'LaunchAgents'
        ]
        
        agents_results = {}
        
        for path in launch_paths:
            path = Path(path)
            if path.exists():
                for plist_file in path.glob('*.plist'):
                    agents_results[str(plist_file)] = self._analyze_plist(plist_file)
        
        self.results['launch_agents'] = agents_results
    
    def _analyze_plist(self, filepath: Path) -> Dict[str, Any]:
        """Analyze macOS plist file"""
        try:
            with open(filepath, 'rb') as f:
                plist_data = plistlib.load(f)
            
            analysis = {
                'label': plist_data.get('Label', 'unknown'),
                'program': plist_data.get('Program'),
                'program_arguments': plist_data.get('ProgramArguments', []),
                'run_at_load': plist_data.get('RunAtLoad', False),
                'keep_alive': plist_data.get('KeepAlive', False),
                'start_interval': plist_data.get('StartInterval'),
                'watch_paths': plist_data.get('WatchPaths', []),
                'suspicious': False
            }
            
            # Check for suspicious elements
            suspicious_keywords = ['mic', 'voice', 'speak', 'claude', 'flow', '🎤']
            program_str = str(plist_data).lower()
            
            if any(keyword in program_str for keyword in suspicious_keywords):
                analysis['suspicious'] = True
                analysis['suspicious_reasons'] = [
                    keyword for keyword in suspicious_keywords 
                    if keyword in program_str
                ]
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def audit_executable_scripts(self):
        """Find and analyze executable scripts"""
        script_extensions = ['.sh', '.py', '.js', '.pl', '.rb', '.swift']
        
        # Search in common directories
        search_dirs = [
            self.current_dir,
            self.home_dir / 'bin',
            self.home_dir / '.local' / 'bin',
            Path('/usr/local/bin'),
            Path('/opt/homebrew/bin')
        ]
        
        executable_results = {}
        
        for search_dir in search_dirs:
            if search_dir.exists():
                # Find executable files
                try:
                    for filepath in search_dir.rglob('*'):
                        if filepath.is_file() and os.access(filepath, os.X_OK):
                            # Skip if in node_modules or similar
                            if 'node_modules' in str(filepath) or '.git' in str(filepath):
                                continue
                            
                            # Check if it's a script or has suspicious content
                            if any(str(filepath).endswith(ext) for ext in script_extensions):
                                executable_results[str(filepath)] = self._analyze_executable(filepath)
                            elif self._contains_shebang(filepath):
                                executable_results[str(filepath)] = self._analyze_executable(filepath)
                except PermissionError:
                    continue
        
        self.results['executable_scripts'] = executable_results
    
    def _analyze_executable(self, filepath: Path) -> Dict[str, Any]:
        """Analyze executable file"""
        try:
            stat_info = filepath.stat()
            
            analysis = {
                'size': stat_info.st_size,
                'permissions': oct(stat_info.st_mode)[-3:],
                'modified': datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                'is_executable': os.access(filepath, os.X_OK),
                'file_type': None,
                'suspicious_content': [],
                'contains_network_calls': False,
                'contains_system_calls': False
            }
            
            # Determine file type
            try:
                result = subprocess.run(['file', str(filepath)], 
                                      capture_output=True, text=True, timeout=5)
                analysis['file_type'] = result.stdout.strip()
            except:
                pass
            
            # Analyze content if it's a text file
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(10000)  # First 10KB
                
                suspicious_patterns = [
                    (r'curl|wget|fetch', 'Network calls'),
                    (r'osascript|launchctl', 'System calls'),
                    (r'🎤|mic|speak|voice', 'Microphone references'),
                    (r'claude|anthropic', 'Claude references'),
                    (r'nohup.*&|screen.*-d', 'Background execution'),
                    (r'chmod\s+\+x', 'Permission changes'),
                    (r'rm\s+-rf|rmdir', 'File deletion'),
                    (r'sudo|su\s+', 'Privilege escalation')
                ]
                
                for pattern, description in suspicious_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        analysis['suspicious_content'].append(description)
                
                analysis['contains_network_calls'] = bool(
                    re.search(r'curl|wget|fetch|http|https', content, re.IGNORECASE)
                )
                analysis['contains_system_calls'] = bool(
                    re.search(r'osascript|launchctl|sudo|su\s+', content, re.IGNORECASE)
                )
                
            except:
                pass
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _contains_shebang(self, filepath: Path) -> bool:
        """Check if file contains a shebang"""
        try:
            with open(filepath, 'rb') as f:
                first_bytes = f.read(2)
                return first_bytes == b'#!'
        except:
            return False
    
    def audit_environment_vars(self):
        """Audit environment variables"""
        env_results = {
            'total_vars': len(os.environ),
            'suspicious_vars': {},
            'path_analysis': {},
            'shell_vars': {}
        }
        
        # Look for suspicious environment variables
        suspicious_keywords = ['mic', 'voice', 'speak', 'claude', 'anthropic', 'token', 'key', 'secret']
        
        for key, value in os.environ.items():
            key_lower = key.lower()
            value_lower = value.lower()
            
            if any(keyword in key_lower or keyword in value_lower for keyword in suspicious_keywords):
                env_results['suspicious_vars'][key] = {
                    'value': value[:100] + '...' if len(value) > 100 else value,
                    'full_length': len(value),
                    'reasons': [
                        keyword for keyword in suspicious_keywords 
                        if keyword in key_lower or keyword in value_lower
                    ]
                }
        
        # Analyze PATH
        if 'PATH' in os.environ:
            path_dirs = os.environ['PATH'].split(':')
            env_results['path_analysis'] = {
                'total_dirs': len(path_dirs),
                'directories': path_dirs,
                'suspicious_dirs': [
                    d for d in path_dirs 
                    if any(keyword in d.lower() for keyword in suspicious_keywords)
                ]
            }
        
        # Common shell variables
        shell_vars = ['SHELL', 'TERM', 'EDITOR', 'PAGER', 'BROWSER']
        for var in shell_vars:
            if var in os.environ:
                env_results['shell_vars'][var] = os.environ[var]
        
        self.results['environment_vars'] = env_results
    
    def audit_running_processes(self):
        """Audit currently running processes"""
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout.strip().split('\n')[1:]  # Skip header
            
            process_results = {
                'total_processes': len(processes),
                'suspicious_processes': [],
                'claude_processes': [],
                'voice_processes': []
            }
            
            suspicious_keywords = ['mic', 'voice', 'speak', '🎤']
            claude_keywords = ['claude', 'anthropic']
            
            for process_line in processes:
                process_lower = process_line.lower()
                
                # Check for suspicious processes
                if any(keyword in process_lower for keyword in suspicious_keywords):
                    process_results['suspicious_processes'].append(process_line)
                
                # Check for Claude processes
                if any(keyword in process_lower for keyword in claude_keywords):
                    process_results['claude_processes'].append(process_line)
                
                # Check for voice processes
                if any(keyword in process_lower for keyword in ['voice', 'audio', 'speech']):
                    process_results['voice_processes'].append(process_line)
            
            self.results['running_processes'] = process_results
            
        except Exception as e:
            self.results['running_processes'] = {'error': str(e)}
    
    def generate_recommendations(self):
        """Generate security recommendations based on findings"""
        recommendations = []
        
        # Check shell configs
        for filepath, analysis in self.results['shell_configs'].items():
            if isinstance(analysis, dict) and analysis.get('suspicious_patterns'):
                recommendations.append(f"Review suspicious patterns in {filepath}")
        
        # Check launch agents
        for filepath, analysis in self.results['launch_agents'].items():
            if isinstance(analysis, dict) and analysis.get('suspicious'):
                recommendations.append(f"Investigate suspicious LaunchAgent: {filepath}")
        
        # Check executables
        suspicious_executables = [
            path for path, analysis in self.results['executable_scripts'].items()
            if isinstance(analysis, dict) and analysis.get('suspicious_content')
        ]
        if suspicious_executables:
            recommendations.append(f"Review {len(suspicious_executables)} suspicious executable files")
        
        # Check environment
        if self.results['environment_vars'].get('suspicious_vars'):
            recommendations.append("Review suspicious environment variables")
        
        # Check processes
        if (self.results['running_processes'].get('suspicious_processes') or 
            self.results['running_processes'].get('claude_processes')):
            recommendations.append("Monitor running processes for unwanted services")
        
        # General recommendations
        recommendations.extend([
            "Regularly audit shell configuration files",
            "Review LaunchAgents and LaunchDaemons periodically",
            "Monitor executable files in PATH directories",
            "Use secure environment variable management",
            "Implement process monitoring"
        ])
        
        self.results['recommendations'] = recommendations
    
    def run_audit(self) -> Dict[str, Any]:
        """Run complete audit"""
        print("Starting comprehensive startup audit...")
        
        print("1. Gathering system information...")
        self.audit_system_info()
        
        print("2. Auditing shell configurations...")
        self.audit_shell_configs()
        
        print("3. Scanning LaunchAgents and LaunchDaemons...")
        self.audit_launch_agents()
        
        print("4. Analyzing executable scripts...")
        self.audit_executable_scripts()
        
        print("5. Reviewing environment variables...")
        self.audit_environment_vars()
        
        print("6. Checking running processes...")
        self.audit_running_processes()
        
        print("7. Generating recommendations...")
        self.generate_recommendations()
        
        print("Audit complete!")
        return self.results
    
    def save_report(self, filename: str = None):
        """Save audit report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"startup_audit_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"Audit report saved to: {filename}")
        return filename

def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
Comprehensive Environment, Shell & Startup Audit Tool

Usage: python3 startup_audit.py [options]

Options:
  --help          Show this help message
  --output FILE   Save report to specific file
  --quiet         Run in quiet mode
  --summary       Show only summary information

This tool audits:
- Shell configuration files
- LaunchAgents and LaunchDaemons
- Executable scripts
- Environment variables
- Running processes
- Security issues and recommendations
        """)
        return
    
    quiet_mode = '--quiet' in sys.argv
    summary_only = '--summary' in sys.argv
    
    # Get output filename if specified
    output_file = None
    try:
        output_idx = sys.argv.index('--output')
        if output_idx + 1 < len(sys.argv):
            output_file = sys.argv[output_idx + 1]
    except ValueError:
        pass
    
    # Run audit
    auditor = StartupAuditor()
    
    if not quiet_mode:
        results = auditor.run_audit()
    else:
        print("Running quiet audit...")
        results = auditor.run_audit()
    
    # Save report
    report_file = auditor.save_report(output_file)
    
    # Display summary
    if not quiet_mode or summary_only:
        print("\n" + "="*60)
        print("AUDIT SUMMARY")
        print("="*60)
        
        print(f"System: {results['system_info'].get('platform', 'unknown')} "
              f"{results['system_info'].get('version', '')}")
        print(f"User: {results['system_info'].get('current_user', 'unknown')} "
              f"(Shell: {results['system_info'].get('current_shell', 'unknown')})")
        
        print(f"\nShell Configs: {len(results['shell_configs'])} files analyzed")
        suspicious_shells = sum(1 for analysis in results['shell_configs'].values() 
                              if isinstance(analysis, dict) and analysis.get('suspicious_patterns'))
        if suspicious_shells:
            print(f"  ⚠️  {suspicious_shells} files contain suspicious patterns")
        
        print(f"Launch Agents: {len(results['launch_agents'])} files analyzed")
        suspicious_agents = sum(1 for analysis in results['launch_agents'].values() 
                               if isinstance(analysis, dict) and analysis.get('suspicious'))
        if suspicious_agents:
            print(f"  ⚠️  {suspicious_agents} suspicious agents found")
        
        print(f"Executable Scripts: {len(results['executable_scripts'])} files analyzed")
        suspicious_scripts = sum(1 for analysis in results['executable_scripts'].values() 
                                if isinstance(analysis, dict) and analysis.get('suspicious_content'))
        if suspicious_scripts:
            print(f"  ⚠️  {suspicious_scripts} scripts contain suspicious content")
        
        print(f"Environment Variables: {results['environment_vars'].get('total_vars', 0)} total")
        suspicious_vars = len(results['environment_vars'].get('suspicious_vars', {}))
        if suspicious_vars:
            print(f"  ⚠️  {suspicious_vars} suspicious variables found")
        
        running_processes = results['running_processes']
        if running_processes.get('claude_processes'):
            print(f"  ⚠️  {len(running_processes['claude_processes'])} Claude processes running")
        if running_processes.get('suspicious_processes'):
            print(f"  ⚠️  {len(running_processes['suspicious_processes'])} suspicious processes")
        
        print(f"\nRecommendations: {len(results['recommendations'])}")
        for i, rec in enumerate(results['recommendations'][:5], 1):
            print(f"  {i}. {rec}")
        if len(results['recommendations']) > 5:
            print(f"  ... and {len(results['recommendations']) - 5} more")
        
        print(f"\nDetailed report saved to: {report_file}")

if __name__ == '__main__':
    main()