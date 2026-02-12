#!/usr/bin/env python3
import json
import sys
from collections import defaultdict

session_file = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/tsl/.clawdbot/agents/main/sessions/ff2c51b1-4a8f-4b63-b54f-1a7937166449.jsonl"

cron_calls = []
cron_errors = []
timestamps = []

with open(session_file, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('type') == 'message':
                msg = data.get('message', {})
                ts = data.get('timestamp', '')
                
                # Tool use (assistant calling tool)
                if msg.get('role') == 'assistant':
                    content = msg.get('content', [])
                    if isinstance(content, str):
                        # Skip text-only messages
                        pass
                    elif isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get('type') == 'tool_use':
                                if block.get('name') == 'cron':
                                    cron_calls.append({
                                        'timestamp': ts,
                                        'input': block.get('input', {})
                                    })
                
                # Also check toolUse role (alternative format)
                elif msg.get('role') == 'toolUse' and msg.get('toolName') == 'cron':
                    cron_calls.append({
                        'timestamp': ts,
                        'input': msg.get('toolInput', {})
                    })
                
                # Tool result
                elif msg.get('role') == 'toolResult' and msg.get('toolName') == 'cron':
                    error = msg.get('details', {}).get('error', '')
                    if error:
                        cron_errors.append({
                            'timestamp': ts,
                            'error': error
                        })
        except Exception as e:
            pass

print(f"Total cron tool calls: {len(cron_calls)}")
print(f"Total cron errors: {len(cron_errors)}")

if cron_calls:
    print("\n" + "="*80)
    print("FIRST CRON CALL")
    print("="*80)
    print(f"Timestamp: {cron_calls[0]['timestamp']}")
    print(json.dumps(cron_calls[0]['input'], indent=2))
    
    print("\n" + "="*80)
    print(f"LAST CRON CALL (#{len(cron_calls)})")
    print("="*80)
    print(f"Timestamp: {cron_calls[-1]['timestamp']}")
    print(json.dumps(cron_calls[-1]['input'], indent=2))
    
    # Check for identical calls
    first_json = json.dumps(cron_calls[0]['input'], sort_keys=True)
    last_json = json.dumps(cron_calls[-1]['input'], sort_keys=True)
    
    if first_json == last_json:
        print("\n⚠️  LOOP DETECTED: First and last calls are IDENTICAL!")
    
    # Count unique call patterns
    unique_patterns = defaultdict(int)
    for call in cron_calls:
        pattern = json.dumps(call['input'], sort_keys=True)
        unique_patterns[pattern] += 1
    
    print(f"\nUnique call patterns: {len(unique_patterns)}")
    if len(unique_patterns) < len(cron_calls):
        print("⚠️  Agent is repeating the same parameters!")
        for i, (pattern, count) in enumerate(sorted(unique_patterns.items(), key=lambda x: -x[1])[:3]):
            print(f"\nPattern #{i+1} (repeated {count} times):")
            print(json.dumps(json.loads(pattern), indent=2)[:500])

if cron_errors:
    print("\n" + "="*80)
    print("SAMPLE ERROR")
    print("="*80)
    print(cron_errors[0]['error'])
    
    # Check if all errors are the same
    unique_errors = set(e['error'] for e in cron_errors)
    if len(unique_errors) == 1:
        print(f"\n⚠️  Same error repeated {len(cron_errors)} times!")
