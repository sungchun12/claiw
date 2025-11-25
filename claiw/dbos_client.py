from dbos import DBOSClient  
from registry import list_workflows as list_workflows_from_registry

dbos_client = DBOSClient("sqlite:///dbostest.sqlite")  

workflows_from_registry = list_workflows_from_registry() # TODO: need to fix how name in DBOS state is different from claiw registry

latest_dbos_workflows_by_name = {}
for workflow in workflows_from_registry:
    dbos_workflows = dbos_client.list_workflows(name=workflow['name'], limit=1, sort_desc=True)
    if dbos_workflows:
        latest_dbos_workflows_by_name[workflow['name']] = dbos_workflows[0].workflow_id
    else:
        print(f"No DBOS workflow found for {workflow['name']}")

print(latest_dbos_workflows_by_name)