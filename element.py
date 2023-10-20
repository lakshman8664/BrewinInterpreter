class Element:
    def __init__(self, elem_type, **kwargs):
        self.elem_type = elem_type
        self.dict = {}
        for key, value in kwargs.items():
            self.dict[key] = value

    def get(self, key):
        if key not in self.dict:
            return None
        return self.dict[key]

    def __str__(self):
        s = f"{self.elem_type}: "
        for key, value in self.dict.items():
            s += key + ": " + self.__val(value) + ", "
        return s[0:-2]

    def __val(self, v):
        if isinstance(v, Element):
            return "[" + str(v) + "]"
        if isinstance(v, list):
            s = ""
            for i in v:
                s += str(i) + ", "
            if len(s) > 0:
                return "[" + s[0:-2] + "]"
            return "[" + s + "]"
        return str(v)
