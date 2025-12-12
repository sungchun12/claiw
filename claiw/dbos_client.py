"""DBOS Client wrapper for claiw workflow history.

This module provides a Pythonic, type-safe interface for interacting with
DBOS workflow execution history. It uses Pydantic models for data validation
and a class-based client for extensibility.
"""

from typing import Any

from dbos import DBOSClient
from pydantic import BaseModel, Field

from claiw.registry import list_workflows_from_registry


class DBOSClientConfig(BaseModel):
    """Configuration for the ClaiW DBOS client.

    Attributes:
        database_url: SQLite or PostgreSQL connection string for the DBOS system database.
    """

    database_url: str = Field(
        default="sqlite:///dbostest.sqlite",
        description="Database URL for the DBOS system database",
    )


class WorkflowStep(BaseModel):
    """Represents a single step within a workflow execution.

    Attributes:
        function_id: The numeric or string identifier of the step function.
        function_name: The name of the function executed in this step.
        child_workflow_id: ID of a child workflow spawned by this step, if any.
        output: The output/return value of the step, if completed successfully.
        error: Error message if the step failed.
        started_at_epoch_ms: Unix timestamp (milliseconds) when the step started.
        completed_at_epoch_ms: Unix timestamp (milliseconds) when the step completed.
    """

    function_id: int | str = Field(default="?")
    function_name: str = Field(default="<?>")
    child_workflow_id: str | None = None
    output: Any | None = None
    error: str | None = None
    started_at_epoch_ms: int | None = None
    completed_at_epoch_ms: int | None = None

    @property
    def is_completed(self) -> bool:
        """Check if the step has completed (with or without error)."""
        return self.output is not None or self.error is not None

    @property
    def is_error(self) -> bool:
        """Check if the step ended with an error."""
        return self.error is not None

    @property
    def is_success(self) -> bool:
        """Check if the step completed successfully."""
        return self.output is not None and self.error is None

    @property
    def has_child_workflow(self) -> bool:
        """Check if this step spawned a child workflow."""
        return self.child_workflow_id is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create a WorkflowStep from a raw dictionary.

        Args:
            data: Dictionary containing step data from DBOS.

        Returns:
            A validated WorkflowStep instance.
        """
        return cls(
            function_id=data.get("function_id", "?"),
            function_name=data.get("function_name", "<?>"),
            child_workflow_id=data.get("child_workflow_id"),
            output=data.get("output"),
            error=data.get("error"),
            started_at_epoch_ms=data.get("started_at_epoch_ms"),
            completed_at_epoch_ms=data.get("completed_at_epoch_ms"),
        )


class WorkflowExecution(BaseModel):
    """Represents a workflow execution with all its steps.

    Attributes:
        workflow_id: The unique identifier for this workflow execution.
        steps: List of steps executed within this workflow.
    """

    workflow_id: str
    steps: list[WorkflowStep] = Field(default_factory=list)

    @property
    def child_workflow_ids(self) -> list[str]:
        """Get all child workflow IDs spawned by this workflow."""
        return [
            step.child_workflow_id
            for step in self.steps
            if step.child_workflow_id is not None
        ]

    @property
    def is_parent_of(self) -> bool:
        """Check if this workflow has spawned any child workflows."""
        return len(self.child_workflow_ids) > 0


class WorkflowSummary(BaseModel):
    """Summary information for a workflow execution.

    Attributes:
        workflow_id: The unique identifier for this workflow execution.
        name: The workflow name.
        step_count: Number of steps in this workflow.
        created_at: Unix timestamp (milliseconds) when the workflow was created.
        status: The execution status (SUCCESS, ERROR, PENDING, etc.).
        executor_id: The ID of the executor (process) that most recently executed this workflow.
        updated_at: Unix timestamp (milliseconds) when the workflow status was last updated.
        forked_from: The workflow ID this workflow was forked from, if any.
    """

    workflow_id: str
    name: str
    step_count: int = 0
    created_at: int | None = None
    status: str = "UNKNOWN"
    executor_id: str | None = None
    updated_at: int | None = None
    forked_from: str | None = None

    @property
    def created_at_formatted(self) -> str:
        """Format created_at as a human-readable datetime string."""
        if self.created_at is None:
            return "—"
        from datetime import datetime

        try:
            return datetime.fromtimestamp(self.created_at / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            return str(self.created_at)

    @property
    def updated_at_formatted(self) -> str:
        """Format updated_at as a human-readable datetime string."""
        if self.updated_at is None:
            return "—"
        from datetime import datetime

        try:
            return datetime.fromtimestamp(self.updated_at / 1000).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        except Exception:
            return str(self.updated_at)

    @property
    def status_display(self) -> str:
        """Get a display-friendly status with color hint."""
        status_map = {
            "SUCCESS": "success",
            "ERROR": "error",
            "PENDING": "pending",
            "RETRIES_EXCEEDED": "error",
            "CANCELLED": "cancelled",
        }
        return status_map.get(self.status, "unknown")


class ClaiwDBOSClient:
    """Type-safe client for interacting with DBOS workflow history.

    This client wraps the DBOSClient and provides typed methods that return
    Pydantic models for workflow execution history.

    Attributes:
        config: Configuration for the DBOS client connection.

    Example:
        ```python
        config = DBOSClientConfig(database_url="sqlite:///mydb.sqlite")
        client = ClaiWDBOSClient(config)
        history = client.get_workflow_history("my_workflow")
        for execution in history:
            print(f"Workflow {execution.workflow_id} has {len(execution.steps)} steps")
        ```
    """

    def __init__(self, config: DBOSClientConfig | None = None) -> None:
        """Initialize the ClaiW DBOS client.

        Args:
            config: Configuration for the DBOS client. Uses defaults if not provided.
        """
        self.config = config or DBOSClientConfig()
        self._client = DBOSClient(self.config.database_url)

    def get_latest_workflow_id(self, name: str) -> str | None:
        """Get the latest workflow execution ID for a given workflow name.

        Args:
            name: The name of the workflow to look up.

        Returns:
            The workflow ID of the most recent execution, or None if not found.
        """
        workflows = self._client.list_workflows(name=name, limit=1, sort_desc=True)
        if workflows:
            return workflows[0].workflow_id
        return None

    def get_latest_workflows_by_name(self) -> dict[str, str]:
        """Get the latest workflow IDs for all workflows in the registry.

        Queries the claiw registry for all registered workflows and finds
        the most recent DBOS execution for each.

        Returns:
            Dictionary mapping workflow names to their latest execution IDs.
        """
        workflows_from_registry = list_workflows_from_registry()
        latest_by_name: dict[str, str] = {}

        for workflow in workflows_from_registry:
            workflow_name = workflow["name"]
            dbos_workflows = self._client.list_workflows(
                name=workflow_name, limit=1, sort_desc=True
            )
            if dbos_workflows:
                latest_by_name[workflow_name] = dbos_workflows[0].workflow_id

        return latest_by_name

    def get_recent_workflows_summary(
        self, limit_per_name: int = 3
    ) -> dict[str, list[WorkflowSummary]]:
        """Get recent workflow summaries for all registered workflows.

        Returns the most recent N executions for each workflow in the registry,
        with summary information including step count, status, and timestamps.

        Args:
            limit_per_name: Maximum number of recent executions per workflow name.

        Returns:
            Dictionary mapping workflow names to lists of WorkflowSummary objects.
        """
        workflows_from_registry = list_workflows_from_registry()
        summaries_by_name: dict[str, list[WorkflowSummary]] = {}

        for workflow in workflows_from_registry:
            workflow_name = workflow["name"]
            dbos_workflows = self._client.list_workflows(
                name=workflow_name, limit=limit_per_name, sort_desc=True
            )

            summaries: list[WorkflowSummary] = []
            for wf in dbos_workflows:
                # Get step count for this workflow (with fallback for missing app db)
                try:
                    steps = self._client.list_workflow_steps(wf.workflow_id)
                    step_count = len(steps)
                except Exception as e:
                    # Fallback to sys_db if transaction_outputs table doesn't exist
                    if "no such table: transaction_outputs" in str(
                        e
                    ) or "does not exist" in str(e):
                        try:
                            steps = self._client._sys_db.get_workflow_steps(
                                wf.workflow_id
                            )
                            step_count = len(steps)
                        except Exception:
                            step_count = 0
                    else:
                        step_count = 0

                summaries.append(
                    WorkflowSummary(
                        workflow_id=wf.workflow_id,
                        name=wf.name,
                        step_count=step_count,
                        created_at=wf.created_at,
                        status=wf.status,
                        executor_id=getattr(wf, "executor_id", None),
                        updated_at=getattr(wf, "updated_at", wf.created_at),
                        forked_from=getattr(wf, "forked_from", None),
                    )
                )

            if summaries:
                summaries_by_name[workflow_name] = summaries

        return summaries_by_name

    def get_workflow_steps_recursive(
        self,
        workflow_id: str,
        visited: set[str] | None = None,
        has_app_db: bool = True,
    ) -> list[WorkflowExecution]:
        """Recursively get all steps for a workflow and its child workflows.

        Args:
            workflow_id: The workflow ID to get steps for.
            visited: Set of already-visited workflow IDs (for cycle detection).
            has_app_db: Whether the application database is available.

        Returns:
            List of WorkflowExecution objects for the workflow and all children.
        """
        if visited is None:
            visited = set()

        if workflow_id in visited:
            return []

        visited.add(workflow_id)

        # Get steps for this workflow
        try:
            raw_steps = self._client.list_workflow_steps(workflow_id)
        except Exception as e:
            # If transaction_outputs table doesn't exist, fall back to system DB only
            if "no such table: transaction_outputs" in str(
                e
            ) or "does not exist" in str(e):
                raw_steps = self._client._sys_db.get_workflow_steps(workflow_id)
                has_app_db = False
            else:
                raise

        # Convert raw dictionaries to Pydantic models
        steps = [WorkflowStep.from_dict(step) for step in raw_steps]
        executions = [WorkflowExecution(workflow_id=workflow_id, steps=steps)]

        # Recursively get steps for child workflows
        for step in steps:
            if step.child_workflow_id:
                executions.extend(
                    self.get_workflow_steps_recursive(
                        step.child_workflow_id, visited, has_app_db
                    )
                )

        return executions

    def get_workflow_history(self, name: str) -> list[WorkflowExecution]:
        """Get the complete execution history for the latest run of a workflow.

        This is a convenience method that combines getting the latest workflow ID
        and recursively fetching all steps including child workflows.

        Args:
            name: The name of the workflow to get history for.

        Returns:
            List of WorkflowExecution objects for the workflow and all children.

        Raises:
            ValueError: If no workflow execution is found for the given name.
        """
        workflow_id = self.get_latest_workflow_id(name)
        if workflow_id is None:
            raise ValueError(f"No workflow execution found for '{name}'")

        return self.get_workflow_steps_recursive(workflow_id)

    def get_workflow_summaries_by_name(
        self, name: str, limit: int = 10
    ) -> list[WorkflowSummary]:
        """Get recent workflow summaries for a specific workflow name.

        Args:
            name: The workflow name to get summaries for.
            limit: Maximum number of recent executions to return.

        Returns:
            List of WorkflowSummary objects for the workflow, sorted by most recent first.
        """
        dbos_workflows = self._client.list_workflows(
            name=name, limit=limit, sort_desc=True
        )

        summaries: list[WorkflowSummary] = []
        for wf in dbos_workflows:
            # Get step count for this workflow (with fallback for missing app db)
            try:
                steps = self._client.list_workflow_steps(wf.workflow_id)
                step_count = len(steps)
            except Exception as e:
                # Fallback to sys_db if transaction_outputs table doesn't exist
                if "no such table: transaction_outputs" in str(
                    e
                ) or "does not exist" in str(e):
                    try:
                        steps = self._client._sys_db.get_workflow_steps(wf.workflow_id)
                        step_count = len(steps)
                    except Exception:
                        step_count = 0
                else:
                    step_count = 0

            summaries.append(
                WorkflowSummary(
                    workflow_id=wf.workflow_id,
                    name=wf.name,
                    step_count=step_count,
                    created_at=wf.created_at,
                    status=wf.status,
                    executor_id=getattr(wf, "executor_id", None),
                    updated_at=getattr(wf, "updated_at", None),
                    forked_from=getattr(wf, "forked_from", None),
                )
            )

        return summaries


# Default client instance for convenience (lazy initialization)
_default_client: ClaiwDBOSClient | None = None


def get_default_client() -> ClaiwDBOSClient:
    """Get the default ClaiW DBOS client instance.

    Returns:
        The default client instance, creating it if necessary.
    """
    global _default_client
    if _default_client is None:
        _default_client = ClaiwDBOSClient()
    return _default_client
