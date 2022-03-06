"""Overall ZIP structure.

See full spec at https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT
"""

from enum import IntEnum
from typing import Generator

from .iterators import SyncStream
from .primitives import DateTime, Int2, Int4, Str

ByteStream = Generator[bytes, None, None]


class ZipHeaders(IntEnum):
    """Constants hardcoded in the spec."""

    LOCAL_FILE = 0x04034B50
    DESCRIPTOR = 0x08074B50
    CENTRAL_DIRECTORY = 0x02014B50
    END_OF_CENTRAL_DIRECTORY = 0x06054B50


class FlagBits(IntEnum):
    """Only used values from paragraph 4.4.4 of the spec."""

    SIZE_IN_DESCRIPTOR = 3
    UNICODE_SUPPORT = 11

    @classmethod
    def default(cls) -> int:  # noqa D102
        return cls.SIZE_IN_DESCRIPTOR.as_int() | cls.UNICODE_SUPPORT.as_int()

    def as_int(self) -> int:
        """Transform bit number into int."""
        return 1 << self


class CompressionMethods(IntEnum):
    """Only used values from paragraph 4.4.5 of the spec."""

    STORED = 0


ZERO_TWO = Int2.zero()  # at least this library has own Zero Two
ZERO_FOUR = Int4.zero()
PROTOCOL_VERSION = Int2(20).as_bytes()
FLAGS = Int2(FlagBits.default()).as_bytes()
NO_COMPRESSION = Int2(CompressionMethods.STORED).as_bytes()


class LocalFileHeader(SyncStream[bytes]):
    """Local file header (placed before file).

    More details in paragraph 4.3.7 of the spec
    """

    header = Int4(ZipHeaders.LOCAL_FILE).as_bytes()

    def __init__(self, file_name: str) -> None:  # noqa D107
        self.file_name = Str(file_name).as_bytes()
        self.name_size = Int2(len(self.file_name)).as_bytes()
        self.modified = DateTime().as_bytes()

    def stream(self) -> ByteStream:  # noqa D102
        yield self.header
        yield PROTOCOL_VERSION
        yield FLAGS
        yield NO_COMPRESSION
        yield self.modified
        yield ZERO_FOUR  # crc
        yield ZERO_FOUR  # compressed
        yield ZERO_FOUR  # uncompressed
        yield self.name_size
        yield ZERO_TWO  # extra_size
        yield self.file_name


class DataDescriptor(SyncStream[bytes]):
    """Data descriptor at the end of file.

    More details in paragraph 4.3.9 of the spec
    """

    header = Int4(ZipHeaders.DESCRIPTOR).as_bytes()

    def __init__(self, crc: int, size: int) -> None:  # noqa D107
        self.crc = Int4(crc).as_bytes()
        self.uncompressed = Int4(size).as_bytes()
        self.compressed = self.uncompressed

    def stream(self) -> ByteStream:  # noqa D102
        yield self.header
        yield self.crc
        yield self.compressed
        yield self.uncompressed


class CentralDirectoryEntry(DataDescriptor, LocalFileHeader):
    """The part of central directory describing single file.

    See paragraph 4.3.12 of the spec for more info
    """

    header = Int4(ZipHeaders.CENTRAL_DIRECTORY).as_bytes()

    def __init__(self, file_name: str, crc: int, size: int, offset: int) -> None:
        """File metadata and the offset from start of archive in bytes."""
        DataDescriptor.__init__(self, crc, size)
        LocalFileHeader.__init__(self, file_name)
        self.offset = Int4(offset).as_bytes()

    def stream(self) -> ByteStream:  # noqa D102
        yield self.header
        yield PROTOCOL_VERSION  # made by
        yield PROTOCOL_VERSION  # required version
        yield FLAGS
        yield NO_COMPRESSION
        yield self.modified
        yield self.crc
        yield self.compressed
        yield self.uncompressed
        yield self.name_size
        yield ZERO_TWO  # extra field length
        yield ZERO_TWO  # file comment length
        yield ZERO_TWO  # disk number start
        yield ZERO_TWO  # internal file attributes
        yield ZERO_FOUR  # external file attributes
        yield self.offset
        yield self.file_name


class EndOfCentralDirectory(SyncStream[bytes]):
    """The final part of the Central Directory.

    More details in paragraph 4.3.16 of the spec
    """

    header = Int4(ZipHeaders.END_OF_CENTRAL_DIRECTORY).as_bytes()

    def __init__(self, count: int, size: int, offset: int) -> None:
        """Provide the metadata of central directory.

        Args:
            count: the number of files (records in cd)
            size: total size of central directory entries in bytes
            offset: start of the first cd entry (bytes)
        """
        self.count = Int2(count).as_bytes()
        self.size = Int4(size).as_bytes()
        self.offset = Int4(offset).as_bytes()

    def stream(self) -> ByteStream:  # noqa D102
        yield self.header
        yield ZERO_TWO  # number of this disk
        yield ZERO_TWO  # disk with start of the central directory
        yield self.count  # on this disk
        yield self.count  # total
        yield self.size
        yield self.offset
        yield ZERO_TWO  # comment length
