#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import traceback
from pathlib import Path

from cdptools import get_module_version
from cdptools.dev_utils import check_system_version, load_custom_object

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s"
)
log = logging.getLogger(__name__)

###############################################################################

LOWER_VERSION = "2.0.0"
UPPER_VERSION = "2.0.4"

###############################################################################


class Args(argparse.Namespace):

    def __init__(self):
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog="cdp_migrate_2.0.0_2.0.4",
            description="Add core NLP additions."
        )
        p.add_argument("--up", "--upgrade", action="store_true", dest="upgrade", default=True,
                       help="Should the system upgrade or downgrade versions. Defaults to upgrade.")
        p.add_argument("--down", "--downgrade", action="store_false", dest="upgrade", default=True,
                       help="Should the system upgrade or downgrade versions. Defaults to upgrade.")
        p.add_argument("config_path", type=Path,
                       help="Path to a configuration file with details for the migration script.")
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        p.parse_args(namespace=self)


###############################################################################

def upgrade(config_path: Path):
    log.info(f"Upgrading from {LOWER_VERSION} to {UPPER_VERSION}")


def downgrade(config_path: Path):
    log.info(f"Downgrading from {UPPER_VERSION} to {LOWER_VERSION}")


def run(args: Args):
    try:
        log.info(f"CDPTools Version: {get_module_version()}")
        log.info(f"Initializing: {args.pipeline_type}")

        # Run upgrade/ downgrade
        if args.upgrade:
            upgrade(args.config_path)
        else:
            downgrade(args.config_path)

    except Exception as e:
        log.error("=============================================")
        if args.debug:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


def main():
    args = Args()
    run(args)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
