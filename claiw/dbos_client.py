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
    print_steps(steps)
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

get_workflow_step_latest_history('example')