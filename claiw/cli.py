import click
import asyncio
import inspect
import importlib
import sys
import os
from pydantic_ai import Agent
from pydantic_ai.durable_exec.dbos import DBOSAgent
from claiw.registry import register_workflows, list_workflows, get_workflow
from claiw.dbos_config import configure_dbos, launch_dbos

@click.group()
@click.version_option()
def main():
    """claiw: A supercharged agent workflow CLI."""
    pass

@main.command()
@click.argument("name", required=False)
@click.argument("input_text", required=False)
def run(name, input_text):
    """Run a registered workflow.
    
    NAME: The name of the workflow to run.
    INPUT_TEXT: Optional input text to pass to the workflow's entrypoint.
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

        # 5. Find the target to run
        target = None
        
        # Priority 1: Explicit 'entrypoint'
        if hasattr(module, "entrypoint"):
            target = module.entrypoint

        # Priority 2: 'main' function (MOVED UP: User explicit request)
        elif hasattr(module, "main") and callable(module.main):
             target = module.main

        # Priority 3: Auto-discovery of DBOSAgent/Agent (Fallback if no main/entrypoint)
        else:
             for var_name, val in vars(module).items():
                if isinstance(val, (DBOSAgent, Agent)):
                    target = val
                    break
        
        # Execute the target
        if target:
            # Case A: It's an object with a .run() method (e.g., Pydantic/DBOS Agent)
            if hasattr(target, "run"):
                prompt = input_text or "Default prompt" 
                if inspect.iscoroutinefunction(target.run):
                    result = asyncio.run(target.run(prompt))
                else:
                    result = target.run(prompt)
                
                # Print result - PydanticAI results have .data or .output
                if hasattr(result, "data"):
                    print(result.data)
                elif hasattr(result, "output"):
                    print(result.output)
                else:
                    print(result)
                    
            # Case B: It's a callable (function)
            elif callable(target):
                # If it's main(), we might want to pass args if available, or call no-arg if input_text is None
                # BUT, if input_text IS provided, we should probably try to pass it.
                if inspect.iscoroutinefunction(target):
                    if input_text is not None:
                         try:
                             asyncio.run(target(input_text))
                         except TypeError:
                             # Fallback: maybe main() takes no args
                             asyncio.run(target())
                    else:
                         try:
                             asyncio.run(target())
                         except TypeError:
                             click.echo("Error: 'main' function expects an argument but none provided.")
                else:
                    if input_text is not None:
                         try:
                            target(input_text)
                         except TypeError:
                            target()
                    else:
                         try:
                             target()
                         except TypeError:
                             click.echo("Error: 'main' function expects an argument but none provided.")
        else:
            click.echo(f"Warning: No Agent, DBOSAgent, 'entrypoint' variable or 'main()' function found in {name}.")
            
    except ImportError as e:
         click.echo(f"Error importing workflow module '{name}': {e}")
         click.echo("Ensure the file exists in workflow_registry/ and has no syntax errors.")
    except Exception as e:
        click.echo(f"Error running workflow '{name}': {e}")

if __name__ == "__main__":
    main()
