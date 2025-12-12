import json
import click
import asyncio
import inspect
import importlib
import sys
import os

from claiw.registry import (
    register_workflows,
    list_workflows_from_registry,
    get_workflow,
)
from claiw.dbos_config import configure_dbos, launch_dbos


@click.group()
@click.version_option()
def main():
    """claiw: A supercharged agent workflow CLI."""
    pass


@main.command()
@click.argument("name", required=False)
def run(name: str | None) -> None:
    """Run a registered workflow.

    NAME: The name of the workflow to run.
    """
    # 1. Configure DBOS so DBOSAgent() calls work during import
    # This MUST happen before we import any modules that instantiate DBOSAgent
    try:
        configure_dbos()
    except Exception as e:
        click.echo(f"Warning: Failed to configure DBOS: {e}")

    # 2. Register/Import workflows
    register_workflows()

    if not name:
        # List workflows
        workflows = list_workflows_from_registry()
        if not workflows:
            click.echo("No workflows found in @workflow_registry.")
            return

        click.echo("Available Workflows:")
        for wf in workflows:
            click.echo(f"- {wf['name']}: {wf['description']}")
        return

    # Run specific workflow
    workflow = get_workflow(name)
    if not workflow:
        click.echo(f"Error: Workflow '{name}' not found.")
        return

    click.echo(f"Running workflow: {name}...")

    # Add the current working directory to sys.path to ensure we can import modules
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        # 3. Import the module dynamically using importlib
        # This executes the top-level code in the agent file
        module_name = f"workflow_registry.{name}"
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)

        # 4. NOW launch DBOS (after agent is registered via import)
        try:
            launch_dbos()
        except Exception as e:
            click.echo(f"Warning: Failed to launch DBOS: {e}")

        # 5. Find and execute claiw_handler
        if not hasattr(module, "claiw_handler"):
            click.echo(
                f"Error: Workflow '{name}' missing required 'claiw_handler' function.\n"
                f"Define your entrypoint as:\n\n"
                f"    @DBOS.workflow(name='{name}')\n"
                f"    async def claiw_handler() -> None:\n"
                f"        ...",
                err=True,
            )
            return

        handler = module.claiw_handler
        if not callable(handler):
            click.echo(
                f"Error: 'claiw_handler' in workflow '{name}' is not callable.",
                err=True,
            )
            return

        # Execute the handler
        if inspect.iscoroutinefunction(handler):
            asyncio.run(handler())
        else:
            handler()

    except ImportError as e:
        click.echo(f"Error importing workflow module '{name}': {e}")
        click.echo(
            "Ensure the file exists in workflow_registry/ and has no syntax errors."
        )
    except Exception as e:
        click.echo(f"Error running workflow '{name}': {e}")


@main.command()
@click.argument("name_or_id", required=False)
@click.option("--timeline", "-t", is_flag=True, help="Show Gantt chart timeline")
@click.option("--json", "-j", "as_json", is_flag=True, help="Output as JSON")
@click.option("--diff", "-d", is_flag=True, help="Compare two workflow runs")
@click.option("--source", "-s", default=None, help="Source workflow ID for diff")
@click.option("--target", "-T", "target", default=None, help="Target workflow ID to compare against source")
def history(
    name_or_id: str | None,
    timeline: bool,
    as_json: bool,
    diff: bool,
    source: str | None,
    target: str | None,
) -> None:
    """View workflow execution history.

    Shows the execution history for workflows, including steps, timings,
    and child workflows. Can display as text, Gantt chart, or JSON.

    \b
    Examples:
        claiw history                    # List all recent workflows
        claiw history example            # Show latest 'example' run
        claiw history <workflow-id>      # Show specific workflow by ID
        claiw history example --timeline # Show Gantt chart
        claiw history example --json     # Output as JSON
        claiw history example --diff     # Compare two runs interactively
        claiw history example --diff --source <id1> --target <id2>  # Direct diff
    """
    from claiw.dbos_client import get_default_client
    from claiw.display import print_steps, display_timeline, display_diff

    client = get_default_client()

    # Handle diff mode
    if diff:
        if not name_or_id:
            click.echo("Error: Workflow name is required for diff mode.", err=True)
            click.echo("Usage: claiw history <workflow-name> --diff", err=True)
            return

        # Get workflow summaries for selection
        summaries = client.get_workflow_summaries_by_name(name_or_id, limit=10)
        if len(summaries) < 2:
            click.echo(
                f"Error: Need at least 2 workflow runs to compare. Found {len(summaries)}.",
                err=True,
            )
            return

        # If source and target provided, use them directly
        if source and target:
            source_id = source
            target_id = target
        else:
            # Interactive selection using prompt_toolkit
            from claiw.display import select_workflows_for_diff

            result = select_workflows_for_diff(summaries)
            if result is None:
                click.echo("Diff cancelled.")
                return
            source_id, target_id = result

        # Get executions for both workflows
        try:
            source_executions = client.get_workflow_steps_recursive(source_id)
            target_executions = client.get_workflow_steps_recursive(target_id)
        except Exception as e:
            click.echo(f"Error fetching workflow data: {e}", err=True)
            return

        # Display the diff
        display_diff(source_executions, target_executions, source_id, target_id)

        # Print the rerunnable command using Rich for proper formatting
        from rich.console import Console
        console = Console()
        console.print()
        console.print(
            f"[dim]# To rerun this diff without prompts:[/dim]"
        )
        console.print(
            f"[bold]claiw history {name_or_id} --diff --source {source_id} --target {target_id}[/bold]"
        )
        console.print()
        return

    if not name_or_id:
        # List mode: show recent 3 runs per workflow from the registry
        summaries_by_name = client.get_recent_workflows_summary(limit_per_name=3)

        if not summaries_by_name:
            click.echo("No workflow executions found.")
            click.echo("Run a workflow first with: claiw run <workflow-name>")
            return

        click.echo("Recent Workflow Executions:\n")
        for wf_name, summaries in summaries_by_name.items():
            click.echo(f"  {wf_name}:")
            for s in summaries:
                # Format: {workflow_id: xyz, step_count: 5, created_at: timestamp, status: success}
                status_color = {
                    "success": "\033[92m",  # green
                    "error": "\033[91m",  # red
                    "pending": "\033[93m",  # yellow
                }.get(s.status_display, "\033[0m")
                reset = "\033[0m"
                click.echo(
                    f"    {{"
                    f"workflow_id: {s.workflow_id}, "
                    f"step_count: {s.step_count}, "
                    f"created_at: {s.created_at_formatted}, "
                    f"status: {status_color}{s.status_display}{reset}"
                    f"}}"
                )
            click.echo()
        click.echo("Use 'claiw history <name>' for detailed execution history.")
        return

    # Detect if input is a workflow ID (UUID-like with hyphens) or a workflow name
    is_workflow_id = "-" in name_or_id and len(name_or_id) > 20

    try:
        if is_workflow_id:
            executions = client.get_workflow_steps_recursive(name_or_id)
        else:
            executions = client.get_workflow_history(name_or_id)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return
    except Exception as e:
        click.echo(f"Error fetching workflow history: {e}", err=True)
        return

    if not executions:
        click.echo(f"No execution history found for '{name_or_id}'.")
        return

    # Output based on format flags
    if as_json:
        output = [execution.model_dump(mode="json") for execution in executions]
        click.echo(json.dumps(output, indent=2, default=str))
    elif timeline:
        display_timeline(executions)
    else:
        print_steps(executions)


if __name__ == "__main__":
    main()
