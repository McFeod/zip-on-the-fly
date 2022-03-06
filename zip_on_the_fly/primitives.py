"""Implementation of basic types in zip metadata.

See full reference at https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT
"""

from datetime import datetime, timezone
from typing import Optional, Protocol


class Primitive(Protocol):
    """Interface of a primitive type."""

    def as_bytes(self) -> bytes:  # noqa D102
        ...


class Int(int, Primitive):
    """Integer with given length in bytes."""

    length: int

    @property
    def cut(self) -> int:
        """Limit value to fit the size."""
        return self & self.mask()

    @classmethod
    def convert(cls, source: int) -> bytes:
        """See paragraph 4.4.1.1 of the spec."""
        return source.to_bytes(length=cls.length, byteorder="little")

    @classmethod
    def mask(cls) -> int:
        """Max unsigned int of given length."""
        return (1 << cls.length * 8) - 1

    @classmethod
    def zero(cls) -> bytes:
        """Proper amount of zero bits."""
        return cls.convert(0)

    def as_bytes(self) -> bytes:
        """Byte representation of int."""
        return self.convert(self.cut)


class Int2(Int):  # noqa D101
    length = 2


class Int4(Int):  # noqa D101
    length = 4


class Str(str, Primitive):
    """Unicode strings in ZIP headers."""

    def as_bytes(self) -> bytes:
        """Max length is limited to 255 bytes without ZIP64."""
        return self.encode("utf-8")[:255]


class DateTime(Primitive):
    """DOS date and time format according to paragraph 4.4.6 of the spec."""

    def __init__(self, date_time: Optional[datetime] = None) -> None:  # noqa PLW0231
        """Transform datetime to DOS format or use current time in UTC.

        Remember: DOS datetime is "naive"
        """
        self.date_time = date_time or datetime.now().astimezone(timezone.utc)

    def as_bytes(self) -> bytes:  # noqa D102
        buffer = self.date_time.year - 1980  # start point
        buffer <<= 4  # bits for month: 2**3 < 12 < 2**4
        buffer |= self.date_time.month
        buffer <<= 5  # bits for day: 2**4 < 31 < 2**5
        buffer |= self.date_time.day
        buffer <<= 5  # bits for hour: 2**4 < 24 < 2**5
        buffer |= self.date_time.hour
        buffer <<= 6  # bits for minute: 2**5 < 60 < 2**6
        buffer |= self.date_time.minute
        buffer <<= 5  # bits for every 2 second: 2**4 < 30 < 2**5
        buffer |= self.date_time.second // 2
        return Int4(buffer).as_bytes()
