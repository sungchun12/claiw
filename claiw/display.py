"""Display utilities for workflow execution visualization.

This module provides functions and classes for rendering workflow execution
history in various formats, including text-based output and Rich-based
Gantt charts.
"""

from __future__ import annotations

import sys
from datetime import datetime
from typing import TYPE_CHECKING

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from claiw.dbos_client import WorkflowExecution, WorkflowStep

if TYPE_CHECKING:
    from claiw.dbos_client import WorkflowSummary


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


def select_workflows_for_diff(
    summaries: list[WorkflowSummary],
) -> tuple[str, str] | None:
    """Interactive selection of two workflows for comparison using prompt_toolkit.

    Displays an arrow-key navigable menu for selecting two workflow runs
    to compare (source and compare targets).

    Args:
        summaries: List of WorkflowSummary objects to choose from.

    Returns:
        Tuple of (source_id, compare_id) or None if cancelled.
    """
    from prompt_toolkit.shortcuts import radiolist_dialog
    from prompt_toolkit.styles import Style

    # Custom style for the dialog
    dialog_style = Style.from_dict(
        {
            "dialog": "bg:#1e1e1e",
            "dialog.body": "bg:#1e1e1e #d4d4d4",
            "dialog frame.label": "bg:#1e1e1e #569cd6 bold",
            "dialog shadow": "bg:#000000",
            "radiolist": "bg:#1e1e1e",
            "radio-checked": "#4ec9b0 bold",
            "radio-selected": "bg:#264f78",
        }
    )

    # Format choices for the dialog
    def format_choice(s: WorkflowSummary) -> tuple[str, str]:
        status_icon = {"success": "✓", "error": "✗", "pending": "…"}.get(
            s.status_display, "?"
        )
        return (
            s.workflow_id,
            f"{status_icon} {s.workflow_id[:12]}... ({s.created_at_formatted}) [{s.step_count} steps]",
        )

    choices = [format_choice(s) for s in summaries]

    # First selection: "Select for Compare"
    source_id = radiolist_dialog(
        title="Select for Compare",
        text="Use arrow keys to navigate, Enter to select the SOURCE workflow:",
        values=choices,
        style=dialog_style,
    ).run()

    if source_id is None:
        return None

    # Filter out the selected source for the second selection
    compare_choices = [(wid, label) for wid, label in choices if wid != source_id]

    if not compare_choices:
        return None

    # Second selection: "Compare with Selected"
    compare_id = radiolist_dialog(
        title="Compare with Selected",
        text=f"Source: {source_id[:12]}...\n\nSelect the workflow to COMPARE against:",
        values=compare_choices,
        style=dialog_style,
    ).run()

    if compare_id is None:
        return None

    return (source_id, compare_id)


def _compute_step_duration(step: WorkflowStep) -> float | None:
    """Compute duration in seconds for a step."""
    if step.started_at_epoch_ms is None or step.completed_at_epoch_ms is None:
        return None
    return (step.completed_at_epoch_ms - step.started_at_epoch_ms) / 1000.0


def _render_single_timeline(
    executions: list[WorkflowExecution],
    label: str,
    workflow_id: str,
    console: Console,
) -> None:
    """Render a single workflow timeline (helper for diff display).

    Args:
        executions: List of WorkflowExecution objects to display.
        label: Label for the timeline (e.g., "Select for Compare").
        workflow_id: The workflow ID being displayed.
        console: Rich Console for output.
    """
    # Theme colors
    WORKFLOW_COLOR = "blue"
    STEP_COMPLETE_COLOR = "green"
    STEP_ERROR_COLOR = "red"
    STEP_PENDING_COLOR = "yellow"

    def status_icon(step: WorkflowStep) -> str:
        if step.is_error:
            return "✗"
        elif step.is_success:
            return "✓"
        else:
            return "…"

    def step_style(step: WorkflowStep) -> str:
        if step.is_error:
            return STEP_ERROR_COLOR
        elif step.is_success:
            return STEP_COMPLETE_COLOR
        else:
            return STEP_PENDING_COLOR

    # Collect timeline bounds
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
        console.print(f"[yellow]No timing data available for {workflow_id}.[/yellow]")
        return

    global_start = min(all_times)
    global_end = max(all_times)
    global_duration = (global_end - global_start).total_seconds()
    if global_duration <= 0:
        global_duration = 1.0

    CHART_WIDTH = 20

    def time_to_col(t: datetime | None) -> int:
        if t is None:
            return 0
        offset = (t - global_start).total_seconds()
        return int((offset / global_duration) * CHART_WIDTH)

    def render_bar(start_col: int, end_col: int, style: str = "green") -> Text:
        bar = Text()
        bar.append(" " * start_col)
        bar_len = max(end_col - start_col, 1)
        bar.append("█" * bar_len, style=style)
        remaining = CHART_WIDTH - end_col
        bar.append(" " * remaining)
        return bar

    # Build table
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold cyan",
        expand=True,
        padding=(0, 1),
    )
    table.add_column("Step", style="bold", no_wrap=True)
    table.add_column("Timeline", no_wrap=True, width=CHART_WIDTH)
    table.add_column("Duration", justify="right", no_wrap=True)
    table.add_column("", width=2)

    for execution in executions:
        if execution.workflow_id != workflow_id:
            continue  # Only show the main workflow for simplicity

        for step_i, step in enumerate(execution.steps):
            st = _epoch_ms_to_datetime(step.started_at_epoch_ms)
            et = _epoch_ms_to_datetime(step.completed_at_epoch_ms) or st

            style = step_style(step)
            icon = status_icon(step)

            if st and et:
                start_col = time_to_col(st)
                end_col = time_to_col(et)
                bar = render_bar(start_col, end_col, style)
                duration = _compute_step_duration(step)
                dur_str = f"{duration:.2f}s" if duration is not None else "—"
            else:
                bar = Text("·····", style="dim")
                dur_str = "—"

            is_last = step_i == len(execution.steps) - 1
            connector = "└─" if is_last else "├─"
            step_label = f"{connector} {step.function_id}: {step.function_name}"

            table.add_row(
                step_label,
                bar,
                dur_str,
                Text(icon, style=f"bold {style}"),
            )

    # Print with header
    console.print(
        Panel(
            table,
            title=f"[bold]{label}[/bold]: {workflow_id[:20]}...",
            border_style="cyan",
            padding=(0, 1),
        )
    )


