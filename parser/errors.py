class UnmatchedParenthesis(Exception):
    def __init__(self, position: int, is_closing_parenthesis: bool = False):
        _type = "Unopened" if is_closing_parenthesis else "Unclosed"
        message = f"{_type} parenthesis found at position {position}"
        super().__init__(message)
