class SemanticError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return 'SemanticError: {}'.format(self.msg)

class Generator:
    text_start = """
.386
.model flat, stdcall
include \masm32\include\masm32rt.inc
main proto
.data
.code
__print proc
    push  ebp 
    mov   ebp, esp
    fn MessageBox, 0, str$(8[ebp]), "Result", MB_OK
    pop   ebp
    ret
__print endp
start:
invoke main
invoke ExitProcess, 0
"""
    
    binary_ops = [
        'plus',
        'minus',
        'mul',
        'percent',
        'less',
        'greater',
        'equals'
    ]
    
    def __init__(self):
        self.function_ids = []
        self.jmp_counter = 0
    
    def __generate_expression(self, node, variables):
        type = node['type']
        
        if type == 'number':
            return ['push {}'.format(node['value'])]
        
        if type == 'id':
            name = node['name']
            
            if name == 'True':
                return ['push 1']
            elif name == 'False':
                return ['push 0']
            
            if name not in variables[1]:
                raise SemanticError('Variable "{}" is undefined'.format(name))
            return [
                'mov eax, [ebp{:+}]'.format(variables[1][name]),
                'push eax'
            ]
        
        if type == 'function_call':    
            name = node['name']
            parameters = node['parameters']
            code = []
            for parameter in parameters:
                code.extend(self.__generate_expression(parameter, variables))
            return code + [
                'call {}'.format(name),
                'add esp, {}'.format(4 * len(parameters)),
                'push ebx'
            ]
        
        if type in self.binary_ops:
            op1 = self.__generate_expression(node['op1'], variables)
            op2 = self.__generate_expression(node['op2'], variables)
            
            if type == 'plus':
                return op1 + op2 + [
                    'pop eax',
                    'pop ebx',
                    'add ebx, eax',
                    'push ebx'
                ]
            
            if type == 'minus':
                return op1 + op2 + [
                    'pop eax',
                    'pop ebx',
                    'sub ebx, eax',
                    'push ebx'
                ]
            
            if type == 'mul':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'mul ebx',
                    'push eax'
                ]
            
            if type == 'percent':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cdq',
                    'idiv ebx',
                    'push edx'
                ]
            
            if type == 'less':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'setl al',
                    'push eax'
                ]
            
            if type == 'greater':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'setg al',
                    'push eax'
                ]
            
            if type == 'equals':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'sete al',
                    'push eax'
                ]
        
        raise SemanticError('Unknow operation "{}"'.format(type))
    
    def __generate_inner(self, node, variables):
        type = node['type']
        
        if type == 'return':
            return self.__generate_expression(node['expression'], variables) + [
                'pop ebx',
                'mov esp, ebp',
                'pop ebp',
                'ret'
            ]
        
        if type == 'assignment':
            name = node['name']
            node_value = node['value']
            value = self.__generate_expression(node_value, variables)
            ternary_operator = []
            if 'ternary' in node:
                ternary_operator = self.__generate_inner(node['ternary'], variables)
            code = []
            
            if name not in variables[1]:
                variables[0] -= 1
                variables[1][name] = variables[0] * 4
                code.append('sub esp, 4')
            
            code.extend(value)
            
            return code + [
                'pop ebx',
                'mov [ebp{:+}], ebx'.format(variables[1][name])
            ] + ternary_operator
        
        if type == 'if':
            condition = self.__generate_expression(node['condition'], variables)
            body = []
            for inner_node in node['body']:
                body.extend(self.__generate_inner(inner_node, variables))
            self.jmp_counter += 1
            return condition + [
                'pop ebx',
                'cmp ebx, 0',
                'je _if_end_{}'.format(self.jmp_counter)
            ] + body + [
                '_if_end_{}:'.format(self.jmp_counter)
            ]
        
        if type == 'while':
            condition = self.__generate_expression(node['condition'], variables)
            body = []
            for inner_node in node['body']:
                body.extend(self.__generate_inner(inner_node, variables))
            self.jmp_counter += 1
            return ['_while_{}:'.format(self.jmp_counter)] + condition + [
                'pop eax',
                'cmp eax, 0',
                'je _while_end_{}'.format(self.jmp_counter)
            ] + body + [
                'jmp _while_{}'.format(self.jmp_counter),
                '_while_end_{}:'.format(self.jmp_counter)
            ]
        
        if type == 'print':
            return self.__generate_expression(node['expression'], variables) + [
                'call __print'
            ]
        
        raise SemanticError('Unknow operation "{}"'.format(type))
    
    def __generate_function(self, function):
        name = function['name']
        parameters = function['parameters']
        variables = [0, {}]
        
        code = [
            '{} proc'.format(name),
            'push ebp',
            'mov ebp, esp'
        ]
        
        i = 2
        for parameter in parameters:
            variables[1][parameter] = i * 4
            i += 1
        
        for node in function['body']:
            code.extend(self.__generate_inner(node, variables))
            
        code.append('{} endp'.format(name))
        
        return code
    
    def generate(self, ast):
        main_function = {
            'type': 'function',
            'name': 'main',
            'parameters': [], 
            'body': [] }
        functions = []
        
        for node in ast:
            if node['type'] == 'function':
                if node['name'] in self.function_ids:
                    raise SemanticError('Function "{}" is already defined'.format(node['name']))
                functions.append(self.__generate_function(node))
                self.function_ids.append(node['name'])
            else:
                main_function['body'].append(node)
        
        main_function['body'].append({
            'type': 'return', 
            'expression': {
                'type': 'number',
                'value': '0'
            }})
        functions.append(self.__generate_function(main_function))
        
        code = []
        for function in functions:
            code.append('\n'.join(function))
        
        return "{}\n{}\n{}".format(self.text_start, '\n\n'.join(code), 'end start')
        
        
        
        
        
        
        