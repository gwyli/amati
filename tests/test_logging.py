"""
Tests amati/warnings.py
"""

from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject


class Model1(GenericObject):
    value: str

    def test_log(self):
        LogMixin.log(Log('Model1', ValueError))


class Model2(GenericObject):
    value: str
    value: str

    def test_log(self):
        LogMixin.log(Log('Model2', ValueError))


def test_writer():
    with LogMixin.context():
        model1 = Model1(value='a')
        model1.test_log()
        assert LogMixin.logs == [Log('Model1', ValueError)]

        model2 = Model2(value='b')
        model2.test_log()
        assert LogMixin.logs == [Log('Model1', ValueError), Log('Model2', ValueError)]
