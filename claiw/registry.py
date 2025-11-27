import os
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

def register_workflows(directory: str = "workflow_registry"):
    """Scan the directory and register workflows in the database."""
    # Ensure DB exists
    init_db()
    
    registry_path = Path(directory)
    if not registry_path.exists():
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        for file_path in registry_path.glob("*.py"):
            if file_path.name.startswith("__") or file_path.name.startswith("test"):
                continue
                
            name = file_path.stem
            try:
                code_content = file_path.read_text(encoding="utf-8")
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
