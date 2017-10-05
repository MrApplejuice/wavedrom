import pyparsing as pp

DEBUG_PRINT = lambda *args, **argv: None

def gen_data_container(value, _type=lambda x: x):
    DEBUG_PRINT("wrapping", value)
    def f():
        DEBUG_PRINT("unwrapping", value)
        v2 = _type(value)
        if isinstance(v2, list):
            v2 = [x() for x in v2]
        elif isinstance(v2, dict):
            v2 = {k(): v() for k, v in v2.items()}
        DEBUG_PRINT("unwrapped", v2)
        return v2
    return f

class TranslateException(Exception): pass
def translate_to_python(obj):
    DEBUG_PRINT(type(obj), obj.getName(), len(obj), str(obj[0]), type(obj[0]))

    if obj.getName() is None:
        return obj[0]
    elif obj.getName() == "STR":
        return gen_data_container(obj[0], str)
    elif obj.getName() == "FNUM":
        return gen_data_container(obj[0], float)
    elif obj.getName() == "INUM":
        return gen_data_container(obj[0], int)
    elif obj.getName() == "NULL":
        return gen_data_container(None)
    elif obj.getName() == "BOOL":
        return gen_data_container(str(obj[0]) == "true")
    elif obj.getName() == "ARRAY":
        return gen_data_container(obj[0], list)
    elif obj.getName() == "OBJECT":
        def generate_dict(items):
            result = {}
            for i in items:
                result[i[0]] = i[1]
            return result
        return gen_data_container(list(obj[0]), generate_dict)
    elif obj.getName() == "OBJECT_FIELD":
        return (obj[0], obj[1])
    else:
        raise TranslateException("Unknown parse object of type: {}".format(obj.getName()))

def at(x):
    """ at = add translate """
    x.setParseAction(translate_to_python)
    return x


### GRAMMAR ###

STRING = (pp.QuotedString(quoteChar="'", escChar="\\") \
    | pp.QuotedString(quoteChar='"', escChar="\\"))("STR")
    
REAL = pp.pyparsing_common.real \
    ^ pp.pyparsing_common.sci_real \
    ^ pp.Combine(
        pp.Optional(pp.pyparsing_common.signed_integer) \
        + "." + pp.Optional(pp.pyparsing_common.integer) \
        + pp.Optional("e" + pp.pyparsing_common.signed_integer))
REAL.leaveWhitespace()
NUMBER = REAL("FNUM") | pp.pyparsing_common.signed_integer("INUM")

NULL = pp.Literal("null")("NULL")

BOOL = (pp.Literal("true") | pp.Literal("false"))("BOOL")

VALUE = at(STRING | NUMBER | NULL | BOOL)

ELEMENT = pp.Forward()
ARRAY = pp.Group(pp.Suppress("[") + pp.Optional(ELEMENT + pp.ZeroOrMore(pp.Suppress(",") + ELEMENT)) + pp.Suppress("]"))("ARRAY")

NAKED_FIELD_NAME = at(pp.Word(pp.alphas, pp.alphanums + "_")("STR"))
OBJECT_FIELD = at(((VALUE | NAKED_FIELD_NAME) + pp.Suppress(":") + ELEMENT)("OBJECT_FIELD"))
OBJECT = pp.Group(pp.Suppress("{") + pp.Optional(OBJECT_FIELD + pp.ZeroOrMore(pp.Suppress(",") + OBJECT_FIELD) + pp.Optional(",").suppress()) + pp.Suppress("}"))("OBJECT")

ELEMENT << at(VALUE | ARRAY | OBJECT)

GRAMMAR = at(ELEMENT)
GRAMMAR.ignore(pp.cStyleComment)
GRAMMAR.ignore(pp.dblSlashComment)


def parse_browser_json(text):
    DEBUG_PRINT("----------------")
    DEBUG_PRINT("text:", text)
    
    the_parse = GRAMMAR.parseString(text, parseAll=True)
    
    # Damnit - I do not get what pyparsing returns... 
    while isinstance(the_parse, pp.ParseResults):
        the_parse = the_parse[0]
    the_parse = the_parse()
    
    DEBUG_PRINT("final parse:", the_parse)
    
    return the_parse
