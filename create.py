from lexer import Lexer
from parse import Parser
import sys
from interpreter import Interpreter


# http://web.eecs.utk.edu/~azh/blog/teenytinycompiler2.html
# https://ruslanspivak.com/lsbasi-part9/

def main():

    if len(sys.argv) != 2:
        sys.exit("Error: Compiler needs source file as argument.")
    with open(sys.argv[1], 'r') as inputFile:
        input = inputFile.read()

    # Initialize the lexer, emitter, and parser.
    lexer = Lexer(input)
    parser = Parser(lexer)
    interpreter = Interpreter(parser)

    res = interpreter.interpret()

main()
