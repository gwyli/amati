"""
Collected rules from RFC 6901, Section 3.
https://www.rfc-editor.org/rfc/rfc6901#section-3

"""

from typing import ClassVar

from abnf.grammars.misc import load_grammar_rulelist
from abnf.parser import Rule as _Rule


@load_grammar_rulelist()
class Rule(_Rule):
    """Parser rules for grammar from RFC 6901"""

    grammar: ClassVar[
        list[str] | str
    ] = r"""
json-pointer    = *( "/" reference-token )
reference-token = *( unescaped / escaped )
unescaped       = %x00-2E / %x30-7D / %x7F-10FFFF
    ; %x2F ('/') and %x7E ('~') are excluded from 'unescaped'
escaped         = "~" ( "0" / "1" )
; representing '~' and '/', respectively
"""
