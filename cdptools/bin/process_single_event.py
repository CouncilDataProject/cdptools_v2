import argparse
import logging
import sys
import traceback
from pathlib import Path

from cdptools import get_module_version

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
            prog="process_single_event",
            description="Process a single event."
        )

        p.add_argument("--event_url", type=str, help="URL of the event you want to process.", required=True)
        p.add_argument("--config_path", type=Path, help="Path to a configuration file with details for the pipeline.",
                       required=True)
        p.add_argument("--debug", action="store_true", dest="debug", help="Show traceback if the script were to fail.")
        p.parse_args(namespace=self)


def main():
    args = Args()

    try:
        pipeline = load_custom_object.load_custom_object(
            module_path="cdptools.pipelines",
            object_name="EventGatherPipeline",
            object_kwargs={"config_path": args.config_path}
        )

        event = pipeline.event_scraper.get_single_event(args.event_url, backfill=True)

        log.info(f"CDPTools Version: {get_module_version()}")
        log.info("Initializing: EventGatherPipeline")

        pipeline.process_event(event)
    except Exception as e:
        log.error("=============================================")
        if args.debug:
            log.error("\n\n" + traceback.format_exc())
            log.error("=============================================")
        log.error("\n\n" + str(e) + "\n")
        log.error("=============================================")
        sys.exit(1)


if __name__ == "__main__":
    main()
