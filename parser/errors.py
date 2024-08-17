class ParseError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UnmatchedParenthesis(ParseError):
    def __init__(self, index: int, is_closing_parenthesis: bool = False):
        _type = "Unopened" if is_closing_parenthesis else "Unclosed"
        message = f"{_type} parenthesis found at index {index}"
        super().__init__(message)

