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
    """Interactive selection of two workflows for comparison.

    Displays an arrow-key navigable menu for selecting two workflow runs
    to compare (source and compare targets). Press Enter to confirm selection.

    Args:
        summaries: List of WorkflowSummary objects to choose from.

    Returns:
        Tuple of (source_id, compare_id) or None if cancelled.
    """
    from prompt_toolkit import Application
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.layout import Layout
    from prompt_toolkit.layout.containers import HSplit, Window
    from prompt_toolkit.layout.controls import FormattedTextControl
    from prompt_toolkit.styles import Style

    console = Console()

    # Format choices
    def format_choice(s: WorkflowSummary, selected: bool = False) -> str:
        status_icon = {"success": "✓", "error": "✗", "pending": "…"}.get(
            s.status_display, "?"
        )
        prefix = "▶ " if selected else "  "
        return f"{prefix}{status_icon} {s.workflow_id[:20]}... ({s.created_at_formatted}) [{s.step_count} steps]"

    def run_selection(title: str, choices: list[WorkflowSummary], exclude_id: str | None = None) -> str | None:
        """Run a single selection prompt."""
        filtered = [s for s in choices if s.workflow_id != exclude_id]
        if not filtered:
            return None

        selected_index = [0]  # Use list for mutability in closure
        result = [None]  # Store result

        bindings = KeyBindings()

        @bindings.add("up")
        @bindings.add("k")
        def move_up(event):
            selected_index[0] = max(0, selected_index[0] - 1)

        @bindings.add("down")
        @bindings.add("j")
        def move_down(event):
            selected_index[0] = min(len(filtered) - 1, selected_index[0] + 1)

        @bindings.add("enter")
        def confirm(event):
            result[0] = filtered[selected_index[0]].workflow_id
            event.app.exit()

        @bindings.add("c-c")
        @bindings.add("escape")
        @bindings.add("q")
        def cancel(event):
            result[0] = None
            event.app.exit()

        def get_formatted_text():
            lines = [("class:title", f"\n  {title}\n"), ("", "\n")]
            lines.append(("class:hint", "  Use ↑/↓ to navigate, Enter to select, Esc to cancel\n\n"))
            
            # Header row
            header_parts = [
                "    ",
                "Workflow ID".ljust(24),
                "│ ",
                "Status".ljust(12),
                "│ ",
                "Executor".ljust(12),
                "│ ",
                "Created At".ljust(19),
                "│ ",
                "Updated At".ljust(19),
                "│ ",
                "Forked From".ljust(24),
                "│ ",
                "Steps".ljust(6),
                "\n"
            ]
            lines.append(("class:hint", "".join(header_parts)))
            lines.append(("class:hint", "    " + "─" * 120 + "\n"))
            
            for i, s in enumerate(filtered):
                is_selected = i == selected_index[0]
                base_style = "class:selected" if is_selected else ""
                prefix = "  ▶ " if is_selected else "    "
                
                status_color_style = "class:success" if s.status_display == "success" else "class:error" if s.status_display == "error" else ""
                
                # Format fields
                workflow_id_display = (s.workflow_id[:22] + "..." if len(s.workflow_id) > 25 else s.workflow_id).ljust(24)
                status_text = s.status[:10].ljust(12)
                executor_display = (s.executor_id[:10] + "..." if s.executor_id and len(s.executor_id) > 13 else s.executor_id or "—").ljust(12)
                created_display = s.created_at_formatted.ljust(19)
                updated_display = s.updated_at_formatted.ljust(19)
                forked_display = ((s.forked_from[:22] + "..." if s.forked_from and len(s.forked_from) > 25 else s.forked_from or "—")).ljust(24)
                steps_display = str(s.step_count).ljust(6)
                
                # Build the row with proper styling
                row_parts = [
                    (base_style, prefix),
                    (base_style, workflow_id_display),
                    (base_style, "│ "),
                    (f"{base_style} {status_color_style}" if status_color_style else base_style, status_text),
                    (base_style, "│ "),
                    (base_style, executor_display),
                    (base_style, "│ "),
                    (base_style, created_display),
                    (base_style, "│ "),
                    (base_style, updated_display),
                    (base_style, "│ "),
                    (base_style, forked_display),
                    (base_style, "│ "),
                    (base_style, steps_display),
                    ("", "\n")
                ]
                lines.extend(row_parts)
            return lines

        style = Style.from_dict({
            "title": "bold cyan",
            "hint": "dim",
            "selected": "bold bg:#264f78",
            "success": "green",
            "error": "red",
        })

        layout = Layout(
            HSplit([
                Window(content=FormattedTextControl(get_formatted_text), wrap_lines=False),
            ])
        )

        app: Application = Application(
            layout=layout,
            key_bindings=bindings,
            style=style,
            full_screen=False,
            mouse_support=True,
        )
        app.run()
        return result[0]

    # First selection - SOURCE
    console.print()
    source_id = run_selection("Select SOURCE workflow:", summaries)
    if source_id is None:
        return None

    # Second selection - TARGET
    target_id = run_selection(
        f"Select TARGET workflow (source: {source_id[:12]}...):",
        summaries,
        exclude_id=source_id
    )
    if target_id is None:
        return None

    return (source_id, target_id)


