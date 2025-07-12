import tokenize

def check_brackets_and_strings(filename):
    with open(filename, 'rb') as f:
        tokens = list(tokenize.tokenize(f.readline))
    
    # Stack for brackets
    bracket_stack = []
    # Track string status
    string_stack = []
    errors = []

    for tok in tokens:
        if tok.type == tokenize.OP:
            if tok.string in '([{':
                bracket_stack.append((tok.string, tok.start))
            elif tok.string in ')]}':
                if not bracket_stack:
                    errors.append(f"Unmatched closing {tok.string} at line {tok.start[0]}")
                else:
                    opening, pos = bracket_stack.pop()
                    if '([{'.index(opening) != ')]}'.index(tok.string):
                        errors.append(f"Mismatched {opening} at line {pos[0]} and {tok.string} at line {tok.start[0]}")
        elif tok.type == tokenize.STRING:
            # Check for triple-quoted (multi-line) strings
            if tok.string.startswith(('"""', "'''")) and not tok.string.endswith(('"""', "'''")):
                string_stack.append((tok.string[:3], tok.start))
            elif string_stack:
                opening, pos = string_stack.pop()
                if not tok.string.endswith(opening):
                    errors.append(f"Unclosed string starting at line {pos[0]}")
    
    if bracket_stack:
        for b, pos in bracket_stack:
            errors.append(f"Unclosed {b} at line {pos[0]}")
    if string_stack:
        for s, pos in string_stack:
            errors.append(f"Unclosed string starting at line {pos[0]}")
    if not errors:
        print("No obvious unclosed brackets or strings detected.")
    else:
        print("Potential issues detected:")
        for err in errors:
            print("  -", err)

if __name__ == "__main__":
    check_brackets_and_strings("src/script_generation/script_generator.py")
