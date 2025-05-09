import sys
import os

def fix_xml_quotes(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    fixed_content = content.replace('""', '"')
    if content != fixed_content:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed double double-quotes in: {filename}")
    else:
        print(f"No changes needed in: {filename}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_xml_quotes.py <xmlfile>")
        sys.exit(1)
    filename = sys.argv[1]
    if not os.path.isfile(filename):
        print(f"File not found: {filename}")
        sys.exit(1)
    fix_xml_quotes(filename) 