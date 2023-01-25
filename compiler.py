import sys, json
import tokenizer
from parse import *
from generator import *

token_list = [
    ('PLUS', r'\+'),
    ('MINUS', r'\-'),
    ('MUL', r'\*'),
    ('PERCENT', r'\%'),
    ('EQUALS', r'\=\='),
    ('LESS', r'\<'),
    ('GREATER', r'\>'),
    ('ASSIGN', r'\='),
    ('RET', r'return'),
    ('IF', r'if'),
    ('ELSE', r'else'),
    #('TERNARY', r'if [a-zA-Z][a-zA-Z0-9_]*\s*[\<|\>]\s*[a-zA-Z][a-zA-Z0-9_]* else [a-zA-Z][a-zA-Z0-9_]*'),
    ('WHILE', r'while'),
    ('DEF', r'def'),
    ('PRINT', r'print'),
    ('LPAR', r'\('),
    ('RPAR', r'\)'),
    ('COLON', r'\:'),
    ('COMMA', r'\,'),
    ('NUMBER', r'\d+'),
    ('TAB', r' {4}'),
    ('WHITESPACE', r'\s'),
    ('ID', r'[a-zA-Z][a-zA-Z0-9_]*')
]

if __name__ == '__main__':
    filename = "algorithm.py"#sys.argv[1]
    text = ''

    with open(filename, 'r') as file:
        text = file.read().strip()
    
    tokens = []
    try:
        tokens = tokenizer.tokenize(text, token_list)
    except tokenizer.TokenError as e:
        print(e)
    
    ast = []
    parser = Parser()
    try:
        ast = parser.parse(tokens)
    except ParseError as e:
        print(e)
        
    json_obj = json.dumps(ast, indent=4)
    print(json_obj)
    
    generator = Generator()
    text = ''
    try:
        text = generator.generate(ast)
    except SemanticError as e:
        print(e)
    
    with open(filename.split('.')[0] + '.asm', 'w') as file:
        file.write(text)