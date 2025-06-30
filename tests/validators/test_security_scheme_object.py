"""
Tests amati/validators/oas311.py - ServerVariableObject
and the sub-objects OAuthFlowsObject
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls
from pydantic import ValidationError

from amati._logging import Logger
from amati.fields import URI
from amati.fields.iso9110 import HTTP_AUTHENTICATION_SCHEMES
from amati.validators.oas304 import OAuthFlowsObject
from amati.validators.oas311 import SecuritySchemeObject
from tests.helpers import text_excluding_empty_string

VALID_SECURITY_SCHEME_TYPES: list[str] = list(
    SecuritySchemeObject._SECURITY_SCHEME_TYPES  # type: ignore
)
INVALID_SECURITY_SCHEME_TYPES: st.SearchStrategy[str] = (
    st.text()
    .filter(lambda x: x not in VALID_SECURITY_SCHEME_TYPES)
    .filter(lambda x: x != "")
)

VALID_HTTP_AUTHENTICATION_SCHEMES: list[str] = list(HTTP_AUTHENTICATION_SCHEMES)
INVALID_HTTP_AUTHENTICATION_SCHEMES: st.SearchStrategy[str] = st.text().filter(
    lambda x: x not in VALID_HTTP_AUTHENTICATION_SCHEMES
)


@given(INVALID_SECURITY_SCHEME_TYPES)
def test_security_scheme_invalid(scheme_type: str):
    with Logger.context():
        SecuritySchemeObject(type=scheme_type)
        assert Logger.logs
        assert Logger.logs[0]["msg"] is not None
        assert Logger.logs[0]["type"] == "value_error"


@given(st.none())
def test_security_scheme_none(scheme_type: str):
    with pytest.raises(ValidationError):
        SecuritySchemeObject(type=scheme_type)


@given(
    st.text(),
    text_excluding_empty_string(),
    st.sampled_from(("query", "header", "cookie")),
)
def test_security_scheme_apikey_valid(description: str, name: str, in_: str):
    with Logger.context():
        SecuritySchemeObject(
            **{
                "type": "apiKey",
                "description": description,
                "name": name,
                "in": in_,
            }  # type: ignore
        )
        assert not Logger.logs


@given(
    st.text(),
    st.text(),
    st.text().filter(lambda x: x not in ("query", "header", "cookie")),
)
def test_security_scheme_apikey_invalid(description: str, name: str, in_: str):
    with Logger.context():
        SecuritySchemeObject(
            **{
                "type": "apiKey",
                "description": description,
                "name": name,
                "in": in_,
            }  # type: ignore
        )
        assert Logger.logs
        assert Logger.logs[0]["msg"] is not None
        assert Logger.logs[0]["type"] == "value_error"


@given(st.text(), st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES), st.text())
def test_security_scheme_http_valid(description: str, scheme: str, bearer_format: str):
    with Logger.context():
        SecuritySchemeObject(
            type="http",
            description=description,
            scheme=scheme,  # type: ignore
            bearerFormat=bearer_format,
        )
        assert not Logger.logs


@given(st.text(), st.text(), INVALID_HTTP_AUTHENTICATION_SCHEMES, st.text())
def test_security_scheme_http_invalid(
    type_: str, description: str, scheme: str, bearer_format: str
):
    with pytest.raises(ValidationError):
        SecuritySchemeObject(
            type=type_,
            description=description,
            scheme=scheme,  # type: ignore
            bearerFormat=bearer_format,
        )


@given(st.text(), st.sampled_from(VALID_HTTP_AUTHENTICATION_SCHEMES), st.text())
def test_security_scheme_oauth2_valid(
    description: str, scheme: str, bearer_format: str
):
    with Logger.context():
        SecuritySchemeObject(
            type="oauth2",
            description=description,
            scheme=scheme,  # type: ignore
            bearerFormat=bearer_format,
            flows=OAuthFlowsObject(),
        )
        assert not Logger.logs


@given(st.text(), st.text(), INVALID_HTTP_AUTHENTICATION_SCHEMES, st.text())
def test_security_scheme_oauth2_invalid(
    type_: str, description: str, scheme: str, bearer_format: str
):
    with pytest.raises(ValidationError):
        SecuritySchemeObject(
            type=type_,
            description=description,
            scheme=scheme,  # type: ignore
            bearerFormat=bearer_format,
        )


@given(
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_implicit_valid(
    authorization_url: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "implicit": {
                    "authorizationUrl": authorization_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )

        assert not Logger.logs


@given(
    urls(),
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_implicit_invalid(
    authorization_url: URI, token_url: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "implicit": {
                    "authorizationUrl": authorization_url,
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )

        assert Logger.logs


@given(
    urls(),
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_authorization_code_valid(
    authorization_url: URI, token_url: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "authorizationCode": {
                    "authorizationUrl": authorization_url,
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert not Logger.logs


@given(
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_authorization_code_invalid(
    uri: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "authorizationCode": {
                    "authorizationUrl": uri,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert Logger.logs
    with Logger.context():
        OAuthFlowsObject(
            **{
                "authorizationCode": {
                    "tokenUrl": uri,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert Logger.logs


@given(
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_client_and_password_valid(
    token_url: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "clientCredentials": {
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )

        assert not Logger.logs
    with Logger.context():
        OAuthFlowsObject(
            **{
                "password": {
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert not Logger.logs


@given(
    urls(),
    urls(),
    urls(),
    st.dictionaries(keys=text_excluding_empty_string(), values=st.text()),
)
def test_oauth_flows_client_and_password_invalid(
    authorization_url: URI, token_url: URI, refresh_url: URI, scopes: dict[str, str]
):
    with Logger.context():
        OAuthFlowsObject(
            **{
                "clientCredentials": {
                    "authorizationUrl": authorization_url,
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert Logger.logs
    with Logger.context():
        OAuthFlowsObject(
            **{
                "password": {
                    "authorizationUrl": authorization_url,
                    "tokenUrl": token_url,
                    "refreshUrl": refresh_url,
                    "scopes": scopes,
                }
            }  # type: ignore
        )
        assert Logger.logs
