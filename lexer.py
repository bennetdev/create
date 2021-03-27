import sys
from token_types import TokenType


def _build_types():
    types = {}
    for token in TokenType:
        types[token.value] = token
    return types


# all available types
TYPES = _build_types()


# Lexer to tokenize text
class Lexer:

    def __init__(self, input):
        self.input = input + "\n"
        self.current_char = ''
        self.current_pos = -1
        self._next_char()

        self.tokens = []

    # set next char of input
    def _next_char(self):
        self.current_pos += 1
        if self.current_pos >= len(self.input):
            self.current_char = '\0'
        else:
            self.current_char = self.input[self.current_pos]

    # get next char
    def _peek(self):
        if self.current_pos + 1 >= len(self.input):
            return '\0'
        else:
            return self.input[self.current_pos + 1]

    # raise Exception
    def _abort(self, message):
        raise Exception("Lexing error: " + message)

    def _skip_whitespace(self):
        while self.current_char in {' ', '\t', '\r'}:
            self._next_char()

    def _skip_comment(self):
        if self.current_char == TokenType.COMMENT:
            while self.current_char != "\n":
                self._next_char()

    # get current token
    def get_token(self):
        # ignore whitespace and comments
        self._skip_whitespace()
        self._skip_comment()

        token = None
        # if combined token
        if self.current_char + self._peek() in TYPES:
            last_char = self.current_char
            self._next_char()
            combined_char = last_char + self.current_char

            token = Token(combined_char, TYPES[combined_char])
        # if single token
        elif self.current_char in TYPES:
            token = Token(self.current_char, TYPES[self.current_char])
        # if string
        elif self.current_char == "\"":
            self._next_char()
            start_pos = self.current_pos

            while self.current_char != "\"":
                if self.current_char in {"\r", "\n", "\t", "\\", "%"}:
                    self._abort("Illegal character in string.")
                self._next_char()
            token = Token(self.input[start_pos: self.current_pos], TokenType.STRING)
        # if number
        elif self.current_char.isdigit():
            start_pos = self.current_pos

            while self._peek().isdigit():
                self._next_char()
            if self._peek() == ".":
                self._next_char()
                if not self._peek().isdigit():
                    self._abort("Illegal character in number")
                while self._peek().isdigit():
                    self._next_char()
            token = Token(self.input[start_pos: self.current_pos + 1], TokenType.NUMBER)
        # if letter
        elif self.current_char.isalpha():
            start_pos = self.current_pos
            while self._peek().isalpha():
                self._next_char()
            text = self.input[start_pos: self.current_pos + 1]
            token = Token(text, None)
            token.set_keyword()
        else:
            self._abort("Unknown token: " + self.current_char)
        self._next_char()

        self.tokens.append(token)

        return token


class Token:
    def __init__(self, text, type):
        self.text = text
        self.type = type

    # set keyword as tokentype
    def set_keyword(self):
        for kind in TokenType:
            if kind.value == self.text:
                self.type = kind
                break
        else:
            self.type = TokenType.IDENT
