import copy
from enum import Enum

from brewparse import parse_program
from env_v2 import EnvironmentManager, Lambda
from intbase import InterpreterBase, ErrorType
from type_valuev2 import Type, Value, create_value, get_printable


class ExecStatus(Enum):
    CONTINUE = 1
    RETURN = 2


# Main interpreter class
class Interpreter(InterpreterBase):
    # constants
    NIL_VALUE = create_value(InterpreterBase.NIL_DEF)
    TRUE_VALUE = create_value(InterpreterBase.TRUE_DEF)
    BIN_OPS = {"+", "-", "*", "/", "==", "!=", ">", ">=", "<", "<=", "||", "&&"}

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
        self.env = EnvironmentManager()
        main_func = self.__get_func_by_name("main", 0)
        self.__run_statements(main_func.get("statements"))

    def __set_up_function_table(self, ast):
        self.func_name_to_ast = {}
        for func_def in ast.get("functions"):
            func_name = func_def.get("name")
            num_params = len(func_def.get("args"))
            if func_name not in self.func_name_to_ast:
                self.func_name_to_ast[func_name] = {}
            self.func_name_to_ast[func_name][num_params] = func_def

    def __get_func_by_name(self, name, num_params):
        if name not in self.func_name_to_ast:
            super().error(ErrorType.NAME_ERROR, f"Function {name} not found")
        candidate_funcs = self.func_name_to_ast[name]
        if num_params not in candidate_funcs:
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {name} taking {num_params} params not found",
            )
        return candidate_funcs[num_params]

    def __run_statements(self, statements):
        self.env.push()
        for statement in statements:
            if self.trace_output:
                print(statement)
            status = ExecStatus.CONTINUE
            if statement.elem_type == InterpreterBase.FCALL_DEF:
                self.__call_func(statement)
            elif statement.elem_type == "=":
                self.__assign(statement)
            elif statement.elem_type == InterpreterBase.RETURN_DEF:
                status, return_val = self.__do_return(statement)
            elif statement.elem_type == Interpreter.IF_DEF:
                status, return_val = self.__do_if(statement)
            elif statement.elem_type == Interpreter.WHILE_DEF:
                status, return_val = self.__do_while(statement)

            if status == ExecStatus.RETURN:
                self.env.pop()
                return (status, return_val)

        self.env.pop()
        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __call_func(self, call_node):

        func_name = call_node.get("name")
        if func_name == "print":
            return self.__call_print(call_node)
        if func_name == "inputi":
            return self.__call_input(call_node)
        if func_name == "inputs":
            return self.__call_input(call_node)
        
        actual_args = call_node.get("args") # calling function arguments
        
        func_object = self.env.get(func_name) # get lambda object created in create_lambda_object OR return None if its not a lambda func
        
        # LAMBDA FUNCTION
        if func_object != None:
            if (func_object.type() == Type.FUNCTION):
                func_ast = func_object.value()
                self.env.push()
            elif ((func_object.type()) == Type.LAMBDA):
                lambda_env = func_object.value().env
                self.env.environment.append(lambda_env) # append lambda env to stack
                func_ast = func_object.value().lambda_ast
            else:
                super().error(ErrorType.TYPE_ERROR, f"Bad function call.")
        else: # REGULAR FUNCTION
            # obtain callee function node & formal args 
            func_ast = self.__get_func_by_name(func_name, len(actual_args)) 
            self.env.push()

        formal_args = func_ast.get("args") # callee function arguments 

        if len(actual_args) != len(formal_args):
            super().error(
                ErrorType.NAME_ERROR,
                f"Function {func_ast.get('name')} with {len(actual_args)} args not found",
            )

        refarg_to_actual = {} # maps REF ARG to ORIGINAL variable name 
        for formal_ast, actual_ast in zip(formal_args, actual_args):
            result = copy.deepcopy(self.__eval_expr(actual_ast))
            arg_name = formal_ast.get("name")
            if formal_ast.elem_type == 'arg':
                self.env.create(arg_name, result)
            elif formal_ast.elem_type == 'refarg':
                # map refarg to original var to original value  
                refarg_to_actual[arg_name] = actual_ast.get('name')
                self.env.create(arg_name, result)

        _, return_val = self.__run_statements(func_ast.get("statements"))

        # loop through and find all params by ref
        vals_to_values = {} # dict that maps ORIGINAL var to NEW value 
        for ref_arg in formal_args:
            if ref_arg.elem_type == "refarg":
                # get its new value AFTER function has run
                new_refarg_value = self.env.get(ref_arg.get('name'))
                original_var_name = refarg_to_actual[ref_arg.get('name')]
                # map ORIGINAL variable to NEW value 
                vals_to_values[original_var_name] = new_refarg_value
        self.env.pop()
        #after most recent env is gone, go through dict and assign each var its NEW value 
        for var_name, value in vals_to_values.items():
            self.env.set(var_name, value)

        return return_val
    

    def __create_lambda_object(self, lambda_node):
        # args = lambda_node.get('args')

        lambda_env = self.env.flatten()

        lambda_func = Lambda(lambda_env, lambda_node)

        return Value(Type.LAMBDA, lambda_func)

        # lambda goes thorugh args and creates env 
        # lambda env has access to all env 
        # lambda has access to all env so that all vars can be captured 
        # when lambda is DONE running, lambda env should be stored somewhere on the side 

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
        if call_ast.get("name") == "inputs":
            return Value(Type.STRING, inp)

    def __assign(self, assign_ast):
        var_name = assign_ast.get("name")
        value_obj = self.__eval_expr(assign_ast.get("expression"))
        
        self.env.set(var_name, value_obj)

    def __eval_expr(self, expr_ast):
        # print("here expr")
        # print("type: " + str(expr_ast.elem_type))
        if expr_ast.elem_type == InterpreterBase.NIL_DEF:
            # print("getting as nil")
            return Interpreter.NIL_VALUE
        if expr_ast.elem_type == InterpreterBase.INT_DEF:
            return Value(Type.INT, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.STRING_DEF:
            # print("getting as str")
            return Value(Type.STRING, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.BOOL_DEF:
            return Value(Type.BOOL, expr_ast.get("val"))
        if expr_ast.elem_type == InterpreterBase.VAR_DEF:
            var_name = expr_ast.get("name")
            val = self.env.get(var_name)

            if var_name not in self.func_name_to_ast:
                candidate_funcs = None
            else:
                candidate_funcs = self.func_name_to_ast[var_name]

            # if val is None, its a function
            if val is not None:
                return val
            elif candidate_funcs is not None:
                if len(candidate_funcs) > 1:
                    super().error(ErrorType.NAME_ERROR, f"Multiple functions with name {var_name}.")

                num_args, function = list(candidate_funcs.items())[0]
                return Value(Type.FUNCTION, function)

            
            else: #both candidate_funcs and val is None
                super().error(ErrorType.NAME_ERROR, f"Function {var_name} not found")
        if expr_ast.elem_type == InterpreterBase.FCALL_DEF:
            return self.__call_func(expr_ast)
        if expr_ast.elem_type in Interpreter.BIN_OPS:
            return self.__eval_op(expr_ast)
        if expr_ast.elem_type == Interpreter.NEG_DEF:
            return self.__eval_unary(expr_ast, Type.INT, lambda x: -1 * x)
        if expr_ast.elem_type == Interpreter.NOT_DEF:
            return self.__eval_unary(expr_ast, Type.BOOL, lambda x: not x)
        if expr_ast.elem_type == Interpreter.LAMBDA_DEF:
            return self.__create_lambda_object(expr_ast)
            # return Value(Type.LAMBDA, self.env.flatten())

    def __eval_op(self, arith_ast):
        left_value_obj = self.__eval_expr(arith_ast.get("op1"))
        right_value_obj = self.__eval_expr(arith_ast.get("op2"))

        if arith_ast.elem_type in ['+', '-', '/', '*']:
            if right_value_obj.type() == Type.BOOL:
                if(right_value_obj.value() == False):
                    right_value_obj = Value(Type.INT, 0)
                else:
                    right_value_obj = Value(Type.INT, 1)
            if left_value_obj.type() == Type.BOOL:
                if(left_value_obj.value() == False):
                    left_value_obj = Value(Type.INT, 0)
                else:
                    left_value_obj = Value(Type.INT, 1)

        if arith_ast.elem_type in ['==', '!=', '&&', '||']:
            if right_value_obj.type() == Type.INT:
                if(right_value_obj.value() == 0):
                    right_value_obj = Value(Type.BOOL, False)
                else:
                    right_value_obj = Value(Type.BOOL, True)
            if left_value_obj.type() == Type.INT:
                if(left_value_obj.value() == 0):
                    left_value_obj = Value(Type.BOOL, False)
                else:
                    left_value_obj = Value(Type.BOOL, True)

        if not self.__compatible_types(
            arith_ast.elem_type, left_value_obj, right_value_obj
        ):
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
        # print("here eval")
        # print(arith_ast)
        # print("evaluating " + str(left_value_obj.type()) + " " + str(arith_ast.elem_type))
        # print("obj left: " + str(left_value_obj.value()))
        return f(left_value_obj, right_value_obj)

    def __compatible_types(self, oper, obj1, obj2):
        # DOCUMENT: allow comparisons ==/!= of anything against anything
        if oper in ["==", "!="]:
            return True
        return obj1.type() == obj2.type()

    def __eval_unary(self, arith_ast, t, f):
        value_obj = self.__eval_expr(arith_ast.get("op1"))
        if arith_ast.elem_type == '!':
            if value_obj.type() == Type.INT:
                if(value_obj.value() == 0):
                    value_obj = Value(Type.BOOL, False)
                else:
                    value_obj = Value(Type.BOOL, True)

        if value_obj.type() != t:
            super().error(
                ErrorType.TYPE_ERROR,
                f"Incompatible type for {arith_ast.elem_type} operation",
            )
        return Value(t, f(value_obj.value()))

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
        self.op_to_lambda[Type.INT]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.INT]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
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
        #  set up operations on strings
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
        #  set up operations on bools
        self.op_to_lambda[Type.BOOL] = {}
        self.op_to_lambda[Type.BOOL]["&&"] = lambda x, y: Value(
            x.type(), x.value() and y.value()
        )
        self.op_to_lambda[Type.BOOL]["||"] = lambda x, y: Value(
            x.type(), x.value() or y.value()
        )
        self.op_to_lambda[Type.BOOL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.BOOL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on nil
        self.op_to_lambda[Type.NIL] = {}
        self.op_to_lambda[Type.NIL]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.NIL]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on lambda
        self.op_to_lambda[Type.LAMBDA] = {}
        self.op_to_lambda[Type.LAMBDA]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.LAMBDA]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

        #  set up operations on lambda
        self.op_to_lambda[Type.FUNCTION] = {}
        self.op_to_lambda[Type.FUNCTION]["=="] = lambda x, y: Value(
            Type.BOOL, x.type() == y.type() and x.value() == y.value()
        )
        self.op_to_lambda[Type.FUNCTION]["!="] = lambda x, y: Value(
            Type.BOOL, x.type() != y.type() or x.value() != y.value()
        )

    def __do_if(self, if_ast):
        cond_ast = if_ast.get("condition")

        result = self.__eval_expr(cond_ast)

        # check for int -> bool coercion 
        if result.type() == Type.INT:
            if(result.value() == 0):
                result = Value(Type.BOOL, False)
            else:
                result = Value(Type.BOOL, True)


        if result.type() != Type.BOOL:
            super().error(
                ErrorType.TYPE_ERROR,
                "Incompatible type for if condition",
            )
        if result.value():
            statements = if_ast.get("statements")
            status, return_val = self.__run_statements(statements)
            return (status, return_val)
        else:
            else_statements = if_ast.get("else_statements")
            if else_statements is not None:
                status, return_val = self.__run_statements(else_statements)
                return (status, return_val)

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_while(self, while_ast):
        cond_ast = while_ast.get("condition")

        run_while = Interpreter.TRUE_VALUE
        while run_while.value():
            run_while = self.__eval_expr(cond_ast)

            # check for int -> bool coercion 
            if run_while.type() == Type.INT:
                if(run_while.value() == 0):
                    run_while = Value(Type.BOOL, False)
                else:
                    run_while = Value(Type.BOOL, True)

            if run_while.type() != Type.BOOL:
                super().error(
                    ErrorType.TYPE_ERROR,
                    "Incompatible type for while condition",
                )
            if run_while.value():
                statements = while_ast.get("statements")
                status, return_val = self.__run_statements(statements)
                if status == ExecStatus.RETURN:
                    return status, return_val

        return (ExecStatus.CONTINUE, Interpreter.NIL_VALUE)

    def __do_return(self, return_ast):
        expr_ast = return_ast.get("expression")
        if expr_ast is None:
            return (ExecStatus.RETURN, Interpreter.NIL_VALUE)
        value_obj = copy.deepcopy(self.__eval_expr(expr_ast))
        return (ExecStatus.RETURN, value_obj)
    


# program_source = """
# func foo() { return bar; }

# func bar(a,b) { print(a,b); }

# func main() {
#  a = foo();
#  a(10,20);
# }

# /*
# *OUT*
# 1020
# *OUT*
# */

#     """

# interpreter = Interpreter()
# interpreter.run(program_source)