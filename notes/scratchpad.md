# scratchpad

## 11/25/25

I'm trying to auto-list workflow id and steps. If I breakdown the problem it looks like this.

This is the experience I want. It's essentially print debugging without the manual tedium.

```shell
$ claiw history
Historical Workflow Latest Runs:
- example: {worflow_id: xyz, step_count: 5, status: success}
- another: {worflow_id: abc, step_count: 2, status: failure}
- random: None

$ claiw history example --recent
worflow_id: xyz
Steps:
- 


```

DBOS data model notes

https://deepwiki.com/search/how-to-get-latest-workflow-id_fbaf2806-2ef3-4f6a-87a0-5f1ed86b2fd8?mode=fast

`workflow_status` table is important to get the main workflow fields
- `workflow_uuid`319c1e24-2bf9-4d5f-8f34-c260d0b08c42
- `status` SUCCESS
- `name` main (name of the function that it decorates)
- `created_at` 1764098785249
- `updated_at` 1764098794000
- `application_version` 26798847cd047a312f4942bea875137d
- `output` gAROLg== (automatically deserialized when retrieved)


main workflow uuid: 319c1e24-2bf9-4d5f-8f34-c260d0b08c42
childe workflow uuid: 319c1e24-2bf9-4d5f-8f34-c260d0b08c42-1

`operation_outputs` table is important to get the steps
`function_id` 3
`function_name` get_mood
`output` gASVFwAAAAAAAACME1lvdSBhcmUgaGFwcHkgdG9kYXmULg== (automatically deserialized when retrieved)
`started_at_epoch_ms` 1764098794728
`completed_at_epoch_ms` 1764098794728


Need to use `DBOSClient` given I'm building a CLI tool