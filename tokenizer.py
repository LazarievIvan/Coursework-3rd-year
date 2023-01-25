import re

class TokenError(Exception):
    def __init__(self, symbol, line):
        self.symbol = symbol
        self.line = line
    
    def __str__(self):
        return 'Lexical error: Unexpected char/expression "{}" at line {}'.format(self.symbol, self.line)

class Token:
    def __init__(self, variation, value, position):
        self.variation = variation
        self.value = value
        self.position = position
    
    def __str__(self):
        return '(Token at line {}) variation: {}, value: {}'.format(self.position, self.variation, self.value)
    
    def __repr__(self):
        return self.variation

def tokenize(input, all_tokens):
    tokens = []

    lines = input.splitlines()
    patterns = '|'.join('(?P<%s>%s)' % pair for pair in all_tokens)
    regex_pattern = re.compile(patterns)
    
    for num, line in enumerate(lines):
        tokens += [tokenize_line(num + 1, line, regex_pattern)]

    return tokens

def tokenize_line(num, line, regex):
    tokenized_line = []
    position = 0

    while position < len(line):
        
        match = regex.match(line, position)
        if not match:
            raise TokenError(line[position], num)
        
        variation = match.lastgroup
        value = match.group(variation)
        position = match.end()
        
        if variation == 'WHITESPACE':
            continue

        tokenized_line.append(Token(variation, value, num))

    return tokenized_line