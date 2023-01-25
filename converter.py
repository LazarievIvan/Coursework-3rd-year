class SemanticError(Exception):
    def __init__(self, msg):
        self.msg = msg
    
    def __str__(self):
        return 'Semantic Error: {}'.format(self.msg)

class Converter:
    script_start = """
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
start_position:
invoke main
invoke ExitProcess, 0
"""
    
    binary_operations = [
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
        self.jump_counter = 0
    
    def __convert_expression(self, entry, variables):
        variation = entry['variation']
        
        if variation == 'number':
            return ['push {}'.format(entry['value'])]
        
        if variation == 'id':
            name = entry['name']
            
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
        
        if variation == 'function_call':
            name = entry['name']
            parameters = entry['parameters']
            code = []
            for parameter in parameters:
                code.extend(self.__convert_expression(parameter, variables))
            return code + [
                'call {}'.format(name),
                'add esp, {}'.format(4 * len(parameters)),
                'push ebx'
            ]
        
        if variation in self.binary_operations:
            op1 = self.__convert_expression(entry['op1'], variables)
            op2 = self.__convert_expression(entry['op2'], variables)
            
            if variation == 'plus':
                return op1 + op2 + [
                    'pop eax',
                    'pop ebx',
                    'add ebx, eax',
                    'push ebx'
                ]
            
            if variation == 'minus':
                return op1 + op2 + [
                    'pop eax',
                    'pop ebx',
                    'sub ebx, eax',
                    'push ebx'
                ]
            
            if variation == 'mul':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'mul ebx',
                    'push eax'
                ]
            
            if variation == 'percent':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cdq',
                    'idiv ebx',
                    'push edx'
                ]
            
            if variation == 'less':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'setl al',
                    'push eax'
                ]
            
            if variation == 'greater':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'setg al',
                    'push eax'
                ]
            
            if variation == 'equals':
                return op1 + op2 + [
                    'pop ebx',
                    'pop eax',
                    'cmp eax, ebx',
                    'mov eax, 0',
                    'sete al',
                    'push eax'
                ]
        
        raise SemanticError('Unknown operation "{}"'.format(variation))
    
    def __convert_inner(self, entry, variables):
        variation = entry['variation']
        
        if variation == 'return':
            return self.__convert_expression(entry['expression'], variables) + [
                'pop ebx',
                'mov esp, ebp',
                'pop ebp',
                'ret'
            ]
        
        if variation == 'assignment':
            name = entry['name']
            node_value = entry['value']
            value = self.__convert_expression(node_value, variables)
            ternary_operator = []
            if 'ternary' in entry:
                ternary_operator = self.__convert_inner(entry['ternary'], variables)
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
        
        if variation == 'if':
            condition = self.__convert_expression(entry['condition'], variables)
            body = []
            for inner_entry in entry['body']:
                body.extend(self.__convert_inner(inner_entry, variables))
            self.jump_counter += 1
            return condition + [
                'pop ebx',
                'cmp ebx, 0',
                'je _if_end_{}'.format(self.jump_counter)
            ] + body + [
                '_if_end_{}:'.format(self.jump_counter)
            ]
        
        if variation == 'while':
            condition = self.__convert_expression(entry['condition'], variables)
            body = []
            for inner_entry in entry['body']:
                body.extend(self.__convert_inner(inner_entry, variables))
            self.jump_counter += 1
            return ['_while_{}:'.format(self.jump_counter)] + condition + [
                'pop eax',
                'cmp eax, 0',
                'je _while_end_{}'.format(self.jump_counter)
            ] + body + [
                'jmp _while_{}'.format(self.jump_counter),
                '_while_end_{}:'.format(self.jump_counter)
            ]
        
        if variation == 'print':
            return self.__convert_expression(entry['expression'], variables) + [
                'call __print'
            ]
        
        raise SemanticError('Unknow operation "{}"'.format(variation))
    
    def __convert_function(self, function):
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
            code.extend(self.__convert_inner(node, variables))
            
        code.append('{} endp'.format(name))
        
        return code
    
    def convert(self, parsed):
        main = {
            'variation': 'function',
            'name': 'main',
            'parameters': [], 
            'body': []}
        functions = []
        
        for entry in parsed:
            if entry['variation'] == 'function':
                if entry['name'] in self.function_ids:
                    raise SemanticError('Function "{}" is already defined'.format(entry['name']))
                functions.append(self.__convert_function(entry))
                self.function_ids.append(entry['name'])
            else:
                main['body'].append(entry)
        
        main['body'].append({
            'variation': 'return',
            'expression': {
                'variation': 'number',
                'value': '0'
            }})
        functions.append(self.__convert_function(main))
        
        code = []
        for function in functions:
            code.append('\n'.join(function))
        
        return "{}\n{}\n{}".format(self.script_start, '\n\n'.join(code), 'end start_position')
