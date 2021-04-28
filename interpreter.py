from token_types import TokenType
from custom_builtins import builtin_functions


class NodeVisitor:
    def visit(self, node):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    GLOBAL_SCOPE = {}
    FUNCTIONS = {}
    LOCAL_SCOPES = []
    globals()["__builtins__"]["print"]("test")

    def __init__(self, parser):
        self.parser = parser

    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.SLASH:
            return self.visit(node.left) / self.visit(node.right)
        elif node.op.type == TokenType.ASTERISK:
            return self.visit(node.left) * self.visit(node.right)
        else:
            operations = {
                TokenType.EQEQ: lambda left, right: left == right,
                TokenType.GTEQ: lambda left, right: left >= right,
                TokenType.GT: lambda left, right: left > right,
                TokenType.LTEQ: lambda left, right: left <= right,
                TokenType.LT: lambda left, right: left < right,
                TokenType.NOTEQ: lambda left, right: left != right,
            }
            return operations[node.op.type](self.visit(node.left), self.visit(node.right))

    def visit_Num(self, node):
        return node.value

    def visit_CallArray(self, node):
        return self.GLOBAL_SCOPE[node.name][int(self.visit(node.index))]

    def visit_Array(self, node):
        return [self.visit(child) for child in node.children]

    def visit_UnaryOp(self, node):
        if node.op.type == TokenType.PLUS:
            return +self.visit(node.expression)
        if node.op.type == TokenType.MINUS:
            return -self.visit(node.expression)

    def visit_If(self, node):
        condition = self.visit(node.comparison) if node.comparison is not None else True
        if condition:
            for child in node.children:
                self.visit(child)
        return condition

    def visit_NoneType(self, node):
        return None

    def visit_CallFunction(self, node):
        arguments = []
        for child in node.parameters:
            arguments.append(self.visit(child))
        if node.name in globals()["__builtins__"]:
            return globals()["__builtins__"][node.name](*arguments)
        elif node.name in builtin_functions:
            return builtin_functions[node.name](*arguments)
        else:
            self.LOCAL_SCOPES.append({})
            func = self.FUNCTIONS[node.name]
            for index, parameter in enumerate(func.parameters):
                self.LOCAL_SCOPES[-1][parameter.text] = arguments[index]
            statements = func.children
            for statement in statements:
                self.visit(statement)

            return_value = self.visit(func.return_statement)

            self.LOCAL_SCOPES.pop(-1)

            return return_value

    def visit_Repeat(self, node):
        for i in range(int(self.visit(node.count))):
            for child in node.children:
                self.visit(child)

    def visit_Each(self, node):
        iterable = self.visit(node.iterable)
        for i in iterable:
            self.get_current_scope()[node.iterator.value] = i
            for child in node.children:
                self.visit(child)
        del self.get_current_scope()[node.iterator.value]

    def visit_String(self, node):
        return node.value

    def visit_CallMethod(self, node):
        object_called = node.object_called
        method_called = node.method_called

        arguments = []
        for child in method_called.parameters:
            arguments.append(self.visit(child))

        return getattr(self.get_current_scope()[object_called.token.text], method_called.name)(*arguments)

    def visit_DefineFunction(self, node):
        self.FUNCTIONS[node.name.text] = node

    def visit_While(self, node):
        condition = self.visit(node.comparison)
        while condition:
            for child in node.children:
                self.visit(child)
            condition = self.visit(node.comparison)

    def visit_Conditional(self, node):
        for case in node.cases:
            if self.visit(case):
                break
        else:
            self.visit(node.else_case)

    def visit_Assign(self, node):
        name = node.left.value
        value = None
        if node.op.type == TokenType.EQ:
            value = self.visit(node.right)
        elif node.op.type == TokenType.PLUSPLUS:
            value = self.visit(node.left) + 1
        elif node.op.type == TokenType.MINUSMINUS:
            value = self.visit(node.left) - 1
        elif node.op.type == TokenType.PLUSEQ:
            value = self.get_current_scope()[name] + self.visit(node.right)
        elif node.op.type == TokenType.MINUSEQ:
            value = self.get_current_scope()[name] - self.visit(node.right)
        elif node.op.type == TokenType.ASTERISKEQ:
            value = self.get_current_scope()[name] * self.visit(node.right)
        elif node.op.type == TokenType.SLASHEQ:
            value = self.get_current_scope()[name] / self.visit(node.right)
        self.get_current_scope()[name] = value

    def visit_Program(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Var(self, node):
        return self.get_current_scope()[node.value]

    def interpret(self):
        tree = self.parser.parse()
        print(tree)
        return self.visit(tree)

    def get_current_scope(self):
        return self.GLOBAL_SCOPE if len(self.LOCAL_SCOPES) == 0 else self.LOCAL_SCOPES[-1]
