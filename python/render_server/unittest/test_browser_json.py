import unittest

import browser_json
from browser_json import *

import pyparsing as pp

browser_json.DEBUG_PRINT = print

class TestParsing(unittest.TestCase):
    def testStringParsing(self):
        self.assertEqual(
            parse_browser_json("'hello'"),
            'hello'
        )
        self.assertEqual(
            parse_browser_json('"world"'),
            'world'
        )
        self.assertEqual(
            parse_browser_json(r'"\\escape\n\\sequences\"work\""'),
            "\\escape\n\\sequences\"work\""
        )
        
    def testParseNumber(self):
        self.assertEqual(
            parse_browser_json(r'1000'),
            1000)
        self.assertEqual(
            parse_browser_json(r'-1000'),
            -1000)
        self.assertEqual(
            parse_browser_json(r'-0'),
            0)
        self.assertEqual(
            parse_browser_json(r'1000e-3'),
            1)
        self.assertEqual(
            parse_browser_json(r'0.2131e6'),
            0.2131e6)
        self.assertEqual(
            parse_browser_json(r'.2131e6'),
            .2131e6)
        self.assertEqual(
            parse_browser_json(r'-0.321e1'),
            -0.321e1)
        self.assertEqual(
            parse_browser_json(r'-1.e-0'),
            -1.e-0)
        self.assertEqual(
            parse_browser_json(r'1939192223121'),
            1939192223121)
        self.assertEqual(
            parse_browser_json(r'3426524525625471132467123513267418772562'),
            3426524525625471132467123513267418772562)
        
        with self.assertRaises(pp.ParseException):
            parse_browser_json(r'-1. e-0'),
            
    def testParseNull(self):
        self.assertIs(
            parse_browser_json(r'null'),
            None)
        with self.assertRaises(pp.ParseException):
            parse_browser_json(r'NULL'),

    def testParseBool(self):
        self.assertIs(
            parse_browser_json(r'true'),
            True)
        self.assertIs(
            parse_browser_json(r'false'),
            False)
        with self.assertRaises(pp.ParseException):
            parse_browser_json(r'True'),
        with self.assertRaises(pp.ParseException):
            parse_browser_json(r'False'),
        with self.assertRaises(pp.ParseException):
            parse_browser_json(r'TRUE'),

    def testArrayParsing(self):
        code = r"""[1, true, null, false, 1.2, -1.12e-5, "string", 'string']"""
        self.assertEqual(
            parse_browser_json(code),
            [1, True, None, False, 1.2, -1.12e-5, "string", 'string']
        )

        code = r"""[1, true, null, false, [], 1.2, -1.12e-5, "string", 'string']"""
        self.assertEqual(
            parse_browser_json(code),
            [1, True, None, False, [], 1.2, -1.12e-5, "string", 'string']
        )

        with self.assertRaises(pp.ParseException):
            code = r"""[1, true, null, false, [], 1.2, -1.12e-5, "string", 'string'"""
            parse_browser_json(code)

    def testObjectParsing(self):
        code = r"""
        {
            'str1': [
                1
            ], str2: 8
        }
        """

        self.assertEqual(
            parse_browser_json(code),
            {'str1': [ 1 ], 'str2': 8 }
        )

        code = r"""
        {
            'str1': [
                1
            ],
            "str2": [],
            no_str: { message: "should still work" }
        }
        """
        self.assertEqual(
            parse_browser_json(code),
            {'str1': [ 1 ], 'str2': [], "no_str": { "message": "should still work" } }
        )

        self.assertEqual(
            parse_browser_json("{}"), 
            {})


        code = r"""{a: "a", }"""
        self.assertEqual(
            parse_browser_json(code),
            {"a": "a"}
        )

if __name__ == "__main__":
    unittest.main()
