import click
import asyncio
import inspect
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
    
    code_content = workflow['code_content']
    namespace = {}
    
    try:
        # Execute the module body
        exec(code_content, namespace)
        
        # Look for main()
        if "main" in namespace and callable(namespace["main"]):
            func = namespace["main"]
            if inspect.iscoroutinefunction(func):
                asyncio.run(func())
            else:
                func()
        else:
            click.echo(f"Warning: No 'main()' function found in {name}. Module executed, but entry point might be missing.")
            
    except Exception as e:
        click.echo(f"Error running workflow '{name}': {e}")

if __name__ == "__main__":
    main()
