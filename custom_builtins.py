import random


def println(*x):
    for element in x:
        print(element)


def rmd(x, y):
    return random.randint(x, y)


builtin_functions = {
    "println": println,
    "rdm": rmd
}
