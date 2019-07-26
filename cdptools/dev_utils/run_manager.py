#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, List, NamedTuple, Optional, Tuple, Union
from uuid import uuid4

from ..databases.database import Database
from ..file_stores.file_store import FileStore

###############################################################################

log = logging.getLogger(__name__)

###############################################################################


class RunIO(NamedTuple):
    type: str
    value: Any


class RunManager():
    """
    A RunManager can be used to track the IO of an algorithm and log begin and completed times. Additionally, will
    gracefully handle when an algorithm errors. Depending on IO type, if any IO is a pathlib.Path, the full file will be
    linked to the run.

    A context manager of this class is available and the preffered method of interaction with this object. In the case
    an error occurs during the run, the context manager will catch the error and store it as an output.
    """

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
        """
        Construct a RunManager object to track algorithm IO.

        Parameters
        ----------
        database: Database
            A cdptools.database.Database connection that has full credentials to upload new data.
        file_store: FileStore
            A cdptools.file_store.FileStore connection that has full credentials to upload new data.
        algorithm_name: str
            The name of the algorithm about to run. Preffered: the full module path.
        algorithm_version: str
            The version string of the algorithm about to run.
        inputs: Optional[Union[List, Tuple, RunIO]]
            Inputs that are already known prior to the start of the algorithm run. If provided a List of List or a List
            of Tuple, each object in the outer List will be converted to RunIO objects.
        algorithm_description: Optional[str]
            Optionally, a description for the algorithm about to run.
        algorithm_source: Optional[str]
            Optionally, a uri to view the source of the algorithm about to run.
        remove_files: bool
            Boolean representing whether or not generated output files should be cleaned up after the algorithm
            completes. Default: False (Do not remove files)

        Returns
        -------
        self: The constructed RunManager.
        """
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

    def _make_serializable_type(self, value: Any, io_type: str = "input") -> Optional[Any]:
        """
        Make an IO value serializable.

        Parameters
        ----------
        value: Any
            The value that needs to be made serializable.
        io_type: str
            A string (either "input" or "output") to dictate where to send this IO in the case that the value is a Path.

        Returns
        -------
        value: Optional[Any]
            If the value is already a boolean, None, string, float, integer, or datetime, simply returns the value.
            If the value is a Path, ensure that the Path isn't a directory, and then send the value to the input or
            output files list based off the passed io_type and return None.
            If neither of the above occured, return the to string of the value provided.
        """
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

    def _create_io(self, value: Union[Any, List, Tuple, RunIO], io_type: str = "input") -> Optional[RunIO]:
        """
        Create a RunIO object from the provided value.

        Parameters
        ----------
        value: Union[Any, List, Tuple, RunIO]
            The value to convert to a RunIo object.
        io_type: str
            A string (either "input" or "output") to dictate where to send this IO in the case that the value is a Path.

        Returns
        -------
        io: Optional[RunIO]
            The constructed RunIO object.
            If received an already constructed RunIO object, simply returns the provided object.
            If received a single value, returns a RunIO object with the value and stores the value's type.
            If received a List or Tuple of length one, returns a RunIO object with the single value in the list.
            If received a List or Tuple of length two, returns a RunIO object with the values provided. The format of
                the List or Tuple must follow, [{value_type}, {value_to_store}].

        Examples
        --------
        ```
        io = RunManager._create_io(RunIO(
            type="<class 'str'>",
            value="hello world"
        ))
        # Returns the same RunIO that was passed in

        io = RunManager._create_io("hello world")
        # Returns the same RunIO as above

        io = RunManager._create_io([str, "hello world"])
        # Returns the same RunIO as above
        ```
        """
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
                return RunIO(str(value[0]), serializable_value)

        # Provided a single value
        # Make serializable
        serializable_value = self._make_serializable_type(value, io_type)
        if serializable_value:
            return RunIO(str(type(value)), serializable_value)

        return None

    def register_input(self, input: Union[Any, List, Tuple, RunIO]) -> RunIO:
        """
        Register a value or RunIO as an input to the run.

        Parameters
        ----------
        input: Union[Any, List, Tuple, RunIO]
            The input value that will use `RunManager._create_io` prior to adding the value to the inputs list.

        Returns
        -------
        input: RunIO
            The RunIO object that was stored in the inputs list.
        """
        # Make serializable
        input = self._create_io(input)
        # If it was a filepath, it will return None
        if input:
            self._inputs.append(input)

        return input

    def register_output(self, output: Union[Any, List, Tuple, RunIO]) -> RunIO:
        """
        Register a value or RunIO as an output to the run.

        Parameters
        ----------
        output: Union[Any, List, Tuple, RunIO]
            The output value that will use `RunManager._create_io` prior to adding the value to the outputs list.

        Returns
        -------
        output: RunIO
            The RunIO object that was stored in the outputs list.
        """
        # Make serializable
        output = self._create_io(output, "output")
        # If it was a filepath, it will return None
        if output:
            self._outputs.append(output)

    def register_run(self):
        """
        Uploads the information stored in the RunManager's instance state.

        Creates a row in the Run table of the database, and uploads and links all run inputs (and run input files) and
        all run outputs (an run output files). Additionally, links the run to the algorithm id created or found from
        the details provided on RunManager instance creation.
        """
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
            self.register_output(RunIO(str(exception_type), str(exception_value)))
            self.register_output(traceback_path)

        # Close the run
        self._completed = datetime.utcnow()
        self.register_run()
