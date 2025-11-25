from dbos import DBOSClient  
from registry import list_workflows as list_workflows_from_registry

dbos_client = DBOSClient("sqlite:///dbostest.sqlite")

def get_workflow_step_latest_history(name: str) -> list[dict]:
    latest_workflow_id = get_latest_dbos_workflow_id_by_name(name)
    steps = get_all_steps_recursive(latest_workflow_id)
    print(steps)
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


def get_all_steps_recursive(workflow_id: str, visited=None):  
    """Recursively get all steps and child workflows"""  
    if visited is None:  
        visited = set()
      
    if workflow_id in visited:  
        return []  
      
    visited.add(workflow_id)  
      
    # Get steps for this workflow  
    steps = dbos_client.list_workflow_steps(workflow_id)  
    all_steps = [(workflow_id, steps)]  
      
    # Recursively get steps for child workflows  
    for step in steps:  
        child_id = step.get("child_workflow_id")  
        if child_id:  
            all_steps.extend(get_all_steps_recursive(child_id, visited))  
      
    return all_steps 

def print_all_steps_recursive(workflow_ids: dict[str, str]) -> None:
    """Print all steps and child workflows for all workflows in the registry."""
    for name, wf_id in workflow_ids.items():  
        print(f"\n=== Workflow: {name} ({wf_id}) ===")  
        all_steps = get_all_steps_recursive(wf_id)  
        for workflow_id, steps in all_steps:  
            print(f"\nWorkflow ID: {workflow_id}")  
            for step in steps:  
                print(f"  Step {step['function_id']}: {step['function_name']}")  
                if step['child_workflow_id']:  
                    print(f"    -> Child workflow: {step['child_workflow_id']}")

get_workflow_step_latest_history('example')