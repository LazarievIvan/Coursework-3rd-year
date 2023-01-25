import re

class TokenError(Exception):
    def __init__(self, symbol, line):
        self.symbol = symbol
        self.line = line
    
    def __str__(self):
        return 'LexicalError: Unexpected symbol "{}" at line {}'.format(self.symbol, self.line)

class Token:
    def __init__(self, kind, value, pos):
        self.kind = kind
        self.value = value
        self.pos = pos
    
    def __str__(self):
        return '(Token at line {}) kind: {}, value: {}'.format(self.pos, self.kind, self.value)
    
    def __repr__(self):
        return self.kind

def tokenize(text, token_list):
    tokens = []

    lines = text.splitlines()
    pattern = '|'.join('(?P<%s>%s)' % pair for pair in token_list)
    regex = re.compile(pattern)
    
    for count, line in enumerate(lines):
        tokens += [tokenize_line(count + 1, line, regex)]

    return tokens

def tokenize_line(count, line, regex):
    tokens = []
    pos = 0

    while pos < len(line):
        
        match = regex.match(line, pos)
        if not match:
            raise TokenError(line[pos], count)
        
        kind = match.lastgroup
        value = match.group(kind)
        pos = match.end()
        
        if kind == 'WHITESPACE':
            continue

        tokens.append(Token(kind, value, count))

    return tokens