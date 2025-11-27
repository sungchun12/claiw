"""Display utilities for workflow execution visualization.

This module provides functions and classes for rendering workflow execution
history in various formats, including text-based output and Rich-based
Gantt charts.
"""

import sys
from datetime import datetime

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from claiw.dbos_client import WorkflowExecution, WorkflowStep


# ANSI color codes for terminal output
class TerminalColors:
    """ANSI escape codes for terminal text formatting."""

    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def _format_epoch_ms(epoch_ms: int | None) -> str:
    """Format an epoch timestamp in milliseconds to a human-readable string.

    Args:
        epoch_ms: Unix timestamp in milliseconds, or None.

    Returns:
        Formatted datetime string, or "—" if None.
    """
    if epoch_ms is None:
        return "—"
    try:
        return datetime.fromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(epoch_ms)


def _epoch_ms_to_datetime(epoch_ms: int | None) -> datetime | None:
    """Convert epoch milliseconds to a datetime object.

    Args:
        epoch_ms: Unix timestamp in milliseconds, or None.

    Returns:
        Datetime object, or None if conversion fails.
    """
    if epoch_ms is None:
        return None
    try:
        return datetime.fromtimestamp(epoch_ms / 1000)
    except Exception:
        return None


def _get_display_time(dt: datetime | None) -> str:
    """Format a datetime for display.

    Args:
        dt: Datetime object or None.

    Returns:
        Formatted time string (HH:MM:SS) or "—".
    """
    return dt.strftime("%H:%M:%S") if dt else "—"


def _get_step_status_string(step: WorkflowStep) -> str:
    """Get a colored status string for a step.

    Args:
        step: The workflow step to get status for.

    Returns:
        ANSI-colored status string.
    """
    c = TerminalColors
    if step.is_error:
        return f"{c.RED}✗ error{c.ENDC}"
    elif step.is_success:
        return f"{c.GREEN}✓ done{c.ENDC}"
    else:
        return f"{c.YELLOW}… pending{c.ENDC}"


def print_steps(executions: list[WorkflowExecution]) -> None:
    """Pretty print all steps and child workflows to stdout.

    Displays a text-based tree view of workflow executions with colored
    status indicators, output previews, and timing information.

    Args:
        executions: List of WorkflowExecution objects to display.
    """
    c = TerminalColors

    for workflow_i, execution in enumerate(executions):
        header_line = f"{c.BOLD}{c.HEADER}Workflow {workflow_i + 1}: {execution.workflow_id}{c.ENDC}\n"
        sys.stdout.write(header_line)

        if not execution.steps:
            sys.stdout.write(f"  {c.YELLOW}(No steps for this workflow){c.ENDC}\n")
            continue

        for step in execution.steps:
            step_num = step.function_id
            name = step.function_name
            status_str = _get_step_status_string(step)
            started = _format_epoch_ms(step.started_at_epoch_ms)
            completed = _format_epoch_ms(step.completed_at_epoch_ms)

            line = f"  {c.CYAN}Step {step_num: <2}{c.ENDC}: {c.BOLD}{name}{c.ENDC} {status_str}\n"
            sys.stdout.write(line)

            # Output short preview
            if step.output is not None:
                preview = str(step.output)
                if len(preview) > 150:
                    preview = preview[:147] + "..."
                preview_lines = preview.splitlines() or [preview]
                for ol in preview_lines:
                    sys.stdout.write(f"{c.GREEN}      Output: {ol}{c.ENDC}\n")

            # Error
            if step.error:
                preview = str(step.error)
                if len(preview) > 150:
                    preview = preview[:147] + "..."
                sys.stdout.write(f"{c.RED}      Error: {preview}{c.ENDC}\n")

            # Started/completed
            sys.stdout.write(f"      {c.BLUE}Started:   {started}{c.ENDC}\n")
            sys.stdout.write(f"      {c.BLUE}Completed: {completed}{c.ENDC}\n")

            # Child workflow
            if step.child_workflow_id:
                sys.stdout.write(
                    f"      {c.YELLOW}↳ Child workflow: {step.child_workflow_id}{c.ENDC}\n"
                )

        sys.stdout.write("\n")