def _compute_step_duration(step: WorkflowStep) -> float | None:
    """Compute duration in seconds for a step."""
    if step.started_at_epoch_ms is None or step.completed_at_epoch_ms is None:
        return None
    return (step.completed_at_epoch_ms - step.started_at_epoch_ms) / 1000.0


def _get_step_style(step: WorkflowStep) -> str:
    """Get Rich style for a step based on its status."""
    if step.is_error:
        return "red"
    elif step.is_success:
        return "green"
    return "yellow"


def _get_status_icon(step: WorkflowStep) -> str:
    """Get status icon for a step."""
    if step.is_error:
        return "✗"
    elif step.is_success:
        return "✓"
    return "…"


def _compute_word_diff(source_text: str, compare_text: str) -> tuple[Text, Text]:
    """Compute word-level git-style diff between two text strings.

    Highlights the actual word-level differences like git does:
    - Common text: shown in dim
    - Deleted text (in source only): red background
    - Added text (in compare only): green background

    Args:
        source_text: The source/original text.
        compare_text: The compare/new text.

    Returns:
        Tuple of (source_diff_text, compare_diff_text) as Rich Text objects.
    """
    import difflib
    import re

    # Split into words while preserving whitespace and punctuation
    def tokenize(text: str) -> list[str]:
        return re.findall(r'\S+|\s+', text)

    source_tokens = tokenize(source_text)
    compare_tokens = tokenize(compare_text)

    matcher = difflib.SequenceMatcher(None, source_tokens, compare_tokens)

    source_result = Text()
    compare_result = Text()

    source_result.append("- ", style="red bold")
    compare_result.append("+ ", style="green bold")

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        source_chunk = "".join(source_tokens[i1:i2])
        compare_chunk = "".join(compare_tokens[j1:j2])

        if tag == "equal":
            # Same in both - show in dim
            source_result.append(source_chunk, style="dim")
            compare_result.append(compare_chunk, style="dim")
        elif tag == "replace":
            # Different - highlight the changes
            source_result.append(source_chunk, style="red on #3d0000")
            compare_result.append(compare_chunk, style="green on #003d00")
        elif tag == "delete":
            # Only in source (deleted)
            source_result.append(source_chunk, style="red on #3d0000")
        elif tag == "insert":
            # Only in compare (inserted)
            compare_result.append(compare_chunk, style="green on #003d00")

    return source_result, compare_result


