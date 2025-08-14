import argparse, json
from .graph import run

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--task", required=True)
    a=p.parse_args()
    print(json.dumps(run(a.task), indent=2)[:20000])

if __name__ == "__main__":
    main()