def display_diff(
    source_executions: list[WorkflowExecution],
    compare_executions: list[WorkflowExecution],
    source_id: str,
    compare_id: str,
) -> None:
    """Display a diff comparison between two workflow executions.

    Shows both workflows in timeline format (vertically stacked), followed by
    a diff summary with git-style color coding for differences in steps,
    duration, and output.

    Args:
        source_executions: Executions for the source workflow.
        compare_executions: Executions for the compare workflow.
        source_id: The source workflow ID.
        compare_id: The compare workflow ID.
    """
    console = Console()

    console.print()
    console.print("[bold blue]🔀 Workflow Diff Comparison[/bold blue]")
    console.print()

    # Render source timeline
    _render_single_timeline(source_executions, "Select for Compare", source_id, console)
    console.print()

    # Render compare timeline
    _render_single_timeline(
        compare_executions, "Compare with Selected", compare_id, console
    )
    console.print()

    # Build diff summary
    console.print(Panel("[bold]Diff Summary[/bold]", border_style="yellow"))

    # Get steps from main workflows
    source_steps = (
        source_executions[0].steps if source_executions else []
    )
    compare_steps = (
        compare_executions[0].steps if compare_executions else []
    )

    # Build lookup by function name for matching
    source_by_name: dict[str, WorkflowStep] = {s.function_name: s for s in source_steps}
    compare_by_name: dict[str, WorkflowStep] = {
        s.function_name: s for s in compare_steps
    }

    all_step_names = list(
        dict.fromkeys(
            [s.function_name for s in source_steps]
            + [s.function_name for s in compare_steps]
        )
    )

    # Diff table
    diff_table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold",
        expand=True,
        padding=(0, 1),
    )
    diff_table.add_column("Step", style="bold cyan", no_wrap=True)
    diff_table.add_column("Duration Δ", justify="center", no_wrap=True)
    diff_table.add_column("Output Diff", overflow="fold")

    for step_name in all_step_names:
        source_step = source_by_name.get(step_name)
        compare_step = compare_by_name.get(step_name)

        # Duration comparison
        source_dur = _compute_step_duration(source_step) if source_step else None
        compare_dur = _compute_step_duration(compare_step) if compare_step else None

        if source_dur is not None and compare_dur is not None:
            delta = compare_dur - source_dur
            if abs(delta) < 0.01:
                dur_text = Text("(same)", style="dim")
            else:
                pct = (delta / source_dur * 100) if source_dur > 0 else 0
                sign = "+" if delta > 0 else ""
                color = "red" if delta > 0 else "green"
                dur_text = Text(f"{sign}{delta:.2f}s ({pct:+.0f}%)", style=color)
        elif source_dur is None and compare_dur is None:
            dur_text = Text("—", style="dim")
        elif source_dur is None:
            dur_text = Text(f"+{compare_dur:.2f}s (new)", style="green")
        else:
            dur_text = Text(f"-{source_dur:.2f}s (removed)", style="red")

        # Output comparison
        source_output = str(source_step.output) if source_step and source_step.output else None
        compare_output = (
            str(compare_step.output) if compare_step and compare_step.output else None
        )

        output_diff = Text()
        if source_output == compare_output:
            if source_output:
                output_diff.append("(no change)", style="dim")
            else:
                output_diff.append("—", style="dim")
        else:
            # Show git-style diff
            if source_output:
                # Truncate long outputs
                src_preview = (
                    source_output[:80] + "..."
                    if len(source_output) > 80
                    else source_output
                )
                output_diff.append(f"- {src_preview}\n", style="red")
            if compare_output:
                cmp_preview = (
                    compare_output[:80] + "..."
                    if len(compare_output) > 80
                    else compare_output
                )
                output_diff.append(f"+ {cmp_preview}", style="green")

        # Step label with status
        if source_step and compare_step:
            step_label = f"{source_step.function_id}: {step_name}"
        elif source_step:
            step_label = f"[red]- {source_step.function_id}: {step_name}[/red]"
        else:
            step_label = f"[green]+ {compare_step.function_id}: {step_name}[/green]"

        diff_table.add_row(step_label, dur_text, output_diff)

    console.print(diff_table)
    console.print()
