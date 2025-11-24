import click
import asyncio
import inspect
import importlib
import sys
import os
from dbos import DBOS
from claiw.registry import register_workflows, list_workflows, get_workflow

@click.group()
@click.version_option()
def main():
    """claiw: A supercharged agent workflow CLI."""
    pass

@main.command()
@click.argument("name", required=False)
def run(name):
    """Run a registered workflow or list available ones."""
    # Always auto-register on run
    register_workflows()
    
    if not name:
        # List workflows
        workflows = list_workflows()
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
        # Initialize DBOS before importing/running
        DBOS.launch()

        # Import the module dynamically using importlib
        # This relies on workflow_registry being a python package or in path
        module_name = f"workflow_registry.{name}"
        # Force reload in case DBOS instrumentation needs to re-apply or cache is stale
        if module_name in sys.modules:
            module = importlib.reload(sys.modules[module_name])
        else:
            module = importlib.import_module(module_name)
        
        # Look for main()
        if hasattr(module, "main") and callable(module.main):
            func = module.main
            if inspect.iscoroutinefunction(func):
                # Wrap in DBOS.start_workflow if it's a DBOS workflow but being called directly
                # However, DBOS.workflow decorated functions should handle this automatically if DBOS is launched.
                # The issue might be that we are running it inside asyncio.run() but DBOS might need to own the loop or context.
                
                # If main is a DBOS workflow, we just await it.
                asyncio.run(func())
            else:
                func()
        else:
            click.echo(f"Warning: No 'main()' function found in {name} (checked module {module_name}).")
            
    except ImportError as e:
         click.echo(f"Error importing workflow module '{name}': {e}")
         click.echo("Ensure the file exists in workflow_registry/ and has no syntax errors.")
    except Exception as e:
        click.echo(f"Error running workflow '{name}': {e}")

if __name__ == "__main__":
    main()
