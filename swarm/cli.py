import argparse
import json
from swarm.graph import run

def main():
    parser = argparse.ArgumentParser(description="Swarm CLI")
    parser.add_argument("--task", required=True, help="Task description")
    
    args = parser.parse_args()
    
    try:
        artifacts = run(args.task)
        output = json.dumps(artifacts, indent=2)
        
        # Limit to 20k chars
        if len(output) > 20000:
            output = output[:10000] + "\n...[TRUNCATED]...\n" + output[-10000:]
        
        print(output)
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()