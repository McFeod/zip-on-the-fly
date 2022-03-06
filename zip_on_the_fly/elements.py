"""Format of input parameters for ArchiveStream."""
from dataclasses import dataclass
from typing import AsyncIterable


@dataclass
class ArchiveElement:
    """Base class for elements in the future archive.

    Attributes:
        file_name: name of file, use / as folder separator
        stream: content of the file
    """

    file_name: str
    stream: AsyncIterable[bytes]