def display_diff(
    source_executions: list[WorkflowExecution],
    target_executions: list[WorkflowExecution],
    source_id: str,
    target_id: str,
) -> None:
    """Display a diff comparison between two workflow executions.

    Shows matching steps stacked together with clear labels for source and
    target workflows. Uses timeline-style display with git-diff color coding.
    Includes child workflows recursively like --timeline does.

    Args:
        source_executions: Executions for the source workflow (including children).
        target_executions: Executions for the target workflow (including children).
        source_id: The source workflow ID.
        target_id: The target workflow ID.
    """
    console = Console()
    CHART_WIDTH = 25

    # Build child workflow ID sets for both source and target
    source_child_ids: set[str] = set()
    target_child_ids: set[str] = set()
    for exec in source_executions:
        for step in exec.steps:
            if step.child_workflow_id:
                source_child_ids.add(step.child_workflow_id)
    for exec in target_executions:
        for step in exec.steps:
            if step.child_workflow_id:
                target_child_ids.add(step.child_workflow_id)

    # Collect all steps from all executions in order
    # Use (workflow_id, function_id, function_name) as a unique key to handle duplicate function names
    StepKey = tuple[str, int | str, str]  # (workflow_id prefix, function_id, function_name)

    def make_step_key(step: WorkflowStep, wf_id: str) -> StepKey:
        # Use first 8 chars of workflow_id to group steps from same workflow
        return (wf_id[:8], step.function_id, step.function_name)

    source_steps_ordered: list[tuple[StepKey, WorkflowStep, bool, str]] = []
    target_steps_ordered: list[tuple[StepKey, WorkflowStep, bool, str]] = []

    for exec in source_executions:
        is_child = exec.workflow_id in source_child_ids
        for step in exec.steps:
            key = make_step_key(step, exec.workflow_id)
            source_steps_ordered.append((key, step, is_child, exec.workflow_id))

    for exec in target_executions:
        is_child = exec.workflow_id in target_child_ids
        for step in exec.steps:
            key = make_step_key(step, exec.workflow_id)
            target_steps_ordered.append((key, step, is_child, exec.workflow_id))

    # Build lookup by (function_id, function_name) for matching across workflows
    # This allows matching step 1: foo in source with step 1: foo in target
    MatchKey = tuple[int | str, str]  # (function_id, function_name)

    def make_match_key(step: WorkflowStep) -> MatchKey:
        return (step.function_id, step.function_name)

    source_by_match: dict[MatchKey, tuple[WorkflowStep, bool, str]] = {}
    target_by_match: dict[MatchKey, tuple[WorkflowStep, bool, str]] = {}

    for _, step, is_child, wf_id in source_steps_ordered:
        key = make_match_key(step)
        source_by_match[key] = (step, is_child, wf_id)

    for _, step, is_child, wf_id in target_steps_ordered:
        key = make_match_key(step)
        target_by_match[key] = (step, is_child, wf_id)

    # Collect all times for global timeline scaling
    all_times: list[datetime] = []
    for _, step, _, _ in source_steps_ordered + target_steps_ordered:
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
        global_duration = 1.0

    def time_to_col(t: datetime | None) -> int:
        if t is None:
            return 0
        offset = (t - global_start).total_seconds()
        return int((offset / global_duration) * CHART_WIDTH)

    def render_bar(step: WorkflowStep | None, style: str) -> Text:
        """Render a timeline bar for a step."""
        bar = Text()
        if step is None:
            bar.append(" " * CHART_WIDTH)
            return bar

        st = _epoch_ms_to_datetime(step.started_at_epoch_ms)
        et = _epoch_ms_to_datetime(step.completed_at_epoch_ms) or st

        if st and et:
            start_col = time_to_col(st)
            end_col = time_to_col(et)
            bar.append(" " * start_col)
            bar_len = max(end_col - start_col, 1)
            bar.append("█" * bar_len, style=style)
            bar.append(" " * (CHART_WIDTH - end_col))
        else:
            bar.append(" " * (CHART_WIDTH // 2 - 2))
            bar.append("·····", style="dim")
            bar.append(" " * (CHART_WIDTH // 2 - 3))
        return bar

    # Get all unique match keys preserving source order, then add target-only keys
    all_match_keys: list[MatchKey] = []
    seen_keys: set[MatchKey] = set()
    for _, step, _, _ in source_steps_ordered:
        key = make_match_key(step)
        if key not in seen_keys:
            all_match_keys.append(key)
            seen_keys.add(key)
    for _, step, _, _ in target_steps_ordered:
        key = make_match_key(step)
        if key not in seen_keys:
            all_match_keys.append(key)
            seen_keys.add(key)

    # Build the diff table with stacked steps
    diff_table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold blue",
        expand=True,
        padding=(0, 1),
        show_lines=False,
    )
    diff_table.add_column("Steps", style="bold", no_wrap=True, min_width=45)
    diff_table.add_column("Timeline", no_wrap=True, width=CHART_WIDTH)
    diff_table.add_column("Duration", style="dim", justify="center", no_wrap=True, min_width=22)
    diff_table.add_column("Output", overflow="fold", ratio=1, no_wrap=False)
    diff_table.add_column("", justify="center", width=2)

    # Add workflow headers
    diff_table.add_row(
        f"[bold blue]▶ SOURCE: {source_id}[/bold blue]",
        Text("▓" * CHART_WIDTH, style="bold blue"),
        f"[dim]{_get_display_time(global_start)} → {_get_display_time(global_end)}[/dim]",
        "",
        "📦",
    )
    diff_table.add_row(
        f"[bold green]▶ TARGET: {target_id}[/bold green]",
        Text("▓" * CHART_WIDTH, style="bold green"),
        "",
        "",
        "📦",
    )
    diff_table.add_row("", "", "", "", "")  # Spacer

    for step_idx, match_key in enumerate(all_match_keys):
        func_id, func_name = match_key
        source_data = source_by_match.get(match_key)
        target_data = target_by_match.get(match_key)

        source_step = source_data[0] if source_data else None
        source_is_child = source_data[1] if source_data else False
        target_step = target_data[0] if target_data else None
        target_is_child = target_data[1] if target_data else False

        is_last = step_idx == len(all_match_keys) - 1

        # Compute durations
        source_dur = _compute_step_duration(source_step) if source_step else None
        target_dur = _compute_step_duration(target_step) if target_step else None

        # Compute duration delta
        dur_delta_text = ""
        if source_dur is not None and target_dur is not None:
            delta = target_dur - source_dur
            if abs(delta) >= 0.001:
                pct = (delta / source_dur * 100) if source_dur > 0 else 0
                sign = "+" if delta > 0 else ""
                color = "red" if delta > 0 else "green"
                dur_delta_text = f"[{color}]Δ {sign}{delta:.2f}s ({pct:+.0f}%)[/{color}]"

        # Get output strings (full text, no truncation)
        source_output = str(source_step.output) if source_step and source_step.output else None
        target_output = str(target_step.output) if target_step and target_step.output else None

        outputs_match = source_output == target_output

        # Compute git-style word diff if outputs differ
        source_diff_text: Text | str | None = None
        target_diff_text: Text | str | None = None
        if source_output and target_output and not outputs_match:
            source_diff_text, target_diff_text = _compute_word_diff(source_output, target_output)
        elif source_output and not target_output:
            # Source has output, target doesn't
            src_text = Text()
            src_text.append("- ", style="red bold")
            src_text.append(source_output, style="red")
            source_diff_text = src_text
        elif target_output and not source_output:
            # Target has output, source doesn't
            tgt_text = Text()
            tgt_text.append("+ ", style="green bold")
            tgt_text.append(target_output, style="green")
            target_diff_text = tgt_text

        # Determine connector style
        connector = "└─" if is_last else "├─"
        is_child_step = source_is_child or target_is_child
        child_prefix = "  ↳ " if is_child_step else " "

        # --- SOURCE ROW (blue) - Only show if source step exists ---
        if source_step:
            style = _get_step_style(source_step)
            icon = _get_status_icon(source_step)
            bar = render_bar(source_step, "blue")
            dur_str = f"{source_dur:.2f}s" if source_dur is not None else "—"

            # Arrow if spawned child workflow
            arrow = " [yellow]→[/yellow]" if source_step.child_workflow_id else ""

            # Output - use git-style diff or show same text
            if source_output:
                if outputs_match:
                    out_preview: Text | str = source_output
                elif source_diff_text:
                    out_preview = source_diff_text
                else:
                    out_preview = "[dim]—[/dim]"
            else:
                out_preview = "[dim]—[/dim]"

            diff_table.add_row(
                f"[blue]{child_prefix}{connector} {func_id}: {func_name}{arrow}[/blue]  [dim](source)[/dim]",
                bar,
                dur_str,
                out_preview,
                Text(icon, style=f"bold {style}"),
            )

        # --- TARGET ROW (green) - Only show if target step exists ---
        if target_step:
            style = _get_step_style(target_step)
            icon = _get_status_icon(target_step)
            bar = render_bar(target_step, "green")
            dur_str = f"{target_dur:.2f}s" if target_dur is not None else "—"

            # Arrow if spawned child workflow
            arrow = " [yellow]→[/yellow]" if target_step.child_workflow_id else ""

            # Determine the step label prefix
            if source_step:
                # Both exist - show as target row
                step_prefix = f"{child_prefix}│  "
            else:
                # Only in target - show as new step
                step_prefix = f"{child_prefix}{connector} "

            # Output - use git-style diff or show same text
            if target_output:
                if outputs_match:
                    out_preview = target_output
                elif target_diff_text:
                    out_preview = target_diff_text
                else:
                    out_preview = "[dim]—[/dim]"
            else:
                out_preview = "[dim]—[/dim]"

            # Duration display
            if source_step:
                dur_display = f"{dur_str}  {dur_delta_text}" if dur_delta_text else dur_str
            else:
                dur_display = f"{dur_str}  [green](new)[/green]"

            diff_table.add_row(
                f"[green]{step_prefix}{func_id}: {func_name}{arrow}[/green]  [dim](target)[/dim]",
                bar,
                dur_display,
                out_preview,
                Text(icon, style=f"bold {style}"),
            )

        # If step only exists in source (removed in target), show the target row as removed
        if source_step and not target_step:
            diff_table.add_row(
                f"[red]{child_prefix}│  {func_id}: {func_name}[/red]  [dim](target)[/dim]",
                Text(" " * CHART_WIDTH),
                f"[red](removed)[/red]",
                "[dim]—[/dim]",
                "",
            )

        # Add spacing between step pairs
        if not is_last:
            diff_table.add_row("", "", "", "", "")

    console.print(diff_table)
    console.print()
