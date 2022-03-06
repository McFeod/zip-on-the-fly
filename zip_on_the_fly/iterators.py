"""Helper classes for streams."""
from typing import (
    AsyncGenerator,
    AsyncIterator,
    Callable,
    Generator,
    Generic,
    Iterator,
    TypeVar,
)

T = TypeVar("T")  # noqa PLC0103
TStream = AsyncGenerator[T, None]


class Stream(Generic[T]):
    """Base class for async streams."""

    __astream__: Callable[..., AsyncGenerator[T, None]]

    def __aiter__(self) -> AsyncIterator[T]:  # noqa 
        return self.__astream__()


class SyncStream(Stream[T]):
    """Use sync generators as async iterable."""

    def stream(self) -> Generator[T, None, None]:
        """Override it to provide ordered chunks."""
        raise NotImplementedError()

    async def __astream__(self) -> TStream:
        """Use same interface as async streams."""
        for chunk in self:
            yield chunk

    def __iter__(self) -> Iterator[T]:
        return self.stream()
