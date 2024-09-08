class HandledResultSymbol:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"<Symbol({self.name})>"


PROCESSED = HandledResultSymbol("PROCESSED")
SKIPPED = HandledResultSymbol("SKIPPED")
