"""Maps a rule code (e.g. "R06") to the function that checks it."""

RULE_FUNCTIONS = {}


def register(code):
    """Decorator: @register("R06") above a function files it under that code."""
    def decorator(func):
        RULE_FUNCTIONS[code] = func
        return func
    return decorator
