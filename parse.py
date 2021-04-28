from token_types import TokenType
import sys


# ASTs for interpreter

class AST:
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.right = right
        self.token = self.op = op


class Statements(AST):
    def __init__(self):
        self.children = []


class CallMethod(AST):
    def __init__(self, object_called, method_called):
        self.object_called = object_called
        self.method_called = method_called


class DefineFunction(Statements):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.parameters = []
        self.return_statement = None


class CallFunction(AST):
    def __init__(self, name):
        self.name = name
        self.parameters = []


class CallArray(AST):
    def __init__(self, name):
        self.name = name
        self.index = 0


class Program(Statements):
    def __init__(self):
        super().__init__()


class Repeat(Statements):
    def __init__(self, count):
        super().__init__()
        self.count = count


class While(Statements):
    def __init__(self, comparison):
        super().__init__()
        self.comparison = comparison


class Each(Statements):
    def __init__(self, iterator, iterable):
        super().__init__()
        self.iterator = iterator
        self.iterable = iterable


class Conditional(AST):
    def __init__(self):
        self.cases = []
        self.else_case = None


class If(AST):
    def __init__(self, comparison):
        self.comparison = comparison
        self.children = []


class UnaryOp(AST):
    def __init__(self, op, expression):
        self.token = self.op = op
        self.expression = expression


class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.right = right
        self.token = self.op = op


class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.text


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = float(token.text)


class Array(Statements):
    def __init__(self):
        super().__init__()


