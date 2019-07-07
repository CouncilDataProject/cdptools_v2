#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Callable, Dict, List
from unittest import mock

from .run_cdp_pipeline import run_cdp_pipeline

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__name__)

###############################################################################


class Args(argparse.Namespace):

    def __init__(self):
        self.__parse()

    def __parse(self):
        p = argparse.ArgumentParser(
            prog='test_cdp_pipeline',
            description='Initialize and test a cdp pipeline.'
        )
        p.add_argument('pipeline_type', help='Which pipeline to launch.')
        p.add_argument('config_path', type=Path, help='Path to a configuration file with details for the pipeline.')
        p.add_argument('--nm', '--run-every-n-minutes', action='store', dest='schedule', type=int, default=None,
                       help='Integer to run the specified pipeline every n minutes. Default: Run pipeline once.')
        p.add_argument('--debug', action='store_true', dest='debug', help='Show traceback if the script were to fail.')
        p.parse_args(namespace=self)


###############################################################################

def recursive_mocks(mocks: List[Dict[str, str]], ending_function: Callable, result_function_args: Args):
    if len(mocks) > 0:
        with mock.patch(mocks[0]["path"]) as mocked_item:
            log.info("Setting up mock for: {}".format(mocks[0]["path"]))
            mocked_item.return_value = mocks[0]["return_value"]
            recursive_mocks(mocks[1:], ending_function, result_function_args)
    else:
        ending_function(result_function_args)


def main():
    try:
        args = Args()

        # Read config
        with open(args.config_path, "r") as read_in:
            config = json.load(read_in)

        # Mocks must be added to the config for this function to run
        try:
            recursive_mocks(config["mocks"], run_cdp_pipeline, args)
        except KeyError as e:
            raise KeyError("'test_cdp_pipeline', takes the exact same arguments as 'run_cdp_pipeline' but requires an "
                           "additional 'mocks' section in the configuration file.", e)

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
