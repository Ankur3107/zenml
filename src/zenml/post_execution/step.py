from collections import OrderedDict
from enum import Enum
from typing import Any, Dict, List

from zenml.artifacts.base_artifact import MATERIALIZERS_PROPERTY_KEY
from zenml.logger import get_logger
from zenml.metadata.base_metadata_store import BaseMetadataStore
from zenml.post_execution.artifact import PEArtifact

logger = get_logger(__name__)


# TODO: docs
class ExecutionStatus(Enum):
    Failed = "Failed"
    Completed = "Succeeded"
    Running = "Running"


class PEStep:
    """Post-execution step class which can be used to query
    artifact information associated with a pipeline step.
    """

    def __init__(
        self,
        id_: int,
        name: str,
        parameters: Dict[str, Any],
        metadata_store: BaseMetadataStore,
    ):
        """Initializes a post-execution step object.

        In most cases `PEStep` objects should not be created manually
        but retrieved from a `PEPipelineRun` object instead.

        Args:
            id_: The execution id of this step.
            name: The name of this step.
            parameters: Parameters that were used to run this step.
            metadata_store: The metadata store which should be used to fetch
                additional information related to this step.
        """
        self._id = id_
        self._name = name
        self._parameters = parameters
        self._metadata_store = metadata_store

        self._inputs: Dict[str, PEArtifact] = OrderedDict()
        self._outputs: Dict[str, PEArtifact] = OrderedDict()

    @property
    def name(self) -> str:
        """Returns the step name.

        This name is equal to the name argument passed to the @step decorator
        or the actual function name if no explicit name was given.

        Examples:
            # the step name will be "my_step"
            @step(name="my_step")
            def my_step_function(...)

            # the step name will be "my_step_function"
            @step
            def my_step_function(...)
        """
        return self._name

    @property
    def parameters(self) -> Dict[str, Any]:
        """The parameters used to run this step."""
        return self._parameters

    @property
    def status(self) -> ExecutionStatus:
        """Returns the current status of the step."""
        proto = self._metadata_store.store.get_executions_by_id([self._id])[0]
        state = proto.last_known_state

        if state == proto.COMPLETE or state == proto.CACHED:
            return ExecutionStatus.Completed
        elif state == proto.RUNNING:
            return ExecutionStatus.Running
        else:
            return ExecutionStatus.Failed

    @property
    def inputs(self) -> List[PEArtifact]:
        """Returns a list of input artifacts that were used to run this step.

        These artifacts are in the same order as defined in the signature of
        the step function.
        """
        self._ensure_inputs_outputs_fetched()
        return list(self._inputs.values())

    def get_input_names(self) -> List[str]:
        """Returns a list of all input artifact names."""
        self._ensure_inputs_outputs_fetched()
        return list(self._inputs.keys())

    def get_input(self, name: str) -> PEArtifact:
        """Returns a input artifact for the given name.

        Args:
            name: The name of the input artifact to return.

        Raises:
            KeyError: If there is no input artifact with the given name.
        """
        self._ensure_inputs_outputs_fetched()
        try:
            return self._inputs[name]
        except KeyError:
            raise KeyError(
                f"No input artifact found for name `{name}`. "
                f"This step only has inputs with the following "
                f"names: `{self.get_input_names()}`"
            )

    @property
    def outputs(self) -> List[PEArtifact]:
        """Returns a list of output artifacts that were written by this step.

        These artifacts are in the same order as defined in the signature of
        the step function.
        """
        self._ensure_inputs_outputs_fetched()
        return list(self._outputs.values())

    def get_output_names(self) -> List[str]:
        """Returns a list of all output artifact names.

        If a step only has a single output, it will have the
        default name `output`.
        """
        self._ensure_inputs_outputs_fetched()
        return list(self._outputs.keys())

    def get_output(self, name: str) -> PEArtifact:
        """Returns a output artifact for the given name.

        Args:
            name: The name of the output artifact to return.

        Raises:
            KeyError: If there is no output artifact with the given name.
        """
        self._ensure_inputs_outputs_fetched()
        try:
            return self._outputs[name]
        except KeyError:
            raise KeyError(
                f"No output artifact found for name `{name}`. "
                f"This step only has outputs with the following "
                f"names: `{self.get_output_names()}`"
            )

    def _ensure_inputs_outputs_fetched(self) -> None:
        """Fetches all step inputs and outputs from the metadata store."""
        if self._inputs or self._outputs:
            # we already fetched inputs/outputs, no need to do anything
            return

        # maps artifact types to their string representation
        artifact_type_mapping = {
            type_.id: type_.name
            for type_ in self._metadata_store.store.get_artifact_types()
        }

        events = self._metadata_store.store.get_events_by_execution_ids(
            [self._id]
        )
        artifacts = self._metadata_store.store.get_artifacts_by_id(
            [event.artifact_id for event in events]
        )

        for event_proto, artifact_proto in zip(events, artifacts):
            artifact_type = artifact_type_mapping[artifact_proto.type_id]
            artifact_name = event_proto.path.steps[0].key

            materializer = artifact_proto.properties[
                MATERIALIZERS_PROPERTY_KEY
            ].string_value

            artifact = PEArtifact(
                id_=event_proto.artifact_id,
                type_=artifact_type,
                uri=artifact_proto.uri,
                materializer=materializer,
            )

            if event_proto.type == event_proto.INPUT:
                self._inputs[artifact_name] = artifact
            elif event_proto.type == event_proto.OUTPUT:
                self._outputs[artifact_name] = artifact

        logger.debug(
            "Fetched %d inputs and %d outputs for step '%s'.",
            len(self._inputs),
            len(self._outputs),
            self._name,
        )

    def __repr__(self) -> str:
        """Returns a string representation of this step."""
        return (
            f"{self.__class__.__qualname__}(id={self._id}, "
            f"name='{self._name}', parameters={self._parameters})"
        )
