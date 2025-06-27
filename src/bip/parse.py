import io
import sys
import datetime
import json
import time
from pathlib import Path

import tqdm

from bip.__version__ import metadata as bip_metadata
from bip.parser_protocol import Parser


METADATA_FILENAME = "metadata.json"


def _save_metadata(
        metadata_file: Path,
        filename: Path,
        file_size: int = None,
        file_format_metadata: dict = {},
        **kwargs):
    metadata_dict = {
        "file": filename.name,
        "path": str(filename.absolute()),
        "size": file_size,
        "format": file_format_metadata,
        "parser": bip_metadata(),
    } | kwargs

    with open(metadata_file, "w", encoding="utf-8") as metadata_file:
        json.dump(metadata_dict,
                  metadata_file,
                  indent=4)


def parse_bin_stream(
    parser: Parser,
    stream: io.BufferedIOBase,
    filename: str,
    file_size: int,
    output_dir: Path,
    *,
    verbose: bool = True,
    metadata_filename: str = METADATA_FILENAME
):

    if not isinstance(parser, Parser):
        raise ValueError("parser does not support bip Parser protocol")
    if not isinstance(stream, io.BufferedIOBase):
        raise ValueError("parameter stream is not a binary stream")
    if not isinstance(output_dir, Path):
        raise ValueError(
            f"parameter output_dir: {output_dir} is not of type pathlib.Path")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError(f"{output_dir} is not a directory")

    is_tty = sys.stdout.isatty()
    if verbose:
        print(f"parsing: {filename}")

    if is_tty:
        bar = tqdm.tqdm(total=file_size, unit="B", desc="parsing",
                        unit_scale=True)
    else:
        bar = None

    start_time = datetime.datetime.now()
    tic = time.time()

    parser.parse_stream(stream, progress_bar=bar)

    toc = time.time()
    end_time = datetime.datetime.now()

    if is_tty:
        bar.close()

    if verbose:
        parse_rate = parser.packets_read / (toc - tic)
        print(
            f"parsed: {
                parser.packets_read} packets, [{
                parse_rate:.1f} packets/second]")

    _save_metadata(
        output_dir / metadata_filename,
        filename,
        file_size,
        file_format_metadata=parser.metadata,
        bytes_processed=parser.bytes_read,
        packets_processed=parser.packets_read,
        start_time=str(start_time),
        end_time=str(end_time),
    )


def parse_bin(
    parser: Parser,
    filename: Path,
    output_dir: Path,
    *,
    verbose: bool = True,
    metadata_filename: str = METADATA_FILENAME
):
    if not isinstance(filename, Path):
        raise ValueError(
            f"parameter filename: {filename} is not of type pathlib.Path")
    with open(filename, "rb") as f:
        parse_bin_stream(
            parser,
            f,
            filename,
            filename.stat().st_size,
            output_dir,
            verbose=verbose,
            metadata_filename=metadata_filename)