class String(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.text


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

        self.symbols = set()

        self.tokens = []
        self.tree = []

        self.current_token = None
        self.peek_token = None

        self.next_token()
        self.next_token()

    # parse all tokens
    def parse(self):
        return self.program()

    def check_token(self, type):
        return type == self.current_token.type

    def _check_peek(self, type):
        return type == self.peek_token.type

    # check token, raise error if not, move one char afterwards
    def _match(self, type):
        if not self.check_token(type):
            self._abort("Expected: " + type.name + ", got " + self.current_token.type.name + " instead")
        self.next_token()

    # match set of types
    def _match_set(self, set):
        if not self.current_token.type in set:
            self._abort("Expected: " + "types" + ", got " + self.current_token.type.name + " instead")
        self.next_token()

    # set next token of lexer
    def next_token(self):
        self.current_token = self.peek_token
        self.peek_token = self.lexer.get_token()
        if self.current_token is not None:
            self.tokens.append(self.current_token)

    # raise Exception
    def _abort(self, message):
        raise Exception(message)

    def program(self):
        node = Program()
        # ignore newline at start
        while self.check_token(TokenType.NEWLINE):
            self.next_token()

        # parse all statements until file end
        while not self.check_token(TokenType.EOF):
            node.children.append(self.statement())
        return node

    def nl(self):
        #print("NEWLINE")
        self._match(TokenType.NEWLINE)
        while self.check_token(TokenType.NEWLINE):
            self.next_token()

    def _nl_peek(self):
        while self._check_peek(TokenType.NEWLINE):
            self.next_token()

    def is_comparison_operator(self):
        return self.current_token.type in {TokenType.EQEQ, TokenType.NOTEQ, TokenType.LT, TokenType.LTEQ, TokenType.GT,
                                           TokenType.GTEQ}

    def expression(self):
        #print("EXPRESSION")
        if self.check_token(TokenType.OBRACKET):
            node = Array()
            self.next_token()
            while not self.check_token(TokenType.CBRACKET):
                node.children.append(self.expression())
                if not self.check_token(TokenType.CBRACKET):
                    self._match(TokenType.SEPERATOR)
            self._match(TokenType.CBRACKET)
        else:
            node = self.term()

            while self.check_token(TokenType.PLUS) or self.check_token(TokenType.MINUS):
                token = self.current_token
                self.next_token()
                node = BinOp(node, token, self.term())
        return node

    def term(self):
        #print("TERM")
        if self.check_token(TokenType.STRING):
            node = self.string()
        else:
            node = self.unary()

            while self.check_token(TokenType.SLASH) or self.check_token(TokenType.ASTERISK):
                token = self.current_token
                self.next_token()
                node = BinOp(node, token, self.unary())
        return node

    def unary(self):
        #print("UNARY")

        token = self.current_token
        if self.check_token(TokenType.PLUS) or self.check_token(TokenType.MINUS):
            self.next_token()
            node = UnaryOp(token, self.unary())
        else:
            node = self.primary()
        return node

    def primary(self):
        #print("PRIMARY (" + self.current_token.text + ")")

        token = self.current_token

        if self.check_token(TokenType.NUMBER):
            self.next_token()
            return Num(token)
        elif self.check_token(TokenType.IDENT):
            if self._check_peek(TokenType.OPAREN):
                node = self.call_function()
            elif self._check_peek(TokenType.OBRACKET):
                node = self.call_array()
            elif self._check_peek(TokenType.DOT):
                node = self.call_method()
            else:
                if self.current_token.text not in self.symbols:
                    self._abort("Referencing variable before assignment: " + self.current_token.text)
                node = self.variable()
            return node
        elif self.check_token(TokenType.OPAREN):
            self._match(TokenType.OPAREN)
            node = self.expression()
            self._match(TokenType.CPAREN)
            return node
        else:
            self._abort("Unexpected token at: " + self.current_token.text)

    def string(self):
        node = String(self.current_token)
        self._match(TokenType.STRING)
        return node

    def call_function(self):
        node = CallFunction(self.current_token.text)
        self._match(TokenType.IDENT)
        self.next_token()

        while not self.check_token(TokenType.CPAREN):
            node.parameters.append(self.expression())
            if not self.check_token(TokenType.CPAREN):
                self._match(TokenType.SEPERATOR)
        self._match(TokenType.CPAREN)
        return node

    def call_method(self):
        left = self.variable()
        self._match(TokenType.DOT)
        right = self.call_function()
        node = CallMethod(left, right)
        return node

    def call_array(self):
        node = CallArray(self.current_token.text)
        self._match(TokenType.IDENT)

        self._match(TokenType.OBRACKET)
        index = self.expression()
        self._match(TokenType.CBRACKET)
        node.index = index
        return node

    def variable(self):
        node = Var(self.current_token)
        self._match(TokenType.IDENT)
        return node

    def comparison(self):
        #print("COMPARISON")
        left = self.expression()

        if self.is_comparison_operator():
            comparison = self.current_token
            self.next_token()
            right = self.expression()
            node = BinOp(left, comparison, right)
        else:
            self._abort("Expected comparison operator at " + self.current_token.text)

        while self.is_comparison_operator():
            self.next_token()
            self.expression()
        return node

    def statement_if(self):
        #print("STATEMENT-IF")
        self.next_token()
        comparison = self.comparison()
        node = Conditional()
        case = If(comparison)
        node.cases.append(case)

        self._match(TokenType.THEN)
        self.nl()

        while not self.check_token(TokenType.END):
            case.children.append(self.statement())
        self._match(TokenType.END)

        while self._check_peek(TokenType.ELSEIF):
            self.nl()
            self.next_token()
            comparison = self.comparison()
            self._match(TokenType.THEN)
            self.nl()
            case = If(comparison)
            node.cases.append(case)
            while not self.check_token(TokenType.END):
                case.children.append(self.statement())
            self._match(TokenType.END)

        while self._check_peek(TokenType.ELSE):
            self.nl()
            self.next_token()
            #print(self.current_token.text)
            self._match(TokenType.THEN)
            self.nl()
            else_case = If(None)
            node.else_case = else_case
            while not self.check_token(TokenType.END):
                else_case.children.append(self.statement())
            self._match(TokenType.END)
        return node

    def statement_assign(self):
        #print("STATEMENT-VAR")
        self.next_token()
        if self.check_token(TokenType.OBRACKET):
            self._match(TokenType.OBRACKET)
            self._match(TokenType.CBRACKET)

        self.symbols.add(self.current_token.text)

        left = self.variable()
        token = self.current_token
        self._match(TokenType.EQ)
        right = self.expression()
        node = Assign(left, token, right)
        return node

    def statement_repeat(self):
        #print("STATEMENT-REPEAT")

        self.next_token()
        count = self.expression()
        self._match(TokenType.THEN)
        node = Repeat(count)

        self.nl()

        while not self.check_token(TokenType.END):
            node.children.append(self.statement())
        self._match(TokenType.END)
        return node

    def statement_each(self):
        #print("STATEMENT-EACH")

        self.next_token()
        iterator = self.variable()
        self.symbols.add(iterator.value)
        self._match(TokenType.IN)
        iterable = self.primary()
        self._match(TokenType.THEN)
        node = Each(iterator, iterable)

        self.nl()

        while not self.check_token(TokenType.END):
            node.children.append(self.statement())
        self._match(TokenType.END)
        return node

    def statement_while(self):
        #print("STATEMENT-WHILE")

        self.next_token()
        comparison = self.comparison()
        node = While(comparison)

        self._match(TokenType.THEN)
        self.nl()
        while not self.check_token(TokenType.END):
            node.children.append(self.statement())
        self._match(TokenType.END)
        return node

    def statement_function(self):
        #print("STATEMENT-FUNCTION")

        self.next_token()
        name = self.current_token
        self._match(TokenType.IDENT)
        self._match(TokenType.OPAREN)
        node = DefineFunction(name)

        while not self.check_token(TokenType.CPAREN):
            node.parameters.append(self.current_token)
            self.symbols.add(self.current_token.text)
            self.next_token()
            if not self.check_token(TokenType.CPAREN):
                self._match(TokenType.SEPERATOR)
        self._match(TokenType.CPAREN)
        self._match(TokenType.THEN)
        self.nl()
        while not self.check_token(TokenType.END):
            node.children.append(self.statement())
            if self.check_token(TokenType.RETURN):
                self._match(TokenType.RETURN)
                value = self.expression()
                self._match(TokenType.NEWLINE)
                node.return_statement = value
                break
        self._match(TokenType.END)
        return node

    def statement_ident(self):
        if self.peek_token.type in {TokenType.PLUSEQ, TokenType.MINUSEQ, TokenType.ASTERISKEQ, TokenType.SLASHEQ,
                                    TokenType.EQ, TokenType.PLUSPLUS, TokenType.MINUSMINUS}:
            #print("STATEMENT-IDENT")
            left = self.variable()
            token = self.current_token
            if self.current_token.type in {TokenType.PLUSPLUS, TokenType.MINUSMINUS}:
                self._match_set(
                    {TokenType.PLUSPLUS, TokenType.MINUSMINUS})
                right = None
            else:
                self._match_set(
                    {TokenType.PLUSEQ, TokenType.MINUSEQ, TokenType.ASTERISKEQ, TokenType.SLASHEQ, TokenType.EQ,
                     TokenType.PLUSPLUS, TokenType.MINUSMINUS})
                right = self.expression()
            node = Assign(left, token, right)
        elif self._check_peek(TokenType.DOT):
            left = self.variable()
            self._match(TokenType.DOT)
            right = self.call_function()
            node = CallMethod(left, right)
        elif self._check_peek(TokenType.OPAREN):
            #print("STATEMENT-Function")
            node = self.call_function()
        return node

    # parse all statements
    def statement(self):
        #print(self.current_token.type, self.current_token.text, "statement")
        if self.check_token(TokenType.IF):
            node = self.statement_if()

        elif self.check_token(TokenType.VAR_ASSIGN):
            node = self.statement_assign()

        elif self.check_token(TokenType.REPEAT):
            node = self.statement_repeat()

        elif self.check_token(TokenType.WHILE):
            node = self.statement_while()
        elif self.check_token(TokenType.EACH):
            node = self.statement_each()
        elif self.check_token(TokenType.FUNCTION_DEFINE):
            node = self.statement_function()
        elif self.check_token(TokenType.IDENT):
            node = self.statement_ident()
        else:
            self._abort("Invalid statement at " + self.current_token.text + " (" + self.current_token.type.name + ")")
        self.nl()
        return node
