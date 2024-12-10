


from abnf.grammars import rfc5322






def _validate_after_email(value: str) -> str:
    """
    Validate that the email address is a valid email address.

    Args:
        value: The email address to validate
    
    Raises:
        ParseError: If the email address does not conform to RFC5322 ABNF grammar
    """

    return rfc5322.Rule('address').parse_all(value).value


Email = Annotated[
    Optional[str],
    AfterValidator(_validate_after_email)
]


