import argparse
import logging
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

        p.add_argument("--target_credentials", type=Path, help="Credentials of target database.", required=True)
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument('--source_project_id', help="Project id of source database.")
        group.add_argument('--source_credentials', type=Path, help="Credentials of source database.")

        p.parse_args(namespace=self)


def pass_through(row, target_db, table):
    row.pop('updated', None)
    row.pop('created', None)
    row.pop(str(table)+'_id', None)
    target_db._cdp_table_to_function_dict[table](**row)


def delete_table(table, target_db):
    target_db.wipe_table(table, 500)


def main():
    args = Args()

    source_db = None
    if args.source_project_id:
        source_db = c_db.CloudFirestoreDatabase(project_id=args.source_project_id)
        log.info("Cloning database with project_id={}".format(args.source_project_id))
    else:
        source_db = c_db.CloudFirestoreDatabase(credentials_path=args.source_credentials)
        log.info("Cloning database with credentials={}".format(args.source_credentials))

    target_db = c_db.CloudFirestoreDatabase(credentials_path=args.target_credentials)

    deletefunc = partial(delete_table, target_db=target_db)

    with ThreadPoolExecutor() as exe:
        exe.map(deletefunc, target_db.tables)

    for table in source_db.tables:
        log.info("Cloning table: " + table)
        processingfunc = partial(pass_through, target_db=target_db, table=table)
        prod_rows = source_db.select_rows_as_list(table)
        with ThreadPoolExecutor() as exe:
            exe.map(processingfunc, prod_rows)


if __name__ == "__main__":
    main()
