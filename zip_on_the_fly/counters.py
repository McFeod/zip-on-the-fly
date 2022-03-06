"""Helper classes for stream measures."""

from typing import AsyncIterable
from zlib import crc32

from .iterators import TStream


class StreamCounter:
    """Base class for counting some property of wrapped stream."""

    def __init__(self) -> None:  # noqa D107
        self.value = 0

    async def wrap(self, stream: AsyncIterable[bytes]) -> TStream[bytes]:
        """Restream wrapped object and make calculations on the fly."""
        async for chunk in stream:
            self.value = self.count(chunk)
            yield chunk

    def count(self, chunk: bytes) -> int:
        """Override this to provide specific measure."""
        raise NotImplementedError()


class LengthCounter(StreamCounter):
    """Counts length of streamed bytes."""

    def count(self, chunk: bytes) -> int:  # noqa D102
        return self.value + len(chunk)


class CRCCounter(StreamCounter):
    """Counts checksum of streamed bytes."""

    def count(self, chunk: bytes) -> int:  # noqa D102
        return crc32(chunk, self.value)


class Chain:
    """Chain of stream counters."""

    def __init__(self, *counters: StreamCounter) -> None:
        """Use given counters as one."""
        self.counters = counters

    def wrap(self, stream: AsyncIterable[bytes]) -> AsyncIterable[bytes]:
        """Restream wrapped object and apply all counters."""
        for counter in self.counters:
            stream = counter.wrap(stream)

        return stream
