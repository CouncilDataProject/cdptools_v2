#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
from pathlib import Path
import traceback
from typing import Any, List, NamedTuple, Optional, Tuple, Union
from uuid import uuid4

from ..databases.database import Database
from ..file_stores.file_store import FileStore

###############################################################################

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)4s: %(module)s:%(lineno)4s %(asctime)s] %(message)s'
)
log = logging.getLogger(__file__)

###############################################################################


class RunIO(NamedTuple):
    type: str
    value: Any


class RunManager():

    def __init__(
        self,
        database: Database,
        file_store: FileStore,
        algorithm_name: str,
        algorithm_version: str,
        inputs: Optional[List[Union[List, Tuple, RunIO]]] = [],
        algorithm_description: Optional[str] = None,
        algorithm_source: Optional[str] = None,
        remove_files: bool = False
    ):
        # Save db reference
        self._db = database
        self._fs = file_store
        self._remove_files = remove_files

        # Get or upload algorithm details
        self._algorithm_name = algorithm_name
        self._algorithm_version = algorithm_version
        self._algorithm_description = algorithm_description
        self._algorithm_source = algorithm_source

        # Create empty file lists
        self._input_files = []
        self._output_files = []

        # Register all inputs
        self._inputs = []
        for i in inputs:
            self.register_input(i)

        # Create empty outputs list
        self._outputs = []

    def _make_serializable_type(self, value: Any, io_type: str = "input"):
        # Standard acceptable types
        if isinstance(value, (bool, type(None), str, float, int, datetime)):
            return value

        # Path type
        if isinstance(value, Path):
            # Resolve
            value = value.resolve(strict=True)
            if value.is_dir():
                raise IsADirectoryError(f"RunIO must be single files or values. Received {value}")
            if io_type == "input":
                self._input_files.append(RunIO(str(type(value)), value))
            elif io_type == "output":
                self._output_files.append(RunIO(str(type(value)), value))
            return None

        return str(value)

    def _create_io(self, value: Union[Any, List, Tuple, RunIO], io_type: str = "input") -> RunIO:
        # Fast create
        if isinstance(value, RunIO):
            return value

        # Provided a list or tuple, expand
        if isinstance(value, (list, tuple)):
            # Single value in list, reduce
            if len(value) == 1:
                return self._create_io(value[0], io_type)
            if len(value) != 2:
                raise ValueError(f"RunIO objects may only be initialized with a type and value. Received: {value}")
            # Make serializable
            serializable_value = self._make_serializable_type(value[1], io_type)
            if serializable_value:
                return RunIO(value[0], serializable_value, io_type)

        # Provided a single value
        # Make serializable
        serializable_value = self._make_serializable_type(value, io_type)
        if serializable_value:
            return RunIO(str(type(value)), serializable_value)

        return None

    def register_input(self, input: Union[Any, List, Tuple, RunIO]) -> RunIO:
        # Make serializable
        input = self._create_io(input)
        # If it was a filepath, it will return None
        if input:
            self._inputs.append(input)

        return input

    def register_output(self, output: Union[Any, List, Tuple, RunIO]) -> RunIO:
        # Make serializable
        output = self._create_io(output, "output")
        # If it was a filepath, it will return None
        if output:
            self._outputs.append(output)

    def register_run(self):
        # Store files before database
        input_files = []
        for f in self._input_files:
            uri = self._fs.upload_file(f.value, remove=self._remove_files)
            input_files.append(self._db.get_or_upload_file(uri))
        log.debug(f"Stored {len(self._input_files)} input files in {self._fs}")

        output_files = []
        for f in self._output_files:
            uri = self._fs.upload_file(f.value, remove=self._remove_files)
            output_files.append(self._db.get_or_upload_file(uri))
        log.debug(f"Stored {len(self._output_files)} output files in {self._fs}")

        algorithm_details = self._db.get_or_upload_algorithm(
            name=self._algorithm_name,
            version=self._algorithm_version,
            description=self._algorithm_description,
            source=self._algorithm_source
        )

        # Create run
        run_details = self._db.get_or_upload_run(algorithm_details["algorithm_id"], self._began, self._completed)
        log.debug(f"Created run: {run_details}")

        # Create file inputs and outputs in db
        for fi in input_files:
            self._db.get_or_upload_run_input_file(run_details["run_id"], fi["file_id"])
        for fo in output_files:
            self._db.get_or_upload_run_output_file(run_details["run_id"], fo["file_id"])
        log.debug("Linked run to I/O files")

        # Create other inputs and outputs in db
        for i in self._inputs:
            self._db.get_or_upload_run_input(run_details["run_id"], i.type, i.value)
        for o in self._outputs:
            self._db.get_or_upload_run_output(run_details["run_id"], o.type, o.value)
        log.debug("Linked run to I/O values")

    def __enter__(self):
        self._began = datetime.utcnow()
        return self

    def __exit__(self, exception_type, exception_value, tb):
        # Handle exception
        if exception_type:
            # Write traceback to file
            traceback_path = Path(f"exception_log_{str(uuid4())}.err")
            with open(traceback_path, "w") as exception_log:
                exception_log.write(traceback.format_exc())

            # Register additional error outputs
            self.register_output(RunIO(str(exception_type), exception_value))
            self.register_output(traceback_path)

        # Close the run
        self._completed = datetime.utcnow()
        self.register_run()
