Zip on the fly
==============

This library provides asyncio-based implementation of uncompressed ZIP stream. No external dependencies needed.

If you don't need to retrieve source files in asynchronous way, you could use [zipstream](https://github.com/kbbdy/zipstream) or even `zipfile` from standard library.


Restrictions
------------
- names are encoded in utf-8
- ZIP64 is not supported (names are limited to 256 bytes, 65535 files max, total size less than 4Gb)
- No compression
- No encryption


Usage
-----
```
from zip_on_the_fly import ArchiveElement, ArchiveStream


async def create_file():
    # get content of the file from disk / via network or generate it
    yield b"next chunk"


async def prepare_sources():
    # provide elements when they are ready
    yield ArchiveElement(
        file_name="foo/bar.txt",
        stream=create_file()
    )


async for chunk in ArchiveStream(prepare_sources()):
    # write next chunk of zip archive to disk / send it via network
```


