import sys
from core.parser import parse
from core.interpreter import interpret

def main():
    if len(sys.argv) != 2:
        print("Usage: poly file.poly")
        return

    file_path = sys.argv[1]

    with open(file_path, "r") as f:
        source_code = f.read()

    program = parse(source_code)
    interpret(program)

if __name__ == "__main__":
    main()
