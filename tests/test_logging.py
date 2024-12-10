"""
Tests amati/logging.py
"""

from amati.logging import Log, LogMixin
from amati.validators.generic import GenericObject
from amati.validators.reference_object import Reference, ReferenceModel

reference1: Reference = ReferenceModel(
    title='Test',
    url='https://example.com'
)

reference2: Reference = ReferenceModel(
    title='Test',
    url='https://a.com'
)

references: Reference = [reference1, reference2]


class Model1(GenericObject):
    value: str

    def test_log(self):
        LogMixin.log(Log('Model1', ValueError, reference1))


class Model2(GenericObject):
    value: str
    value: str

    def test_log(self):
        LogMixin.log(Log('Model2', ValueError, references))


def test_writer():
    with LogMixin.context():
        model1 = Model1(value='a')
        model1.test_log()
        assert LogMixin.logs == [Log('Model1', ValueError, reference1)]

        model2 = Model2(value='b')
        model2.test_log()
        assert LogMixin.logs == [Log('Model1', ValueError, reference1),
                                 Log('Model2', ValueError, references)]
