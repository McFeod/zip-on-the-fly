from io import BytesIO
from zipfile import ZIP_STORED, ZipFile

import pytest

from zip_on_the_fly import ArchiveElement, ArchiveStream


async def read_from_memory(content):
    yield content


async def memory_sources(src_dict):
    for file_name, stream in src_dict.items():
        yield ArchiveElement(file_name=file_name, stream=read_from_memory(stream))


async def write_to_memory(sources):
    result = BytesIO()
    async for chunk in ArchiveStream(sources):
        result.write(chunk)
    result.seek(0)
    return ZipFile(result, mode="r", compression=ZIP_STORED)


@pytest.mark.asyncio()
async def test_compatibility(tmp_path):
    sources = {
        "foo.txt": b"some text",
        "bar/baz.txt": b"more text",
    }
    zip_file = await write_to_memory(memory_sources(sources))
    zip_file.extractall(tmp_path)

    for name, content in sources.items():
        path = tmp_path / name
        with open(path, "rb") as stream:
            assert content == stream.read()
