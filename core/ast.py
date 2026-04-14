class BlockNode:
    def __init__(self, language, code):
        self.language = language
        self.code = code


class ProgramNode:
    def __init__(self, blocks):
        self.blocks = blocks
