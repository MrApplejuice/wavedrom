import pyparsing as pp

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

LBRACKET = pp.Suppress("[")
RBRACKET = pp.Suppress("]")



GRAMMAR = STRING | NUMBER | NULL | BOOL

class TranslateException(Exception): pass

def parse_browser_json(text):
    the_parse = GRAMMAR.parseString(text, parseAll=True)
    
    print(the_parse)
    
    # Translate the parse
    def translate_to_python(obj):
        print(type(obj), obj.getName())

        if obj.getName() == "STR":
            return str(obj[0])
        elif obj.getName() == "FNUM":
            return float(obj[0])
        elif obj.getName() == "INUM":
            return int(obj[0])
        elif obj.getName() == "NULL":
            return None
        elif obj.getName() == "BOOL":
            return str(obj[0]) == "true"
        else:
            raise TranslateException("Unknown parse object of type: {}".format(obj.getName()))
    
    return translate_to_python(the_parse)
