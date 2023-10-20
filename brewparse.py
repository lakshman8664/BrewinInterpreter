from element import Element
from brewlex import *
from intbase import InterpreterBase
from ply import yacc

# Parsing rules

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("left", "GREATER_EQ", "GREATER", "LESS_EQ", "LESS", "EQ", "NOT_EQ"),
    ("left", "PLUS", "MINUS"),
    ("left", "MULTIPLY", "DIVIDE"),
    ("right", "UMINUS", "NOT"),
)


def collapse_items(p, group_index, singleton_index):
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[group_index]
        p[0].append(p[singleton_index])


def p_program(p):
    "program : funcs"
    p[0] = Element(InterpreterBase.PROGRAM_DEF, functions=p[1])


def p_funcs(p):
    """funcs : funcs func
    | func"""
    collapse_items(p, 1, 2)  # 2 -> func


def p_func(p):
    """func : FUNC NAME LPAREN formal_args RPAREN LBRACE statements RBRACE
    | FUNC NAME LPAREN RPAREN LBRACE statements RBRACE"""
    if len(p) == 9:  # handle with 1+ formal args
        p[0] = Element(InterpreterBase.FUNC_DEF, name=p[2], args=p[4], statements=p[7])
    else:  # handle no formal args
        p[0] = Element(InterpreterBase.FUNC_DEF, name=p[2], args=[], statements=p[6])


def p_lambda(p):
    """lambda : LAMBDA LPAREN formal_args RPAREN LBRACE statements RBRACE
    | LAMBDA LPAREN RPAREN LBRACE statements RBRACE"""
    if len(p) == 8:  # handle with 1+ formal args
        p[0] = Element(InterpreterBase.LAMBDA_DEF, args=p[3], statements=p[6])
    else:  # handle no formal args
        p[0] = Element(InterpreterBase.LAMBDA_DEF, args=[], statements=p[5])


def p_formal_args(p):
    """formal_args : formal_args COMMA formal_arg
    | formal_arg"""
    collapse_items(p, 1, 3)  # 3 -> formal_arg


def p_formal_arg(p):
    "formal_arg : NAME"
    p[0] = Element(InterpreterBase.ARG_DEF, name=p[1])


def p_formal_ref_arg(p):
    "formal_arg : REF NAME"
    p[0] = Element(InterpreterBase.REFARG_DEF, name=p[2])


def p_statements(p):
    """statements : statements statement
    | statement"""
    collapse_items(p, 1, 2)  # 3 -> formal_arg


def p_statement___assign(p):
    "statement : variable ASSIGN expression SEMI"
    p[0] = Element("=", name=p[1], expression=p[3])


def p_variable(p):
    """variable : NAME DOT NAME
    | NAME"""
    if len(p) == 4:
        p[0] = p[1] + "." + p[3]
    else:
        p[0] = p[1]


def p_statement_if(p):
    """statement : IF LPAREN expression RPAREN LBRACE statements RBRACE
    | IF LPAREN expression RPAREN LBRACE statements RBRACE ELSE LBRACE statements RBRACE
    """
    if len(p) == 8:
        p[0] = Element(
            InterpreterBase.IF_DEF,
            condition=p[3],
            statements=p[6],
            else_statements=None,
        )
    else:
        p[0] = Element(
            InterpreterBase.IF_DEF,
            condition=p[3],
            statements=p[6],
            else_statements=p[10],
        )


def p_statement_while(p):
    "statement : WHILE LPAREN expression RPAREN LBRACE statements RBRACE"
    p[0] = Element(InterpreterBase.WHILE_DEF, condition=p[3], statements=p[6])


def p_statement_expr(p):
    "statement : expression SEMI"
    p[0] = p[1]


def p_statement_return(p):
    """statement : RETURN expression SEMI
    | RETURN SEMI"""
    if len(p) == 4:
        expr = p[2]
    else:
        expr = None
    p[0] = Element(InterpreterBase.RETURN_DEF, expression=expr)


def p_expression_not(p):
    "expression : NOT expression"
    p[0] = Element(InterpreterBase.NOT_DEF, op1=p[2])


def p_expression_uminus(p):
    "expression : MINUS expression %prec UMINUS"
    p[0] = Element(InterpreterBase.NEG_DEF, op1=p[2])


def p_arith_expression_binop(p):
    """expression : expression EQ expression
    | expression GREATER expression
    | expression LESS expression
    | expression NOT_EQ expression
    | expression GREATER_EQ expression
    | expression LESS_EQ expression
    | expression PLUS expression
    | expression MINUS expression
    | expression MULTIPLY expression
    | expression DIVIDE expression"""
    p[0] = Element(p[2], op1=p[1], op2=p[3])


def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression_and_or(p):
    """expression : expression OR expression
    | expression AND expression"""
    p[0] = Element(p[2], op1=p[1], op2=p[3])


def p_expression_number(p):
    "expression : NUMBER"
    p[0] = Element(InterpreterBase.INT_DEF, val=p[1])


def p_expression_lambda(p):
    "expression : lambda"
    p[0] = p[1]


def p_expression_bool(p):
    """expression : TRUE
    | FALSE"""
    bool_val = p[1] == InterpreterBase.TRUE_DEF
    p[0] = Element(InterpreterBase.BOOL_DEF, val=bool_val)


def p_expression_nil(p):
    "expression : NIL"
    p[0] = Element(InterpreterBase.NIL_DEF)


def p_expression_obj(
    p,
):  # e.g. a = @;   ### creates a new dictionary/object and stores in a
    "expression : AT"
    p[0] = Element(InterpreterBase.OBJ_DEF)


def p_expression_string(p):
    "expression : STRING"
    p[0] = Element(InterpreterBase.STRING_DEF, val=p[1])


def p_expression_variable(p):
    "expression : variable"
    p[0] = Element(InterpreterBase.VAR_DEF, name=p[1])


def p_func_call(p):
    """expression : NAME LPAREN args RPAREN
    | NAME LPAREN RPAREN"""
    if len(p) == 5:
        p[0] = Element(InterpreterBase.FCALL_DEF, name=p[1], args=p[3])
    else:
        p[0] = Element(InterpreterBase.FCALL_DEF, name=p[1], args=[])


def p_method_call(p):
    """expression : NAME DOT NAME LPAREN args RPAREN
    | NAME DOT NAME LPAREN RPAREN"""
    if len(p) == 7:
        p[0] = Element(InterpreterBase.MCALL_DEF, objref=p[1], name=p[3], args=p[5])
    else:
        p[0] = Element(InterpreterBase.MCALL_DEF, objref=p[1], name=p[3], args=[])


def p_expression_args(p):
    """args : args COMMA expression
    | expression"""
    collapse_items(p, 1, 3)


def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")
    else:
        print("Syntax error at EOF")


# exported function
def parse_program(program):
    ast = yacc.parse(program)
    if ast is None:
        raise SyntaxError("Syntax error")
    return ast


# generate our parser
yacc.yacc()
