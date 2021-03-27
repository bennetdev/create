from token_types import TokenType


class NodeVisitor:
    def visit(self, node):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


class Interpreter(NodeVisitor):
    GLOBAL_SCOPE = {}
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

    def visit_CallFunction(self, node):
        arguments = []
        for child in node.parameters:
            arguments.append(self.visit(child))
        return globals()["__builtins__"][node.name](*arguments)

    def visit_Repeat(self, node):
        for i in range(int(self.visit(node.count))):
            for child in node.children:
                self.visit(child)

    def visit_String(self, node):
        return node.value

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
            value = self.GLOBAL_SCOPE[name] + self.visit(node.right)
        elif node.op.type == TokenType.MINUSEQ:
            value = self.GLOBAL_SCOPE[name] - self.visit(node.right)
        elif node.op.type == TokenType.ASTERISKEQ:
            value = self.GLOBAL_SCOPE[name] * self.visit(node.right)
        elif node.op.type == TokenType.SLASHEQ:
            value = self.GLOBAL_SCOPE[name] / self.visit(node.right)
        self.GLOBAL_SCOPE[name] = value

    def visit_Program(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Var(self, node):
        return self.GLOBAL_SCOPE[node.value]

    def interpret(self):
        tree = self.parser.parse()
        print(tree)
        return self.visit(tree)
