from brewparse import parse_program     # imports parser
from intbase import InterpreterBase 
from element import Element
from intbase import ErrorType

class Interpreter(InterpreterBase):
	
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)   # call InterpreterBase's constructor

    def get_main_func_node(self, ast):
        func_node_list = ast.get('functions')
        for node in func_node_list:
            if node.get('name') == 'main':
                return node

        super().error(
        ErrorType.NAME_ERROR,
        "No main() function was found",
        )
	
    def run(self, program):
        ast = parse_program(program) # parse program into AST
        self.variable_name_to_value = {}  # dict to hold variables
        # main_func_node = ast.get('functions')
        main_func_node = self.get_main_func_node(ast)

        self.run_func(main_func_node)

    def run_func(self, func_node_list):
        main_func_node = func_node_list
        for statement_node in main_func_node.get('statements'):
            # print(statement_node.get('name'))
            self.run_statement(statement_node)

        # # if there is more than one function in program 
        # for node in func_node_list:
        #     if (node.get('name') == 'main'):
        #         for statement_node in node.get('statements'):
        #             # print(statement_node.get('name'))
        #             self.run_statement(statement_node)

    def run_statement(self, statement_node):
        # print(statement_node.get('name'))
        if statement_node.elem_type == '=':
            # print("OMG EQUAL")
            self.do_assignment(statement_node)
        elif statement_node.elem_type == 'fcall':
            # print("FCALL")
            self.evaluate_expression(statement_node)

    def do_assignment(self, statement_node):
        target_var_name = statement_node.get('name')
        # print(target_var_name)
        source_node = statement_node.get('expression')
        # print(source_node)
        resulting_value = self.evaluate_expression(source_node)
        # print("Resulting val: " , resulting_value)
        self.variable_name_to_value[target_var_name] = resulting_value # map var to calculated value 

     
    def evaluate_expression(self, source_node):
        if source_node.elem_type == 'int':
            # print("FOUND")
            # print("Evaluate expression returns: ", source_node.get('val'))
            return ("int", source_node.get('val'))
        elif source_node.elem_type == 'string':
            # print("FOUND")
            # print("Evaluate expression returns: ", source_node.get('val'))
            return ("string", source_node.get('val'))
        elif source_node.elem_type == 'var':
            variable_name = source_node.get('name')
            if variable_name in self.variable_name_to_value:
                return (self.variable_name_to_value[variable_name])
            else: 
                super().error(
                    ErrorType.NAME_ERROR,
                    f"Variable '{variable_name}' is not defined.",
                )
            
        elif source_node.elem_type == '+': 
            operand_one = self.evaluate_expression(source_node.get('op1'))
            operand_two = self.evaluate_expression(source_node.get('op2'))

            if(operand_one[0] != operand_two[0]): # error checking
                super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible types for arithmetic operations.",
                )
            data_type = operand_one[0]

            return (data_type, operand_one[1] + operand_two[1]) 
        elif source_node.elem_type == '-':
            operand_one = self.evaluate_expression(source_node.get('op1'))
            operand_two = self.evaluate_expression(source_node.get('op2'))

            if(operand_one[0] != operand_two[0]): # error checking
                super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible types for arithmetic operations.",
                )
            data_type = operand_one[0]

            return (data_type, operand_one[1] - operand_two[1]) #recursively call until there's no more binary operators
        
        elif source_node.elem_type == 'fcall':
            if source_node.get('name') == 'print':
                output_string = ""
                for arg in source_node.get('args'):
                    output = self.evaluate_expression(arg)
                    output_string += str(output[1])
                super().output(output_string)

            elif source_node.get('name') == 'inputi':
                # inputi_node = source_node.get('name') # go into inputi node
                # get list of args in inputi
                inputi_arg = source_node.get('args') 
                if(len(inputi_arg) > 1):
                        super().error(
                        ErrorType.NAME_ERROR,
                        f"No inputi() function found that takes > 1 parameter",
                )         
                # print messsage inside inputi IF there is one
                elif (len(inputi_arg) == 1):
                    super().output(self.evaluate_expression(inputi_arg[0])[1])
                # obtain and return user input
                user_input = int(super().get_input())
                return ("int", user_input)
            
            else:
                super().error(
                ErrorType.NAME_ERROR,
                "Unknown function called.",
                )

        


            


def main():
  
    # program_source = """
    # func main() {
    #     y = 4;
    #     x = 5 - y;
    #     print("The sum is: ", x);
    # }
    # """

    # program_source = """
    #     func main() {
    #         y = 4;
    #         x = 5 + y;
    #         print("The sum is: ", x);
    #     }
    # """
    program_source = """
        func main() {
        x = 3 - (6 + (2 + 3));
    }
    """


    # program_source = """
    # func main() {
    # hello = 5;
    # }
    # """

    # program_source = """
    # func main() {
    # s = "str";
    # a = 8;
    # print(a, s, "hello", s);
    # }
    # """

    

    interpreter = Interpreter()
    interpreter.run(program_source)


if __name__ == '__main__':
    main()