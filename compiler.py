import sys, json
import tokenizer
from parse import *
from converter import *

all_tokens = [
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
    contents = ''

    with open(filename, 'r') as file:
        contents = file.read().strip()
    
    code_tokens = []
    try:
        code_tokens = tokenizer.tokenize(contents, all_tokens)
    except tokenizer.TokenError as e:
        print(e)
    
    parsed_code = []
    parser = Parser()
    try:
        parsed_code = parser.parse(code_tokens)
    except ParseError as e:
        print(e)
        
    syntax_tree = json.dumps(parsed_code, indent=4)
    print(syntax_tree)
    
    converter = Converter()
    contents = ''
    try:
        contents = converter.convert(parsed_code)
    except SemanticError as e:
        print(e)
    
    with open(filename.split('.')[0] + '.asm', 'w') as file:
        file.write(contents)