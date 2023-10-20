# Base class for our interpreter
from enum import Enum


class ErrorType(Enum):
    TYPE_ERROR = 1
    NAME_ERROR = 2  # if a variable or function name can't be found
    FAULT_ERROR = 3  # used if an object reference is null and used to make a call
    # Add others here


class InterpreterBase:
    # AST node types
    PROGRAM_DEF = "program"
    FUNC_DEF = "func"
    LAMBDA_DEF = "lambda"
    NIL_DEF = "nil"
    IF_DEF = "if"
    WHILE_DEF = "while"
    ARG_DEF = "arg"
    REFARG_DEF = "refarg"
    NEG_DEF = "neg"
    RETURN_DEF = "return"
    INT_DEF = "int"
    BOOL_DEF = "bool"
    STRING_DEF = "string"
    FCALL_DEF = "fcall"
    MCALL_DEF = "mcall"
    TRUE_DEF = "true"
    FALSE_DEF = "false"
    THIS_DEF = "this"
    VAR_DEF = "var"
    OBJ_DEF = "@"
    NOT_DEF = "!"

    # methods
    def __init__(self, console_output=True, inp=None):
        self.console_output = console_output
        self.inp = inp  # if not none, then read input from passed-in list
        self.reset()

    # Call to reset I/O for another run of the program
    def reset(self):
        self.output_log = []
        self.input_cursor = 0
        self.error_type = None
        self.error_line = None

    # Students must implement this in their derived class
    def run(self, program):
        pass

    def get_input(self):
        if not self.inp:
            return input()  # Get input from keyboard if not input list provided

        if self.input_cursor < len(self.inp):
            cur_input = self.inp[self.input_cursor]
            self.input_cursor += 1
            return cur_input
        return None

    # students must call this for any errors that they run into
    def error(self, error_type, description=None, line_num=None):
        # log the error before we throw
        self.error_line = line_num
        self.error_type = error_type

        if description:
            description = ": " + description
        else:
            description = ""
        if not line_num:
            raise Exception(f"{error_type}{description}")
        raise Exception(f"{error_type} on line {line_num}{description}")

    def output(self, v):
        if self.console_output:
            print(v)
        self.output_log.append(v)

    def get_output(self):
        return self.output_log

    def get_error_type_and_line(self):
        return self.error_type, self.error_line
