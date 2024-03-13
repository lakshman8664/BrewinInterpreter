from env_v1 import EnvironmentManager
from type_valuev1 import Type, Value, create_value, get_printable
from intbase import InterpreterBase, ErrorType
from brewparse import parse_program
import copy 


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">=", "!", "neg", "||", "&&"}

    # methods
    def __init__(self, console_output=True, inp=None, trace_output=False):
        super().__init__(console_output, inp)
        self.trace_output = trace_output
        self.__setup_ops()

    # run a program that's provided in a string
    # usese the provided Parser found in brewparse.py to parse the program
    # into an abstract syntax tree (ast)
    def run(self, program):
        ast = parse_program(program)
        self.__set_up_function_table(ast)
        main_func = self.__get_func_by_name("main")
        self.env = EnvironmentManager()
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            self.func_name_to_ast[func_def.get("name")] = func_def
            # self.__eval_func(func_def)

    def __eval_func(self, func_node):
        args = func_node.get('args')
        self.arg_name_to_val = {}
        if args != None: #if not None, evaluate args 
            for arg in args:
                var_name = arg.get('name')
                val = self.env.get(var_name)
                if val is None:
                    super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
                self.arg_name_to_val[var_name] = val

        self.__run_statements(func_node.get('statements')) 

    def __get_func_by_name(self, name):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        return self.func_name_to_ast[name]

    def __run_statements(self, statements):
        # all statements of a function are held in arg3 of the function AST node
        for statement in statements:
            if self.trace_output:
                print(statement)
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == "if":
                self.__evaluate_if_condition(statement)
            elif statement.elem_type == "while":
                self.__evaluate_while_condition(statement)
            elif statement.elem_type == "return":
                return self.__evaluate_return(statement)
        return Interpreter.NIL_VALUE
    
    def __evaluate_return(self, return_statement):
        expression = self.__eval_expr(return_statement.get('expression'))
        if expression is None:
            return expression #return nil
        else:
            deep_copy_val = copy.deepcopy(expression) #save a deep copy of value
            return deep_copy_val

    
    def __evaluate_while_condition(self, while_ast):
        condition_passed = self.__eval_expr(while_ast.get('condition'))
        # print(condition_passed.type)

        # if (condition_passed.type[0] != Type.BOOL):
        #     super().error(
        #         ErrorType.NAME_ERROR, "While loop conditional statement does not evaluate to a boolean."
        #     )
        while(condition_passed.v is True):
            self.__run_statements(while_ast.get('statements'))
            condition_passed = self.__eval_expr(while_ast.get('condition'))
    
    def __evaluate_if_condition(self, if_ast):
        condition_passed = self.__eval_expr(if_ast.get('condition'))
        if(condition_passed.v is True):
            self.__run_statements(if_ast.get('statements'))
        else:
            else_statements = if_ast.get('else_statements')
            if(else_statements != None):
                self.__run_statements(if_ast.get('else_statements'))

    def __call_func(self, call_node):
        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)

        # add code here later to call other functions
        super().error(ErrorType.NAME_ERROR, f"Function {func_name} not found")

    def __call_print(self, call_ast):
        output = ""
        for arg in call_ast.get("args"):
            result = self.__eval_expr(arg)  # result is a Value object
            output = output + get_printable(result)
        super().output(output)
        return Interpreter.NIL_VALUE

    def __call_input(self, call_ast):
        args = call_ast.get("args")
        if args is not None and len(args) == 1:
            result = self.__eval_expr(args[0])
            super().output(get_printable(result))
        elif args is not None and len(args) > 1:
            super().error(
                ErrorType.NAME_ERROR, "No inputi() function that takes > 1 parameter"
            )
        inp = super().get_input()
        if call_ast.get("name") == "inputi":
            return Value(Type.INT, int(inp))
        # we can support inputs here later

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        self.env.set(var_name, value_obj)

    def __eval_expr(self, expr_ast):
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.NIL_DEF:
            return Value(Type.NIL, expr_ast.get("val"))
        
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)
            if val is None:
                super().error(ErrorType.NAME_ERROR, f"Variable {var_name} not found")
            return val
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))

        if (arith_ast.elem_type != "neg") & (arith_ast.elem_type != "!"): # if operation is unary, don't look for op2
            right_value_obj = self.__eval_expr(arith_ast.get("op2"))

            if (arith_ast.elem_type != "==") & (arith_ast.elem_type != "!="): # if operation is == or !=, types don't need to be same
                if left_value_obj.type() != right_value_obj.type() : 
                    super().error(
                        ErrorType.TYPE_ERROR,
                        f"Incompatible types for {arith_ast.elem_type} operation",
                    )
        if arith_ast.elem_type not in self.op_to_lambda[left_value_obj.type()]:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible operator {arith_ast.elem_type} for type {left_value_obj.type()}",
            )
        f = self.op_to_lambda[left_value_obj.type()][arith_ast.elem_type]

        # if unary, return only op1 
        if (arith_ast.elem_type == "neg") | (arith_ast.elem_type == "!"):
            return f(left_value_obj)
        
        return f(left_value_obj, right_value_obj)

    def __setup_ops(self):
        self.op_to_lambda = {}
        # set up operations on integers
        self.op_to_lambda[Type.INT] = {}
        self.op_to_lambda[Type.INT]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.INT]["-"] = lambda x, y: Value(
            x.type(), x.value() - y.value()
        )
        self.op_to_lambda[Type.INT]["*"] = lambda x, y: Value(
            x.type(), x.value() * y.value()
        )
        self.op_to_lambda[Type.INT]["/"] = lambda x, y: Value(
            x.type(), x.value() // y.value()
        )
        self.op_to_lambda[Type.INT]["neg"] = lambda x: Value(
            x.type(), -1 * x.value()
        )
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        self.op_to_lambda[Type.INT]["<"] = lambda x, y: Value(
            Type.BOOL, x.value() < y.value()
        )
        self.op_to_lambda[Type.INT]["<="] = lambda x, y: Value(
            Type.BOOL, x.value() <= y.value()
        )
        self.op_to_lambda[Type.INT][">"] = lambda x, y: Value(
            Type.BOOL, x.value() > y.value()
        )
        self.op_to_lambda[Type.INT][">="] = lambda x, y: Value(
            Type.BOOL, x.value() >= y.value()
        )

        # set up operations on string
        self.op_to_lambda[Type.STRING] = {}
        self.op_to_lambda[Type.STRING]["+"] = lambda x, y: Value(
            x.type(), x.value() + y.value()
        )
        self.op_to_lambda[Type.STRING]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.STRING]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )

         # set up operations on bool
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            x.type(), x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            x.type(), x.value() != y.value()
        )
        self.op_to_lambda[Type.BOOL]["!"] = lambda x: Value(
            x.type(), not x.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() | y.value()
        )
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() & y.value()
        )

        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.value() != y.value()
        )
        # add other operators here later for int, string, bool, etc



def main():
  
    program_source = """
    func main() {
        x = nil;
        if (x != true) {
            print(5);
        }
    }
    """

    # program_source = """
    #     func main() {
    #         x = 3;
    #         if (x > 5) {
    #             print(x);
    #             if (x < 30 && x > 10) {
    #                 print(3*x);
    #             }
    #             else{
    #                 print("jello");
    #             }
    #         }
    #         else{
    #             print("yo");
    #         }
    #     }
    #     """
    # program_source = """
    #     func main() {
    #     x = "str";
    #     y = "concat";
    #     a = 7 * 5;
    #     print(9*4);
    # }
    # """

    

    interpreter = Interpreter()
    interpreter.run(program_source)


if __name__ == '__main__':
    main()