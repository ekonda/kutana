class Symbol:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<Symbol({self.name})>"


PROCESSED = Symbol("PROCESSED")
SKIPPED = Symbol("SKIPPED")
