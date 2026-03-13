#!/usr/bin/env python3
"""Fix mojibake in Python files - reverse double UTF-8 encoding."""
import sys

def fix_mojibake(content: bytes) -> str:
    """Fix double UTF-8 encoding (UTF-8 -> latin-1 -> UTF-8)."""
    try:
        text = content.decode('utf-8')
        intermediate = text.encode('latin-1')
        fixed = intermediate.decode('utf-8')
        return fixed
    except Exception as e:
        raise ValueError(f"Cannot fix mojibake: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: fix_mojibake.py <file>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    with open(filepath, 'rb') as f:
        raw = f.read()
    
    try:
        fixed = fix_mojibake(raw)
        # Write back
        with open(filepath, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(fixed)
        print(f"Fixed: {filepath}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
