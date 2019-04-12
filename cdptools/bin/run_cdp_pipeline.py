#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
from pathlib import Path
import sys
import traceback

from cdptools import pipelines

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class Args(argparse.Namespace):

    def __init__(self):
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog='run_cdp_pipeline',
            description='Initialize and run a cdp pipeline.'
        )
        p.add_argument('pipeline_type', help='Which pipeline to launch.')
        p.add_argument('config_path', type=Path, help='Path to a configuration file with details for the pipeline.')
        p.add_argument('--debug', action='store_true', dest='debug', help='Show traceback if the script were to fail.')
        p.parse_args(namespace=self)


###############################################################################


def main():
    try:
        args = Args()

        # Initialize pipeline
        pipeline = pipelines.Pipeline.load_custom_object(
            module_path="cdptools.pipelines",
            object_name=args.pipeline_type,
            object_kwargs={"config_path": args.config_path}
        )

        # Run pipeline
        pipeline.run()

    except Exception as e:
        log.error("=============================================")
        if args.debug:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


###############################################################################
# Allow caller to directly run this module (usually in development scenarios)

if __name__ == '__main__':
    main()
