#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import sys
import time
import traceback
from pathlib import Path

import schedule

from cdptools import get_module_version
from cdptools.dev_utils import load_custom_object

###############################################################################

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
            prog="run_cdp_pipeline",
            description="Initialize and run a CDP pipeline."
        )
        p.add_argument("pipeline_type", help="Which pipeline to launch.")
        p.add_argument("config_path", type=Path, help="Path to a configuration file with details for the pipeline.")
        p.add_argument("--nm", "--run-every-n-minutes", action="store", dest="schedule", type=int, default=None,
                       help="Integer to run the specified pipeline every n minutes. Default: Run pipeline once.")
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        p.parse_args(namespace=self)


###############################################################################

def run_cdp_pipeline(args: Args):
    try:
        # Initialize pipeline
        pipeline = load_custom_object.load_custom_object(
            module_path="cdptools.pipelines",
            object_name=args.pipeline_type,
            object_kwargs={"config_path": args.config_path}
        )

        log.info(f"CDPTools Version: {get_module_version()}")
        log.info(f"Initializing: {args.pipeline_type}")

        # If pipeline schedule was provided run on schedule
        if args.schedule:
            schedule.every(args.schedule).minutes.do(pipeline.run)
            log.info(f"Pipeline will run every {args.schedule} minutes.")
            log.info("=" * 80)

            # Continuely run
            while True:
                schedule.run_pending()
                time.sleep(1)

        # No schedule passed. Run once
        else:
            log.info(f"Pipeline will run once.")
            log.info("=" * 80)
            pipeline.run()

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
    run_cdp_pipeline(args)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == "__main__":
    main()
