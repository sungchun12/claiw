from dbos import DBOSClient  
from registry import list_workflows as list_workflows_from_registry

dbos_client = DBOSClient("sqlite:///dbostest.sqlite")

"""
This is meant to grab all the latest history for workflows registered in the claiw registry.

TODO: likely make this a class

Get specific steps and child workflows and steps for a given workflow name.
"""

def get_workflow_step_latest_history(name: str) -> list[dict]:
    latest_workflow_id = get_latest_dbos_workflow_id_by_name(name)

    # breakpoint()
    steps = get_all_steps_recursive(latest_workflow_id)
    print(steps)
    print_steps(steps)
    display_timeline(steps)
    return steps

def get_latest_dbos_workflow_id_by_name(name: str) -> str:
    """Get the latest DBOS workflow id by name."""
    latest_workflow_id = dbos_client.list_workflows(name=name, limit=1, sort_desc=True)[0].workflow_id
    return latest_workflow_id

def get_latest_dbos_workflows_by_name() -> dict[str, str]:
    """Get the latest DBOS workflows for all workflows in the registry."""
    workflows_from_registry = list_workflows_from_registry() # TODO: need to fix how name in DBOS state is different from claiw registry
    latest_dbos_workflows_by_name = {}
    for workflow in workflows_from_registry:
        dbos_workflows = dbos_client.list_workflows(name=workflow['name'], limit=1, sort_desc=True)
        if dbos_workflows:
            latest_dbos_workflows_by_name[workflow['name']] = dbos_workflows[0].workflow_id
        else:
            print(f"No DBOS workflow found for {workflow['name']}")
    return latest_dbos_workflows_by_name


def get_all_steps_recursive(workflow_id: str, visited=None, has_app_db=True):  
    """Recursively get all steps and child workflows  
      
    Args:  
        workflow_id: The workflow ID to get steps for  
        visited: Set of already-visited workflow IDs (for cycle detection)  
        has_app_db: Whether the application database is available  
    """  
    if visited is None:  
        visited = set()  
      
    if workflow_id in visited:  
        return []  
      
    visited.add(workflow_id)  
      
    # Get steps for this workflow  
    try:  
        steps = dbos_client.list_workflow_steps(workflow_id)  
    except Exception as e:  
        # If transaction_outputs table doesn't exist, fall back to system DB only  
        if "no such table: transaction_outputs" in str(e) or "does not exist" in str(e):  
            # Directly query system database for steps only (no transactions)  
            steps = dbos_client._sys_db.get_workflow_steps(workflow_id)  
            has_app_db = False  # Mark that app DB is unavailable for child workflows  
        else:  
            raise  
      
    all_steps = [(workflow_id, steps)]  
      
    # Recursively get steps for child workflows  
    for step in steps:  
        child_id = step.get("child_workflow_id")  
        if child_id:  
            all_steps.extend(get_all_steps_recursive(child_id, visited, has_app_db))  
      
    return all_steps

