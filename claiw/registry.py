import ast
import click
from pathlib import Path
from typing import List, Optional, Dict, Any

from claiw.db import get_db_connection, init_db

def extract_description(code: str) -> str:
    """Extract the first line of the module docstring."""
    try:
        module = ast.parse(code)
        docstring = ast.get_docstring(module)
        if docstring:
            return docstring.split('\n')[0]
    except Exception:
        pass
    return "No description provided."


def has_claiw_handler(code: str) -> bool:
    """Check if code defines a claiw_handler function.

    Args:
        code: The source code to check.

    Returns:
        True if a claiw_handler function (sync or async) is defined.
    """
    try:
        module = ast.parse(code)
        for node in ast.walk(module):
            if isinstance(node, ast.FunctionDef) and node.name == "claiw_handler":
                return True
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "claiw_handler":
                return True
    except Exception:
        pass
    return False


def extract_workflow_name_from_decorator(code: str) -> str | None:
    """Extract the workflow name from @DBOS.workflow(name='...') decorator.

    Args:
        code: The source code to check.

    Returns:
        The workflow name if found, None otherwise.
    """
    try:
        module = ast.parse(code)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "claiw_handler":
                for decorator in node.decorator_list:
                    # Check for @DBOS.workflow(name='...')
                    if isinstance(decorator, ast.Call):
                        # Check if it's DBOS.workflow
                        if isinstance(decorator.func, ast.Attribute):
                            if decorator.func.attr == "workflow":
                                # Look for name='...' keyword argument
                                for keyword in decorator.keywords:
                                    if keyword.arg == "name":
                                        if isinstance(keyword.value, ast.Constant):
                                            return keyword.value.value
                                        elif isinstance(keyword.value, ast.Str):  # Python < 3.8
                                            return keyword.value.s
    except Exception:
        pass
    return None

def register_workflows(directory: str = "workflow_registry"):
    """Scan the directory and register workflows in the database."""
    # Ensure DB exists
    init_db()
    
    registry_path = Path(directory)
    if not registry_path.exists():
        return

    # First pass: collect all workflow names to check for duplicates
    workflow_names: dict[str, Path] = {}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for file_path in registry_path.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name.startswith("test"):
                continue
                
            name = file_path.stem
            try:
                code_content = file_path.read_text(encoding="utf-8")
                
                # Validate claiw_handler exists
                if not has_claiw_handler(code_content):
                    click.echo(
                        f"Error: Workflow '{name}' missing required 'claiw_handler' function.\n"
                        f"Define your entrypoint as:\n\n"
                        f"    @DBOS.workflow(name='{name}')\n"
                        f"    async def claiw_handler() -> None:\n"
                        f"        ...\n",
                        err=True,
                    )
                    continue
                
                # Validate workflow name in decorator matches filename
                decorator_name = extract_workflow_name_from_decorator(code_content)
                if decorator_name is None:
                    click.echo(
                        f"Error: Workflow '{name}' missing 'name' parameter in @DBOS.workflow decorator.\n"
                        f"Define your entrypoint as:\n\n"
                        f"    @DBOS.workflow(name='{name}')\n"
                        f"    async def claiw_handler() -> None:\n"
                        f"        ...\n",
                        err=True,
                    )
                    continue
                
                if decorator_name != name:
                    click.echo(
                        f"Error: Workflow name mismatch in '{file_path.name}'.\n"
                        f"  Filename suggests: '{name}'\n"
                        f"  Decorator specifies: '{decorator_name}'\n"
                        f"  These must match. Update the decorator to:\n\n"
                        f"    @DBOS.workflow(name='{name}')\n",
                        err=True,
                    )
                    continue
                
                # Check for duplicate workflow names
                if decorator_name in workflow_names:
                    existing_file = workflow_names[decorator_name]
                    click.echo(
                        f"Error: Duplicate workflow name '{decorator_name}' found.\n"
                        f"  First file: {existing_file}\n"
                        f"  Second file: {file_path}\n"
                        f"  Each workflow must have a unique name.\n",
                        err=True,
                    )
                    continue
                
                workflow_names[decorator_name] = file_path
                
                description = extract_description(code_content)
                
                cursor.execute("""
                    INSERT INTO workflows (name, description, code_content, file_path)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        description=excluded.description,
                        code_content=excluded.code_content,
                        file_path=excluded.file_path
                """, (name, description, code_content, str(file_path)))
                
            except Exception as e:
                # Use click.echo for visibility if running from CLI, or just print
                click.echo(f"Warning: Failed to register workflow '{name}' from {file_path}: {e}", err=True)
                # Continue to next file - isolation
                continue
        
        conn.commit()

def list_workflows_from_registry() -> List[Dict[str, Any]]:
    """List all registered workflows."""
    init_db() # Ensure table exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description FROM workflows ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

def get_workflow(name: str) -> Optional[Dict[str, Any]]:
    """Get a workflow by name."""
    init_db() # Ensure table exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
