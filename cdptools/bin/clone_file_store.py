import argparse
import logging
import json
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import cdptools.file_stores.file_store as fs
from ..dev_utils import load_custom_object

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s"
)
log = logging.getLogger(__name__)

###############################################################################


class Args(argparse.Namespace):

    def __init__(self):
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="clone_file_store",
            description="Clone source file store to target file store."
        )

        p.add_argument("--source_config_path", type=Path,
                       help="Path to a configuration file with details for the source file store.", required=True)
        p.add_argument("--target_config_path", type=Path,
                       help="Path to a configuration file with details for the target file store.", required=True)
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")

        p.parse_args(namespace=self)


def read_config_file(config_path: Path):
    resolved_config_path = config_path.resolve(strict=True)

    with open(resolved_config_path, "r") as read_in:
        return json.load(read_in)


def load_file_store(config_json) -> fs.FileStore:
    return load_custom_object.load_custom_object(
        module_path=config_json["file_store"]["module_path"],
        object_name=config_json["file_store"]["object_name"],
        object_kwargs=config_json["file_store"].get("object_kwargs", {})
    )


def clone_file(file_name: str, source_fs, target_fs):
    # download file takes in a filename and returns the path
    downloaded_path = source_fs.download_file(file_name, overwrite=True)

    # upload file takes in a path, removes the downloaded ones
    target_fs.upload_file(downloaded_path, remove=True)


def main():
    args = Args()

    source_config = read_config_file(args.source_config_path)
    target_config = read_config_file(args.target_config_path)

    source_fs = load_file_store(source_config)
    target_fs = load_file_store(target_config)

    files = source_fs.list_all_files()

    proc_func = partial(clone_file, source_fs=source_fs, target_fs=target_fs)
    with ThreadPoolExecutor() as exe:
        exe.map(proc_func, files)

    log.info("Cloned filestore of bucket: {source_bucket} to bucket: {target_fs._bucket}")


if __name__ == "__main__":
    main()
