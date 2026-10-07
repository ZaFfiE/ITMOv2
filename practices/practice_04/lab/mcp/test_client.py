#!/usr/bin/env python3
import subprocess
import json
import os
from datetime import datetime

LAB_DIR = os.path.dirname(os.path.dirname(__file__))
SERVER = os.path.join(LAB_DIR, 'mcp', 'itmo-mcp', 'server.py')
PROOF_DIR = os.path.join(LAB_DIR, 'proofs', 'mcp')
os.makedirs(PROOF_DIR, exist_ok=True)

def run_case(cases, log_path):
    payload = "\n".join(json.dumps(obj) for obj in cases) + "\n"
    p = subprocess.Popen(['python3', SERVER], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=LAB_DIR, text=True)
    try:
        out, err = p.communicate(input=payload, timeout=5)
    except Exception as e:
        p.kill()
        out, err = p.communicate()
        out += f"\nEXC: {e}"
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(out)
        if err:
            f.write("\n[stderr]\n" + err)

def main():
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    success_log = os.path.join(PROOF_DIR, f'success_{ts}.log')
    error_log = os.path.join(PROOF_DIR, f'error_{ts}.log')

    success_cases = [
        {"jsonrpc":"2.0","id":1,"method":"initialize"},
        {"jsonrpc":"2.0","id":2,"method":"tools/list"},
        {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"repo_search","arguments":{"pattern":"AGENTS","include":"**/*.md","limit":5,"max_files":10}}}
    ]

    error_cases = [
        {"jsonrpc":"2.0","id":1,"method":"initialize"},
        {"jsonrpc":"2.0","id":2,"method":"tools/list"},
        {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"repo_search","arguments":{"pattern":"[","include":"**/*.md","max_files":0}}}
    ]

    run_case(success_cases, success_log)
    run_case(error_cases, error_log)
    print("Wrote:", success_log, error_log)

if __name__ == '__main__':
    main()
