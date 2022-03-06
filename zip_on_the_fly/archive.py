"""The main flow of ZIP creation."""

from typing import AsyncIterable, Generic, List, TypeVar

from .counters import Chain, CRCCounter, LengthCounter
from .elements import ArchiveElement
from .iterators import Stream, TStream
from .zip_format import (
    CentralDirectoryEntry,
    DataDescriptor,
    EndOfCentralDirectory,
    LocalFileHeader,
)

Element = TypeVar("Element", bound=ArchiveElement)


class ArchiveStream(Stream[bytes], Generic[Element]):
    """Async iterable providing ZIP archive splitted into chunks."""

    def __init__(self, sources: AsyncIterable[Element]) -> None:
        """Transform multiple async sources into single archive.

        Args:
            sources: Subclasses of ArchiveElement generated on the fly
        """
        self.offset = LengthCounter()
        self.files: List[CentralDirectoryEntry] = []
        self.sources = sources

    async def on_error(self, element: Element, error: Exception) -> None:  # noqa PLR0201
        """Override this method as you want.

        By default any error is reraised
        Args:
            element: ArchiveElement from your sources
            error: original exception
        """
        raise error

    async def _stream_file(self, source: Element) -> TStream[bytes]:
        start = self.offset.value

        header = LocalFileHeader(source.file_name)
        async for chunk in self.offset.wrap(header):
            yield chunk

        size = LengthCounter()
        crc = CRCCounter()
        file_counters = Chain(size, crc, self.offset)
        try:
            async for chunk in file_counters.wrap(source.stream):
                yield chunk
        except Exception as e:  # noqa B902
            await self.on_error(source, e)
        else:
            descriptor = DataDescriptor(crc=crc.value, size=size.value)
            async for chunk in self.offset.wrap(descriptor):
                yield chunk

            self.files.append(
                CentralDirectoryEntry(
                    file_name=source.file_name,
                    crc=crc.value,
                    size=size.value,
                    offset=start,
                )
            )

    async def _stream_central_dir(self) -> TStream[bytes]:
        for entry in self.files:
            async for chunk in entry:
                yield chunk

    async def __astream__(self) -> TStream[bytes]:
        """Entrypoint for the whole stream."""
        async for element in self.sources:
            async for chunk in self._stream_file(element):
                yield chunk

        central_dir_length = LengthCounter()
        async for chunk in central_dir_length.wrap(self._stream_central_dir()):
            yield chunk

        end = EndOfCentralDirectory(
            count=len(self.files),
            size=central_dir_length.value,
            offset=self.offset.value,
        )
        async for chunk in end:
            yield chunk
