"""
Collected rules from the OpenAPI Specification Runtime Expression
grammar - Section 4.8.20.4

https://spec.openapis.org/oas/latest.html#runtime-expressions

"""

from typing import ClassVar

from abnf.grammars import rfc7230
from abnf.grammars.misc import load_grammar_rules
from abnf.parser import Rule as _Rule

from amati.grammars import rfc6901, rfc7159


@load_grammar_rules(
    [
        ("json-pointer", rfc6901.Rule("json-pointer")),
        ("char", rfc7159.Rule("char")),
        ("token", rfc7230.Rule("token")),
    ]
)
class Rule(_Rule):
    """Parser rules for grammar from OpenAPI Specification"""

    grammar: ClassVar[list[str] | str] = [
        'expression = "$url" / "$method" / "$statusCode" / "$request." source / "$response." source',  # pylint: disable=line-too-long
        "source     = header-reference / query-reference / path-reference / body-reference",  # pylint: disable=line-too-long
        'header-reference = "header." token',
        'query-reference  = "query." name',
        'path-reference   = "path." name',
        'body-reference   = "body" ["#" json-pointer ]',
        # json-pointer = *( "/" reference-token )
        # reference-token = *( unescaped / escaped )
        # unescaped       = %x00-2E / %x30-7D / %x7F-10FFFF
        #               ; %x2F ('/') and %x7E ('~') are excluded from 'unescaped'
        # escaped         = "~" ( "0" / "1" )
        #               ; representing '~' and '/', respectively
        "name = *( CHAR )",
        # token = 1*tchar,
        # tchar = "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "."
        #     / "^" / "_" / "`" / "|" / "~" / DIGIT / ALPHA
    ]
