#!/usr/bin/env python3
"""Unified CLI for Sophia-Artemis System"""
import sys
import json
from typing import Dict, Any

class UnifiedCLI:
    def __init__(self):
        self.sophia_agents = ['business_analyst', 'memory_curator', 'insight_generator']
        self.artemis_agents = ['architect', 'developer', 'reviewer', 'tester']
    
    def execute(self, command: str, *args) -> Dict[str, Any]:
        commands = {
            'sophia': self.sophia_command,
            'artemis': self.artemis_command,
            'status': self.status,
            'help': self.help
        }
        
        if command in commands:
            return commands[command](*args)
        return {'error': f'Unknown command: {command}'}
    
    def sophia_command(self, *args):
        return {'agent': 'sophia', 'args': args}
    
    def artemis_command(self, *args):
        return {'agent': 'artemis', 'args': args}
    
    def status(self):
        return {
            'sophia_agents': self.sophia_agents,
            'artemis_agents': self.artemis_agents,
            'status': 'ready'
        }
    
    def help(self):
        return {
            'commands': ['sophia', 'artemis', 'status', 'help'],
            'usage': 'python3 unified_cli.py <command> [args]'
        }

if __name__ == '__main__':
    cli = UnifiedCLI()
    if len(sys.argv) > 1:
        result = cli.execute(sys.argv[1], *sys.argv[2:])
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps(cli.help(), indent=2))