def display_timeline(executions: list[WorkflowExecution]) -> None:
    """Render a Gantt-style chart showing workflows and their step timings.

    Uses Rich library to display a beautiful, colored timeline showing
    the relative timing of workflow steps and child workflows.

    Args:
        executions: List of WorkflowExecution objects to display.
    """
    console = Console()

    # Theme colors
    WORKFLOW_COLOR = "blue"
    CHILD_WORKFLOW_COLOR = "yellow"
    STEP_COMPLETE_COLOR = "green"
    STEP_ERROR_COLOR = "red"
    STEP_PENDING_COLOR = "yellow"

    def status_icon(step: WorkflowStep) -> str:
        """Get status icon for a step."""
        if step.is_error:
            return "✗"
        elif step.is_success:
            return "✓"
        else:
            return "…"

    def step_style(step: WorkflowStep) -> str:
        """Get Rich style for a step based on its status."""
        if step.is_error:
            return STEP_ERROR_COLOR
        elif step.is_success:
            return STEP_COMPLETE_COLOR
        else:
            return STEP_PENDING_COLOR

    # Collect global timeline bounds
    all_times: list[datetime] = []
    for execution in executions:
        for step in execution.steps:
            st = _epoch_ms_to_datetime(step.started_at_epoch_ms)
            et = _epoch_ms_to_datetime(step.completed_at_epoch_ms)
            if st:
                all_times.append(st)
            if et:
                all_times.append(et)

    if not all_times:
        console.print("[yellow]No timing data available.[/yellow]")
        return

    global_start = min(all_times)
    global_end = max(all_times)
    global_duration = (global_end - global_start).total_seconds()
    if global_duration <= 0:
        global_duration = 1.0  # Avoid division by zero

    # Chart dimensions
    CHART_WIDTH = 25

    def time_to_col(t: datetime | None) -> int:
        """Convert a datetime to a column position in the chart."""
        if t is None:
            return 0
        offset = (t - global_start).total_seconds()
        return int((offset / global_duration) * CHART_WIDTH)

    def render_bar(
        start_col: int, end_col: int, char: str = "█", style: str = "green"
    ) -> Text:
        """Render a single bar segment."""
        bar = Text()
        bar.append(" " * start_col)
        bar_len = max(end_col - start_col, 1)
        bar.append(char * bar_len, style=style)
        remaining = CHART_WIDTH - end_col
        bar.append(" " * remaining)
        return bar

    # Build set of child workflow IDs for quick lookup
    child_workflow_ids: set[str] = set()
    for execution in executions:
        for step in execution.steps:
            if step.child_workflow_id:
                child_workflow_ids.add(step.child_workflow_id)

    # Build the Gantt chart as a table
    gantt_table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold blue",
        expand=True,
        padding=(0, 1),
        show_lines=False,
    )
    gantt_table.add_column("Steps", style="bold", no_wrap=True, overflow="visible")
    gantt_table.add_column("Timeline", no_wrap=True, width=25)
    gantt_table.add_column(
        "Duration", style="dim", justify="center", no_wrap=True, overflow="visible"
    )
    gantt_table.add_column(
        "Output", style="dim", no_wrap=False, overflow="fold", ratio=1
    )
    gantt_table.add_column("", justify="center", width=2)

    for execution in executions:
        is_child = execution.workflow_id in child_workflow_ids
        indent = "  ↳ " if is_child else ""
        wf_display_id = execution.workflow_id

        # Workflow header row
        if execution.steps:
            wf_times = [
                (
                    _epoch_ms_to_datetime(s.started_at_epoch_ms),
                    _epoch_ms_to_datetime(s.completed_at_epoch_ms),
                )
                for s in execution.steps
                if s.started_at_epoch_ms
            ]
            wf_start = min((st for st, _ in wf_times if st), default=global_start)
            wf_end = max((et for _, et in wf_times if et), default=wf_start)
            wf_dur = (wf_end - wf_start).total_seconds() if wf_start and wf_end else 0

            start_col = time_to_col(wf_start)
            end_col = time_to_col(wf_end)

            # Workflow-level bar
            bar = Text()
            bar.append(" " * start_col)
            bar_len = max(end_col - start_col, 1)
            wf_color = CHILD_WORKFLOW_COLOR if is_child else WORKFLOW_COLOR
            bar.append("▓" * bar_len, style=f"bold {wf_color}")
            bar.append(" " * (CHART_WIDTH - end_col))

            gantt_table.add_row(
                f"{indent}[{wf_color}]▶ {wf_display_id}[/{wf_color}]",
                bar,
                f"{_get_display_time(wf_start)} → {_get_display_time(wf_end)}",
                f"[cyan]{wf_dur:.1f}s[/cyan]",
                "📦",
            )
        else:
            empty_bar = Text()
            empty_bar.append(" " * CHART_WIDTH)
            wf_color = CHILD_WORKFLOW_COLOR if is_child else WORKFLOW_COLOR
            gantt_table.add_row(
                f"{indent}[{wf_color}]▶ {wf_display_id}[/{wf_color}]",
                empty_bar,
                "—",
                "",
                "—",
            )
            continue

        # Step rows
        for step_i, step in enumerate(execution.steps):
            step_num = step.function_id
            step_display = step.function_name

            st = _epoch_ms_to_datetime(step.started_at_epoch_ms)
            et = _epoch_ms_to_datetime(step.completed_at_epoch_ms) or st

            style = step_style(step)
            icon = status_icon(step)

            if st and et:
                start_col = time_to_col(st)
                end_col = time_to_col(et)
                bar = render_bar(start_col, end_col, "█", style)
            else:
                bar = Text()
                bar.append(" " * (CHART_WIDTH // 2 - 4))
                bar.append("·····", style="dim")
                bar.append(" " * (CHART_WIDTH // 2 - 4))

            # Check if this step spawned a child workflow
            arrow = " [yellow]→[/yellow]" if step.child_workflow_id else ""

            # Get output/error preview
            output_preview = ""
            if step.error:
                error_str = str(step.error).replace("\n", " ")
                output_preview = f"[red]Error: {error_str}[/red]"
            elif step.output is not None:
                output_str = str(step.output).replace("\n", " ")
                output_preview = f"[white]{output_str}[/white]"

            # Format time range
            if st and et:
                time_str = f"{_get_display_time(st)} → {_get_display_time(et)}"
            else:
                time_str = "—"

            # Tree structure with proper connectors
            is_last = step_i == len(execution.steps) - 1
            if is_child:
                connector = "└─" if is_last else "├─"
                step_label = f"   {connector} {step_num}: {step_display}{arrow}"
            else:
                connector = "└─" if is_last else "├─"
                step_label = f" {connector} {step_num}: {step_display}{arrow}"

            gantt_table.add_row(
                step_label,
                bar,
                time_str,
                output_preview,
                Text(icon, style=f"bold {style}"),
            )

    # Render
    console.print()
    console.print("[bold blue]📊 Workflow Execution Gantt Chart[/bold blue]")
    console.print(
        f"[dim]   Timeline: {_get_display_time(global_start)} → {_get_display_time(global_end)}[/dim]"
    )
    console.print()
    console.print(gantt_table)
    console.print()


class WorkflowRenderer:
    """Extensible renderer for workflow execution visualization.

    This class provides a structured way to render workflow execution data
    in various formats. Subclass and override methods for custom rendering.

    Attributes:
        console: Rich Console instance for output.
    """

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the renderer.

        Args:
            console: Optional Rich Console instance. Creates one if not provided.
        """
        self.console = console or Console()

    def render(self, executions: list[WorkflowExecution]) -> None:
        """Render workflow executions using the default display methods.

        Args:
            executions: List of WorkflowExecution objects to render.
        """
        print_steps(executions)
        display_timeline(executions)

    def render_text(self, executions: list[WorkflowExecution]) -> None:
        """Render workflow executions as plain text.

        Args:
            executions: List of WorkflowExecution objects to render.
        """
        print_steps(executions)

    def render_gantt(self, executions: list[WorkflowExecution]) -> None:
        """Render workflow executions as a Gantt chart.

        Args:
            executions: List of WorkflowExecution objects to render.
        """
        display_timeline(executions)
