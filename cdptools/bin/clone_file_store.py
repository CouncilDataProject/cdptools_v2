import argparse
import logging
from pathlib import Path

from google.api_core.page_iterator import Page

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import cdptools.file_stores.gcs_file_store as fs

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

        p.add_argument("--target_bucket", type=str, help="Target bucket name.", required=True)
        p.add_argument("--target_credentials", type=Path, help="Credentials of target file store.", required=True)
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        p.add_argument('--source_bucket', help="Source bucket name.", required=True)
        p.add_argument('--source_credentials', type=Path, help="Credentials of source file store.")

        p.parse_args(namespace=self)


def clone_page(page: Page, source_fs: fs.GCSFileStore, target_fs: fs.GCSFileStore):
    for blob in page:
        # download file takes in a filename and returns a path
        downloaded_path = source_fs.download_file(blob.name, overwrite=True)

        # upload file takes in a path
        target_fs.upload_file(downloaded_path)


def main():
    args = Args()

    source_fs = fs.GCSFileStore(args.source_bucket, args.source_credentials)
    target_fs = fs.GCSFileStore(args.target_bucket, args.target_credentials)

    # We call client list_blobs method as use of the bucket's list_blobs method is deprecated
    source_client = source_fs._client
    source_bucket = source_fs._bucket

    target_bucket = target_fs._bucket

    # Clear the target file store of existing files
    target_fs.clear_bucket()

    # Get blobs in pages so we can use threading
    pages = source_client.list_blobs(source_bucket).pages

    proc_func = partial(clone_page, source_fs=source_fs, target_fs=target_fs)
    with ThreadPoolExecutor() as exe:
        exe.map(proc_func, pages)

    log.info("Cloned filestore of bucket: {source_bucket} to bucket: {target_bucket}")


if __name__ == "__main__":
    main()