def print_steps(steps: list[dict]) -> None:
    """
    Pretty print all steps and child workflows for all workflows in the registry.
    Steps should be a list of tuples: (workflow_id, [step_dicts])
    """

    import sys
    from datetime import datetime

    # Unicode box drawing
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

    def fmt_time(epoch_ms):
        if epoch_ms is None:
            return "—"
        try:
            # Handles both int and float
            return datetime.fromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return str(epoch_ms)

    def indent(lines, level=1, char="│   "):
        return "".join(char * level + line for line in lines)

    for workflow_i, (workflow_id, step_list) in enumerate(steps):
        header_line = f"{BOLD}{HEADER}Workflow {workflow_i + 1}: {workflow_id}{ENDC}\n"
        sys.stdout.write(header_line)

        if not step_list:
            sys.stdout.write(f"  {YELLOW}(No steps for this workflow){ENDC}\n")
            continue

        for step in step_list:
            step_num = step.get("function_id", "?")
            name = step.get("function_name", "<?>")
            child = step.get("child_workflow_id")
            output = step.get("output")
            error = step.get("error")
            started = fmt_time(step.get("started_at_epoch_ms"))
            completed = fmt_time(step.get("completed_at_epoch_ms"))

            # Status
            status_str = ""
            if error:
                status_str = f"{RED}✗ error{ENDC}"
            elif output is not None:
                status_str = f"{GREEN}✓ done{ENDC}"
            else:
                status_str = f"{YELLOW}… pending{ENDC}"

            line = f"  {CYAN}Step {step_num: <2}{ENDC}: {BOLD}{name}{ENDC} {status_str}\n"
            sys.stdout.write(line)

            # Output short preview
            if output is not None:
                preview = str(output)
                # Truncate if very long
                if len(preview) > 150:
                    preview = preview[:147] + "..."
                preview_lines = preview.splitlines() or [preview]
                for ol_i, ol in enumerate(preview_lines):
                    prefix = "      " if ol_i == 0 else "      "
                    sys.stdout.write(f"{GREEN}{prefix}Output: {ol}{ENDC}\n")

            # Error
            if error:
                preview = str(error)
                if len(preview) > 150:
                    preview = preview[:147] + "..."
                sys.stdout.write(f"{RED}      Error: {preview}{ENDC}\n")

            # Started/completed
            sys.stdout.write(f"      {BLUE}Started:   {started}{ENDC}\n")
            sys.stdout.write(f"      {BLUE}Completed: {completed}{ENDC}\n")

            # Child workflow
            if child:
                sys.stdout.write(f"      {YELLOW}↳ Child workflow: {child}{ENDC}\n")

        sys.stdout.write("\n")


from typing import List, Dict, Any, Tuple
from datetime import datetime
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

