from tokenizer import Token

class ParseError(Exception):
    def __init__(self, msg, line):
        self.msg = msg
        self.line = line
    
    def __str__(self):
        return 'Syntax error: {} on line {}'.format(self.msg, self.line)

class Parser:
    def __init__(self):
        self.lines = []
        self.number = -1
        pass
    
    def __convert_tokens_to_lines(self, tokens):
        lines = []
        
        for line in tokens:
            level = sum(1 for x in line if x.variation == 'TAB')
            lines.append((level, [x for x in line if x.variation != 'TAB']))
        
        return lines
    
    def __parse_char(self, start_position, line):
        entry = None
        position = start_position
        
        if position >= len(line):
            return entry
        
        if line[position].variation == 'NUMBER':
            position += 1
            entry = {'variation': 'number', 'value': line[position - 1].value}
        elif line[position].variation == 'ID':
            position += 1
            if position < len(line) and line[position].variation == 'LPAR':
                entry = {'variation': 'function_call', 'name': line[position - 1].value}
                position += 1
                parameters = []
                while line[position].variation != 'RPAR':
                    position, parameter = self.__parse_char(position, line)
                    if parameter == None:
                        raise ParseError('Expected parameter', self.number)
                    parameters.append(parameter)
                    if line[position].variation == 'COMMA':
                        position += 1
                
                entry['parameters'] = parameters
                
                if position >= len(line) or line[position].variation != 'RPAR':
                    raise ParseError('Expected ")"', self.number)

            else:
                entry = {'variation': 'id', 'name': line[position - 1].value}
        elif position < len(line) and line[position].variation == 'IF':
            entry = {'variation': 'if'}
            position += 1
            operation = line[position + 1]
            if operation.variation == 'LESS':
                line[position + 1].variation = 'GREATER'
                line[position + 1].value = '>'
            elif operation.variation == 'GREATER':
                line[position + 1].variation = 'LESS'
                line[position + 1].value = '<'
            condition = self.__parse_expression(line[position:-2])
            entry['condition'] = condition

            expression_body = []
            initial_value = self.__parse_char(0, line[-1:])
            initial_value = initial_value[1]
            false_value = self.__parse_char(0, line[-2:])
            false_value = false_value[1]
            assignment = {'variation': 'assignment', 'name': initial_value['name'], 'value': false_value}
            expression_body.append(assignment)
            entry['body'] = expression_body

        else:
            raise ParseError('Unexpected char "{}"'.format(line[position].value), self.number)
        
        return (position, entry)
    
    def __parse_expression(self, line):
        if len(line) == 0:
            return None
        
        position, operation = self.__parse_char(0, line)
        if operation == None: return None
        
        if position < len(line) and line[position].variation in ['PLUS', 'MINUS', 'MUL', 'LESS', 'GREATER', 'PERCENT', 'EQUALS']:
            operation2 = self.__parse_char(position + 1, line)
            if operation2 == None:
                raise ParseError('Expected second operand', self.number)
            return {'variation': line[position].variation.lower(), 'op1': operation, 'op2': operation2[1]}
        
        return operation
    
    def __parse_line(self):
        self.number += 1
        entry = None
        position = 0
        line = self.lines[self.number][1]
        nesting = self.lines[self.number][0]
        
        if len(line) == 0:
            return entry
        
        if line[position].variation == 'DEF':
            if nesting != 0:
                raise ParseError('Function cannot be nested', self.number)
            position += 1
            if position >= len(line) or line[position].variation != 'ID':
                raise ParseError('Expected function identifier', self.number)
            entry = {'variation': 'function', 'name': line[position].value}
            position += 1
            
            if position >= len(line) or line[position].variation != 'LPAR':
                raise ParseError('Expected "("', self.number)
            position += 1
            
            parameters = []
            while line[position].variation != 'RPAR':
                if line[position].variation != 'ID':
                    raise ParseError('Expected identifier', line[position])
                parameters.append(line[position].value)
                position += 1
                if line[position].variation == 'COMMA':
                    position += 1
            
            entry['parameters'] = parameters
            
            if position >= len(line) or line[position].variation != 'RPAR':
                raise ParseError('Expected ")"', self.number)
            position += 1
            
            if position >= len(line) or line[position].variation != 'COLON':
                raise ParseError('Expected ":"', self.number)
            
            body = []
            while self.number + 1 < len(self.lines) and self.lines[self.number + 1][0] > nesting:
                inner_body = self.__parse_line()
                if (inner_body != None): body.append(inner_body)
            if len(body) == 0:
                raise ParseError('Expected an indented block after function definition', self.number)
            entry['body'] = body
        
        elif line[position].variation == 'RET':
            position += 1
            entry = {'variation': 'return'}
            expression = self.__parse_expression(line[position:])
            if expression == None:
                raise ParseError('Expected an expression after return', self.number)
            entry['expression'] = expression
        
        elif line[position].variation == 'IF':
            position += 1
            entry = {'variation': 'if'}
            condition = self.__parse_expression(line[position:-1])
            if condition == None:
                raise ParseError('Expected an expression after "if" statemenent', self.number)
            entry['condition'] = condition
            if line[len(line) - 1].variation != 'COLON':
                raise ParseError('Expected ":"', self.number)
            
            body = []
            while self.number + 1 < len(self.lines) and self.lines[self.number + 1][0] > nesting:
                inner_body = self.__parse_line()
                if (inner_body != None): body.append(inner_body)
            if len(body) == 0:
                raise ParseError('Expected an indented block after "if" statemenent', self.number)
            entry['body'] = body
        
        elif line[position].variation == 'WHILE':
            position += 1
            entry = {'variation': 'while'}
            condition = self.__parse_expression(line[position:-1])
            if condition == None:
                raise ParseError('Expected an expression after "while" statemenent', self.number)
            entry['condition'] = condition
            if line[len(line) - 1].variation != 'COLON':
                raise ParseError('Expected ":"', self.number)
            
            body = []
            while self.number + 1 < len(self.lines) and self.lines[self.number + 1][0] > nesting:
                inner_body = self.__parse_line()
                if (inner_body != None): body.append(inner_body)
            if len(body) == 0:
                raise ParseError('Expected an indented block after "while" statemenent', self.number)
            entry['body'] = body
        
        elif line[position].variation == 'PRINT':
            position += 1
            
            if position >= len(line) or line[position].variation != 'LPAR':
                raise ParseError('Expected "("', self.number)
            position += 1
            
            expression = self.__parse_expression(line[position:-1])
            if expression == None:
                raise ParseError('Expected an expression after "print"', self.number)

            if position >= len(line) or line[-1].variation != 'RPAR':
                raise ParseError('Expected ")"', self.number)
            position += 1
            
            entry = {'variation': 'print', 'expression': expression}
            
        
        elif line[position].variation == 'ID':
            entry = {'variation': 'assignment', 'name': line[position].value}
            position += 1
            
            if position >= len(line) or line[position].variation != 'ASSIGN':
                entry = self.__parse_expression(line)
                if entry == None:
                    raise ParseError('Expected "="', self.number)
            else:
                position += 1
                
                value = self.__parse_expression(line[position:])
                position += 1
                if position < len(line):
                    next_token = line[position:][0]
                    if next_token.variation == 'IF':
                        id_to_assign = line[position-1]
                        line.append(id_to_assign)
                        ternary_operator = self.__parse_char(0, line[position:])
                        ternary_operator = ternary_operator[1]
                        entry['ternary'] = ternary_operator

                if value == None:
                    raise ParseError('Expected an expression after variable assignment', self.number)
                entry['value'] = value
        
        else:
            entry = self.__parse_expression(line)
            
        if entry == None:
            raise ParseError('Unexpected symbol', self.number)
            
        return entry
    
    def parse(self, tokens):
        self.lines = self.__convert_tokens_to_lines(tokens)
        
        parsed = []
        while self.number + 1 < len(self.lines):
            entry = self.__parse_line()
            if entry != None: parsed.append(entry)
         
        return parsed