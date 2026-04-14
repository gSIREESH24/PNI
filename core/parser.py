import textwrap
from core.ast import BlockNode, ProgramNode

def parse(source_code):
    lines = source_code.splitlines()
    blocks = []

    current_lang = None
    current_code = []
    inside_block = False
    brace_depth = 0

    for line in lines:
        stripped = line.strip()

        if not inside_block and stripped.endswith("{"):
            current_lang = stripped[:-1].strip().lower()
            current_code = []
            inside_block = True
            brace_depth = 1
            continue

        if inside_block:
            brace_depth += stripped.count("{")
            brace_depth -= stripped.count("}")

            if brace_depth == 0:
                cleaned = textwrap.dedent("\n".join(current_code))
                blocks.append(BlockNode(current_lang, cleaned))
                inside_block = False
            else:
                current_code.append(line)

    return ProgramNode(blocks)