def display_timeline(steps: List[Tuple[str, List[dict]]]) -> None:
    """
    Renders a beautiful Gantt-style chart showing workflows, steps, and child workflows
    with their relative timings. All bars are pre-filled to show completed state.

    Args:
        steps: List of tuples (workflow_id, [step_dicts]), as returned by get_all_steps_recursive.
    """
    console = Console()
    
    # Theme colors
    WORKFLOW_COLOR = "blue"            # blue for main workflows
    CHILD_WORKFLOW_COLOR = "yellow"    # yellow for child workflows
    STEP_COMPLETE_COLOR = "green"
    STEP_ERROR_COLOR = "red"
    STEP_PENDING_COLOR = "yellow"
    CHILD_COLOR = "cyan"
    
    def fmt_time(epoch_ms) -> datetime | None:
        if epoch_ms is None:
            return None
        try:
            return datetime.fromtimestamp(epoch_ms / 1000)
        except Exception:
            return None

    def get_display_time(dt: datetime) -> str:
        return dt.strftime("%H:%M:%S") if dt else "—"
    
    def get_display_time_short(dt: datetime) -> str:
        """Shorter time format for table display."""
        return dt.strftime("%M:%S") if dt else "—"

    def status_icon(step: Dict[str, Any]) -> str:
        if step.get("error"):
            return "✗"
        elif step.get("output") is not None:
            return "✓"
        else:
            return "…"

    def step_style(step: Dict[str, Any]) -> str:
        if step.get("error"):
            return STEP_ERROR_COLOR
        elif step.get("output") is not None:
            return STEP_COMPLETE_COLOR
        else:
            return STEP_PENDING_COLOR

    # Collect global timeline bounds
    all_times = []
    for workflow_id, step_list in steps:
        for step in step_list:
            st = fmt_time(step.get("started_at_epoch_ms"))
            et = fmt_time(step.get("completed_at_epoch_ms"))
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
    
    def time_to_col(t: datetime) -> int:
        """Convert a datetime to a column position in the chart."""
        if t is None:
            return 0
        offset = (t - global_start).total_seconds()
        return int((offset / global_duration) * CHART_WIDTH)
    
    def render_bar(start_col: int, end_col: int, char: str = "█", style: str = "green") -> Text:
        """Render a single bar segment."""
        bar = Text()
        bar.append(" " * start_col)
        bar_len = max(end_col - start_col, 1)
        bar.append(char * bar_len, style=style)
        remaining = CHART_WIDTH - end_col
        bar.append(" " * remaining)
        return bar
    
    # Build the Gantt chart as a table
    gantt_table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold blue",
        expand=True,
        padding=(0, 1),
        show_lines=False,  # Remove lines for cleaner look
    )
    gantt_table.add_column("Steps", style="bold", no_wrap=True, overflow="visible")
    gantt_table.add_column("Timeline", no_wrap=True, width=25)
    gantt_table.add_column("Duration", style="dim", justify="center", no_wrap=True, overflow="visible")
    gantt_table.add_column("Output", style="dim", no_wrap=False, overflow="fold", ratio=1)
    gantt_table.add_column("", justify="center", width=2)
    
    for workflow_i, (workflow_id, step_list) in enumerate(steps):
        # Determine if this is a child workflow
        is_child = False
        for other_wf_id, other_steps in steps:
            if other_wf_id == workflow_id:
                continue
            for s in other_steps:
                if s.get("child_workflow_id") == workflow_id:
                    is_child = True
                    break
            if is_child:
                break
        
        indent = "  ↳ " if is_child else ""
        # Don't truncate - show full workflow ID
        wf_display_id = workflow_id
        
        # Workflow header row
        if step_list:
            wf_times = [
                (fmt_time(s.get("started_at_epoch_ms")), fmt_time(s.get("completed_at_epoch_ms")))
                for s in step_list if s.get("started_at_epoch_ms")
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
            # Use different color for child workflows
            wf_color = CHILD_WORKFLOW_COLOR if is_child else WORKFLOW_COLOR
            bar.append("▓" * bar_len, style=f"bold {wf_color}")
            bar.append(" " * (CHART_WIDTH - end_col))
            
            gantt_table.add_row(
                f"{indent}[{wf_color}]▶ {wf_display_id}[/{wf_color}]",
                bar,
                f"{get_display_time(wf_start)} → {get_display_time(wf_end)}",
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
        for step_i, step in enumerate(step_list):
            step_num = step.get("function_id", "?")
            step_name = step.get("function_name", "<?>")
            # Don't truncate - show full step name
            step_display = step_name
            
            st = fmt_time(step.get("started_at_epoch_ms"))
            et = fmt_time(step.get("completed_at_epoch_ms")) or st
            
            style = step_style(step)
            icon = status_icon(step)
            
            if st and et:
                dur = (et - st).total_seconds()
                start_col = time_to_col(st)
                end_col = time_to_col(et)
                bar = render_bar(start_col, end_col, "█", style)
                dur_str = f"{dur:.1f}s"
            else:
                dur_str = "—"
                bar = Text()
                bar.append(" " * (CHART_WIDTH // 2 - 4))
                bar.append("·····", style="dim")
                bar.append(" " * (CHART_WIDTH // 2 - 4))
            
            # Check if this step spawned a child workflow
            child_wf = step.get("child_workflow_id")
            arrow = " [yellow]→[/yellow]" if child_wf else ""
            
            # Get output/error preview
            output = step.get("output")
            error = step.get("error")
            output_preview = ""
            if error:
                error_str = str(error).replace('\n', ' ')
                output_preview = f"[red]Error: {error_str}[/red]"
            elif output is not None:
                output_str = str(output)
                # Clean up the output string - preserve natural line breaks
                output_str = output_str.replace('\n', ' ')
                output_preview = f"[white]{output_str}[/white]"
            
            # Format time range
            if st and et:
                time_str = f"{get_display_time(st)} → {get_display_time(et)}"
            else:
                time_str = "—"
            
            # Tree structure with proper connectors
            is_last = step_i == len(step_list) - 1
            if is_child:
                # For child workflows, use proper tree lines
                prefix = "   │ " if not is_last else "   │ "
                connector = "└─" if is_last else "├─"
                step_label = f"{prefix[:-2]}{connector} {step_num}: {step_display}{arrow}"
            else:
                # For parent workflows
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
    console.print(f"[bold blue]📊 Workflow Execution Gantt Chart[/bold blue]")
    console.print(f"[dim]   Timeline: {get_display_time(global_start)} → {get_display_time(global_end)}[/dim]")
    console.print()
    console.print(gantt_table)
    console.print()

get_workflow_step_latest_history('example')