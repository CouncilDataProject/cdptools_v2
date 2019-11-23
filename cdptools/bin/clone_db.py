import argparse
import logging
import sys
import time
import traceback
from pathlib import Path

from concurrent.futures import ThreadPoolExecutor
from functools import partial
import cdptools.databases.cloud_firestore_database as c_db

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
            prog="clone_prod",
            description="Clone prod database to target database."
        )
        p.add_argument("project_id", help="Project id of source database.", default="cdp-seattle")
        p.add_argument("target_credentials", type=Path, help="Credentials of target database.")
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        p.parse_args(namespace=self)

def pass_through(row, target_db, table):
    row.pop('updated', None)
    row.pop('created', None)
    row.pop(str(table)+'_id', None)
    target_db._table_to_function_dict[table](**row)

def main():
    args = Args()
    source_db = c_db.CloudFirestoreDatabase(project_id=args.project_id)
    target_db = c_db.CloudFirestoreDatabase(credentials_path=args.target_credentials)

    for table in source_db._tables:
        log.info("Cloning table: " + table)
        processingfunc = partial(pass_through, target_db=target_db, table=table)
        prod_rows = source_db.select_rows_as_list(table)
        with ThreadPoolExecutor() as exe:
            exe.map(processingfunc, prod_rows)

if __name__ == "__main__":
    main()
