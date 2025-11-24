# brainstorm

I was inspired by the renaissance we have in CLIs with the advent of claude code and equivalents. The collective standard and imagination for CLI experiences is way higher and deeper and broader. I want to bolster that momentum with this tool. 

Pronounced "claw": like playing the claw machine at an arcade and winning on the first try

Problems to solve:
- Mistrust in running agent workflows that need to go through many complicated steps
- Too much babysitting agents and guiding it in the right direction when I already know what I want
- The gradient of use cases that require something more than a well-written `agents.md`
- Lack of clarity at a glance for what a workflow is doing at any given step
- Debugging is messy and stressful
- Lack of robust testing

How to solve:
- A registry of agentic workflows with robust testing: unit, integration, evals
- UX that makes it feel like a delightful video game

UX:
- Easy to use from any machine with a single command with zero setup: `uvx claiw run <name-of-agent-workflow>`
- beautiful illustrations for progress and steps complete and debugging
- Rerun from a specific step whether success or failure
- Ability to preview similar to a gif preview for a new moveset in a video game
- First time running should make the user instantly think, "This feels so good to use and makes so much sense!"
- Easy to switch llm providers
- Illustrate the graph of steps with elegant ASCII text art

Considerations:
- Look at charm.sh, claude-code, crush, and warp for inspiration
- Use click to leverage its shared state mechanism and deeper control on terminal output
- Ability to run evals upfront before using it
- Make it easy to setup secrets/env vars like API keys
- Store state in sqlite(maybe postgres) and duckdb
- `YAML` configs
- Make workflows stateful by default
- How to train and evolve agents like Pokemon
- Ability to share agents with private/encrypted history/state. Like selling a beefed up account on WoW.
- NOT a TUI trying to replicate the browser experience in the terminal. A pure cli with great outputs.
- Should I fork clai or build from scratch inspired by its design? Leaning towards from scratch.
- Apache 2.0 license
- Heavily inspired by my experience working at dbt Labs, Datafold, and Tobiko

Potential dependencies:
- click
- pydantic-ai
- DBOS