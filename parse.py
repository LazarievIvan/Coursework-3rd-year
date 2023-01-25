from tokenizer import Token

class ParseError(Exception):
    def __init__(self, msg, line):
        self.msg = msg
        self.line = line
    
    def __str__(self):
        return 'SyntaxError: {} on line {}'.format(self.msg, self.line)

class Parser:
    def __init__(self):
        self.lines = []
        self.count = -1
        pass
    
    def __tokens_to_lines(self, tokens):
        lines = []
        
        for line in tokens:
            level = sum(1 for x in line if x.kind == 'TAB')
            lines.append((level, [x for x in line if x.kind != 'TAB']))
        
        return lines
    
    def __parse_symbol(self, start, line):
        node = None
        pos = start
        
        if pos >= len(line):
            return node
        
        if line[pos].kind == 'NUMBER':
            pos += 1
            node = {'type': 'number', 'value': line[pos - 1].value}
        elif line[pos].kind == 'ID':
            pos += 1
            if pos < len(line) and line[pos].kind == 'LPAR':
                node = {'type': 'function_call', 'name': line[pos - 1].value}
                pos += 1
                params = []
                while line[pos].kind != 'RPAR':
                    pos, param = self.__parse_symbol(pos, line)
                    if param == None: 
                        raise ParseError('Expected parameter', self.count)
                    params.append(param)
                    if line[pos].kind == 'COMMA':
                        pos += 1
                
                node['parameters'] = params
                
                if pos >= len(line) or line[pos].kind != 'RPAR':
                    raise ParseError('Expected ")"', self.count)

            else:
                node = {'type': 'id', 'name': line[pos - 1].value}
        elif pos < len(line) and line[pos].kind == 'IF':
            node = {'type': 'if'}
            pos += 1
            operation = line[pos + 1]
            if operation.kind == 'LESS':
                line[pos + 1].kind = 'GREATER'
                line[pos + 1].value = '>'
            elif operation.kind == 'GREATER':
                line[pos + 1].kind = 'LESS'
                line[pos + 1].value = '<'
            condition = self.__parse_expression(line[pos:-2])
            node['condition'] = condition

            body = []
            initial_value = self.__parse_symbol(0, line[-1:])
            initial_value = initial_value[1]
            false_value = self.__parse_symbol(0, line[-2:])
            false_value = false_value[1]
            assignment = {'type': 'assignment', 'name': initial_value['name'], 'value': false_value}
            body.append(assignment)
            node['body'] = body

        else:
            raise ParseError('Unexpected symbol "{}"'.format(line[pos].value), self.count)
        
        return (pos, node)
    
    def __parse_expression(self, line):
        if len(line) == 0:
            return None
        
        pos, op = self.__parse_symbol(0, line)
        if op == None: return None
        
        if pos < len(line) and line[pos].kind in ['PLUS', 'MINUS', 'MUL', 'LESS', 'GREATER', 'PERCENT', 'EQUALS']:
            op2 = self.__parse_symbol(pos + 1, line)
            if op2 == None:
                raise ParseError('Expected second operand', self.count)
            return {'type': line[pos].kind.lower(), 'op1': op, 'op2': op2[1]}
        
        return op
    
    def __parse_line(self):
        self.count += 1
        node = None
        pos = 0
        line = self.lines[self.count][1]
        level = self.lines[self.count][0]
        
        if len(line) == 0:
            return node
        
        if line[pos].kind == 'DEF':
            if level != 0:
                raise ParseError('Function cannot be nested', self.count)
            pos += 1
            if pos >= len(line) or line[pos].kind != 'ID':
                raise ParseError('Expected function identifier', self.count)
            node = {'type': 'function', 'name': line[pos].value}
            pos += 1
            
            if pos >= len(line) or line[pos].kind != 'LPAR':
                raise ParseError('Expected "("', self.count)
            pos += 1
            
            params = []
            while line[pos].kind != 'RPAR':
                if line[pos].kind != 'ID':
                    raise ParseError('Expected identifier', line[pos])
                params.append(line[pos].value)
                pos += 1
                if line[pos].kind == 'COMMA':
                    pos += 1
            
            node['parameters'] = params
            
            if pos >= len(line) or line[pos].kind != 'RPAR':
                raise ParseError('Expected ")"', self.count)
            pos += 1
            
            if pos >= len(line) or line[pos].kind != 'COLON':
                raise ParseError('Expected ":"', self.count)
            
            body = []
            while self.count + 1 < len(self.lines) and self.lines[self.count + 1][0] > level:
                inner = self.__parse_line()
                if (inner != None): body.append(inner)
            if len(body) == 0:
                raise ParseError('Expected an indented block after function definition', self.count)
            node['body'] = body
        
        elif line[pos].kind == 'RET':
            pos += 1
            node = {'type': 'return'}
            expression = self.__parse_expression(line[pos:])
            if expression == None:
                raise ParseError('Expected an expression after return', self.count)
            node['expression'] = expression
        
        elif line[pos].kind == 'IF':
            pos += 1
            node = {'type': 'if'}
            condition = self.__parse_expression(line[pos:-1])
            if condition == None:
                raise ParseError('Expected an expression after "if" statemenent', self.count)
            node['condition'] = condition
            if line[len(line) - 1].kind != 'COLON':
                raise ParseError('Expected ":"', self.count)
            
            body = []
            while self.count + 1 < len(self.lines) and self.lines[self.count + 1][0] > level:
                inner = self.__parse_line()
                if (inner != None): body.append(inner)
            if len(body) == 0:
                raise ParseError('Expected an indented block after "if" statemenent', self.count)
            node['body'] = body
        
        elif line[pos].kind == 'WHILE':
            pos += 1
            node = {'type': 'while'}
            condition = self.__parse_expression(line[pos:-1])
            if condition == None:
                raise ParseError('Expected an expression after "while" statemenent', self.count)
            node['condition'] = condition
            if line[len(line) - 1].kind != 'COLON':
                raise ParseError('Expected ":"', self.count)
            
            body = []
            while self.count + 1 < len(self.lines) and self.lines[self.count + 1][0] > level:
                inner = self.__parse_line()
                if (inner != None): body.append(inner)
            if len(body) == 0:
                raise ParseError('Expected an indented block after "while" statemenent', self.count)
            node['body'] = body
        
        elif line[pos].kind == 'PRINT':
            pos += 1 
            
            if pos >= len(line) or line[pos].kind != 'LPAR':
                raise ParseError('Expected "("', self.count)
            pos += 1
            
            expression = self.__parse_expression(line[pos:-1])
            if expression == None:
                raise ParseError('Expected an expression after "print"', self.count)

            if pos >= len(line) or line[-1].kind != 'RPAR':
                raise ParseError('Expected ")"', self.count)
            pos += 1
            
            node = {'type': 'print', 'expression': expression}
            
        
        elif line[pos].kind == 'ID':
            node = {'type': 'assignment', 'name': line[pos].value}
            pos += 1
            
            if pos >= len(line) or line[pos].kind != 'ASSIGN':
                node = self.__parse_expression(line)
                if node == None:
                    raise ParseError('Expected "="', self.count)
            else:
                pos += 1
                
                value = self.__parse_expression(line[pos:])
                pos += 1
                if pos < len(line):
                    next_token = line[pos:][0]
                    if next_token.kind == 'IF':
                        id_to_assign = line[pos-1]
                        line.append(id_to_assign)
                        ternary_operator = self.__parse_symbol(0, line[pos:])
                        ternary_operator = ternary_operator[1]
                        node['ternary'] = ternary_operator

                if value == None:
                    raise ParseError('Expected an expression after variable assignment', self.count)
                node['value'] = value
        
        else:
            node = self.__parse_expression(line)
            
        if node == None:
            raise ParseError('Unexpected symbol', self.count)
            
        return node
    
    def parse(self, tokens):
        self.lines = self.__tokens_to_lines(tokens)
        
        ast = []
        while self.count + 1 < len(self.lines):
            node = self.__parse_line()
            if node != None: ast.append(node)
         
        return ast