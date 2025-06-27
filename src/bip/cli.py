import argparse
import importlib
import pkgutil
import sys
import logging

from pathlib import Path

from bip.__version__ import __version__ as version
from bip.parse import parse_bin
from bip.recorder.parquet.pqwriter import PQWriter
from bip.recorder.partitioned_parquet.partitioned_pqwriter import new_partitioned_parquet_writer
import bip.plugins


def _find_plugins():
    return {
        name: importlib.import_module(name)
        for finder, name, _
        in pkgutil.iter_modules(bip.plugins.__path__, bip.plugins.__name__ + ".")
    }


def main():
    plugins = _find_plugins()
    plugin_names = [s.split(".")[-1] for s in plugins.keys()]
    assert 'juliet' in plugin_names

    argparser = argparse.ArgumentParser("bip")
    argparser.add_argument(
        "-i", "--input",
        required=True,
        default=None,
        help="[INPUT_FILENAME] complete path to .BIN file to parse")
    argparser.add_argument(
        "-o", "--output",
        required=True,
        default=None,
        help="[OUTPUT_DIRECTORY] directory in which to put output artifacts"
    )
    argparser.add_argument(
        "-f", "--force",
        action="store_true",
        help="create output directory if it does not exist")
    argparser.add_argument(
        "-p", "--parser",
        required=False,
        default="juliet",
        help="parsing engine (select from " + ",".join(plugin_names) + ")",
        choices=plugin_names)
    argparser.add_argument(
        "-v", "--version",
        action="version",
        version=version,
        help="print version")

    argparser.add_argument(
        "-z", "--compression",
        default=None,
        required=False,
        help="compression codec",
        choices=["snappy", "gzip", "brotli", "lz4", "zstd"])
    argparser.add_argument(
        "--compression_level",
        default=None,
        required=False,
        help="compression level",
        type=int)
    argparser.add_argument(
        "--clean",
        action="store_true",
        required=False,
        help="clean DEADBEEF from data")
    argparser.add_argument(
        "--partition-data",
        action="store_true",
        help="Partition the data output by the context packet associated with it. Only implemented for Tango.",
        required=False
    )
    argparser.add_argument(
        "--partition-key-prefix",
        help="Prefix to add to the data output partition key",
        default=""
    )
    argparser.add_argument(
        "--partition-orphan-key",
        help="Partition key to use for data that doesn't belong to a context packet in this file.",
        default="ORPHAN_DATA",
        required=False
    )
    argparser.add_argument(
        "--log-level",
        required=False,
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="The level of logging you want in the log file.")

    args = argparser.parse_args()
    input_file = args.input
    output_directory = args.output

    input_path = Path(input_file)
    if not input_path.exists():
        print(f"{input_file} not found")
        sys.exit(1)

    output_path = Path(output_directory)
    if not output_path.exists():
        if args.force:
            output_path.mkdir(exist_ok=True, parents=True)
            assert output_path.exists()
        else:
            print(f"{output_directory} not found")
            sys.exit(1)

    if not output_path.is_dir():
        print(f"{output_directory} is not a directory")
        sys.exit(1)

    recorder_opts = {}
    if args.compression_level is not None:
        if args.compression is None:
            print("compression level specified with no compression codec")
            sys.exit(1)
        recorder_opts["compression_level"] = args.compression_level

    if args.compression is not None:
        recorder_opts["compression"] = args.compression.upper()

    plugin = plugins[f"bip.plugins.{args.parser}"]
    data_recorder = (
        new_partitioned_parquet_writer(['data_key'])
        if args.partition_data
        else PQWriter
    )

    log_level = getattr(logging, args.log_level.upper())

    try:
        parser = plugin.Parser(
            input_path,
            output_path,
            PQWriter,
            log_level,
            recorder_opts=recorder_opts,
            data_recorder=data_recorder,
            clean=args.clean,
            orphan_context_key=args.partition_orphan_key,
            context_key_function=lambda k: f"{args.partition_key_prefix}{k}"
        )
    except Exception as e:
        raise RuntimeError(f"invalid plugin {args.parser}: {str(e)}")

    parse_bin(parser, input_path, output_path)


if __name__ == '__main__':
    main()
