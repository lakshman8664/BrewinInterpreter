import copy

from enum import Enum
from intbase import InterpreterBase


# Enumerated type for our different language data types
class Type(Enum):
    INT = 1
    BOOL = 2
    STRING = 3
    CLOSURE = 4
    NIL = 5
    OBJECT = 6


class Closure:
    def __init__(self, func_ast, env):
        self.captured_env = copy.deepcopy(env)
        self.func_ast = func_ast
        self.type = Type.CLOSURE


class Object:
    def __init__(self):
        self.fields_to_value = {"proto": None}
        self.type = Type.OBJECT

    #  returns the dict mapping
    def get(self, fieldNeeded):
        if fieldNeeded in self.fields_to_value:
            return self.fields_to_value[fieldNeeded]

        # # Check the prototype chain recursively
        # prototype = self.fields_to_value.get("proto")
        # if prototype and prototype.value() != InterpreterBase.NIL_DEF:
        #     return prototype.value().get(fieldNeeded)

        proto = self.fields_to_value["proto"]
        #print (proto.v)
        if proto is not None:
            #proto_obj = self.proto
            while proto and proto.value() != InterpreterBase.NIL_DEF:
                print("proto", proto.value())
                if fieldNeeded in proto.v.fields_to_value:
                    return proto.v.fields_to_value[fieldNeeded] # Be careful, does this work on recursive calls to proto? and will it call fields correctly from derived object?
                proto = proto.v.fields_to_value["proto"]

        # Field not found in the current object or its prototype chain
        return None




# Represents a value, which has a type and its value
class Value:
    def __init__(self, t, v=None):
        self.t = t
        self.v = v

    def value(self):
        return self.v

    def type(self):
        return self.t

    def set(self, other):
        self.t = other.t
        self.v = other.v

def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type.BOOL, True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type.BOOL, False)
    elif isinstance(val, str):
        return Value(Type.STRING, val)
    elif isinstance(val, int):
        return Value(Type.INT, val)
    elif val == InterpreterBase.NIL_DEF:
        return Value(Type.NIL, None)
    else:
        raise ValueError("Unknown type")


def get_printable(val):
    if val.type() == Type.INT:
        return str(val.value())
    if val.type() == Type.STRING:
        return val.value()
    if val.type() == Type.BOOL:
        if val.value() is True:
            return "true"
        return "false"
    return None
