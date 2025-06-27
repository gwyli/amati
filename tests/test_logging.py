"""
Tests amati/logging.py
"""

from amati.logging import LogMixin
from amati.validators.generic import GenericObject


class Model(GenericObject):
    value: str

    def test_log(self):
        LogMixin.log(
            {"msg": "Model1", "type": "value_error", "url": "https://example.com"}
        )


def test_writer():
    with LogMixin.context():
        model1 = Model(value="a")
        model1.test_log()
        assert LogMixin.logs == [
            {"msg": "Model1", "type": "value_error", "url": "https://example.com"}
        ]

        model2 = Model(value="b")
        model2.test_log()
        assert LogMixin.logs == [
            {"msg": "Model1", "type": "value_error", "url": "https://example.com"},
            {"msg": "Model1", "type": "value_error", "url": "https://example.com"},
        ]
