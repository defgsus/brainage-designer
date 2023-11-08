

def strip_help_text(text: str) -> str:
    lines = text.splitlines()
    min_indent = None
    for line in lines:
        if line.strip():

            indent = len(line) - len(line.lstrip())

            if min_indent is None:
                min_indent = indent
            else:
                min_indent = min(min_indent, indent)

    if min_indent is not None:
        lines = [
            line[min_indent:]
            for line in lines
        ]

    return "\n".join(lines).strip() + "\n"


