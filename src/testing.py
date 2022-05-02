import collections
import datetime as dt
import re
import threading
import typing as tp
from collections import UserDict
from collections import UserList


class ReStr:
    """
    >>> ReStr(r'\d+') == '0000000'
    True
    >>> ReStr(r'\d.\ds remain') == '0.0s remain'
    """  # noqa: W605

    def __init__(self, patt):
        self.rexp = re.compile(patt)

    def __eq__(self, other):
        if isinstance(other, ReStr):
            return self.rexp == other.rexp

        if isinstance(other, str):
            return self.rexp.search(other) is not None

        return super().__eq__(other)

    def __repr__(self):
        return f'ReStr({self.rexp.pattern})'


def maybe_hdict(value):
    if isinstance(value, dict) and not isinstance(value, HDict):
        return HDict(value)
    return value


class HDict(UserDict):
    def __hash__(self):
        return hash(frozenset((k, maybe_hdict(v)) for k, v in self.items()))


# inherit from HDict to workaround dict comparision optimization:
# __eq__ not called if .keys() differ, but calls for sub-types
class AnyDict(HDict):
    """
    >>> # Если ключа нет, он равен ANY
    >>> any_dict = AnyDict({'key': 1})
    >>> extra_key_dict = {'key': 1, 'new_key': 2}
    >>> any_dict == extra_key_dict
    True
    >>> # Если ключи совпадают: то они проверяются
    >>> diff_value_dict = {'key': 2}
    >>> any_dict == diff_value_dict
    False
    """

    def __eq__(self, other):
        if not isinstance(other, collections.Mapping):
            return False

        for key, value in self.items():
            if key not in other:
                return False
            if other[key] != value:
                return False
        return True


class UnorderedList(UserList):
    """
    >>> l1 = UnorderedList([1, 2, 3])
    >>> l2 = UnorderedList([3, 2, 1])
    >>> l1 == l2
    True
    >>> l1 = UnorderedList([{'id': 1}, {'id': 2}])
    >>> l2 = UnorderedList([{'id': 2}, {'id': 1}])
    >>> l1 == l2
    True
    """

    def __init__(self, initlist):
        copy = [maybe_hdict(item) for item in initlist]
        super().__init__(copy)

    def __eq__(self, other):
        if not isinstance(other, UnorderedList):
            other = UnorderedList(other)

        return compare(self, other)


def compare(s, t):
    """Compare with O(n * n) complexity
    but AnyDict __eq__ logic works correctly
    """

    t = list(t)
    for elem in s:
        if elem in t:
            t.remove(elem)
        else:
            return False

    return not t


class PropagatingThread(threading.Thread):
    def run(self):
        self.exc = None
        self.ret = None
        try:
            if self._target:
                self.ret = self._target(*self._args, **self._kwargs)
        except BaseException as e:
            self.exc = e
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def join(self, *args, **kw):
        super().join(*args, **kw)
        if self.exc:
            raise self.exc  # possible refcycle, see .run() to details
        return self.ret


class BytesCMP:
    """Позволяет сравнивать байты с учетом специфики memoryview
    memoryview проверяет внутренний формат перед сравенением буферов
    memoryview можно переводить из одного формата в другой без копирования буфера
    https://devdocs.io/python~3.10/library/stdtypes#memoryview.cast
    Приводим memoryview к байтам и сравниваем именно байты
    """

    def __init__(self, content: tp.Union[memoryview, bytes, None]):
        self.content = content

    def __eq__(self, other):
        if isinstance(other, memoryview):
            return self.content == BytesCMP(other.tobytes())

        return self.content == other

    def __repr__(self):
        return f'BytesCMP({repr(self.content)})'


class DateTimeCMP:
    """Позволяет сравнивать даты вне завсимости от того, в каком они формате (datetime или строка)
    >>> DateTimeCMP('2018-10-11T10:00:00+05:00') == dt.datetime.fromisoformat('2018-10-11T10:00:00+05:00')
    True
    >>> {'date': '2018-10-11T10:00:00+05:00'} == {'date': DateTimeCMP('2018-10-11T05:00:00+00:00')}
    True
    """

    try:
        from dateutil.parser import parse

        parse = staticmethod(parse)
    except ImportError as exc:
        import_exc = exc
        parse = None
    else:
        import_exc = None

    def __init__(
        self,
        value: tp.Union[str, dt.date, dt.datetime],
    ):
        """
        :param value: значение для сравнения
        """
        if self.parse is None:
            raise self.import_exc

        if isinstance(value, str):
            value = self.parse(value)

        self.value = value

    def __repr__(self):
        return f'DateTimeCMP({repr(self.value)})'

    def __eq__(self, other):
        if isinstance(other, DateTimeCMP):
            other = other.value

        if isinstance(other, str):
            other = self.parse(other)

        return self.value == other


def model_to_dict(instance, exclude=(), include_not_editable=True) -> dict:
    """Возвращает словарь с атрибутами модели"""
    from testfixtures.django import model_to_dict

    return model_to_dict(instance, exclude, include_not_editable)