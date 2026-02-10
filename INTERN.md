# AI-Assisted Configuration Tool

## Design Decisions
- **Architecture**: Microservices (Schema, Values, Bot) were chosen to separate concerns. Each service scales independently.
- **LLM**: Ollama with Llama3 was selected for local execution and strong JSON handling capabilities.
- **Communication**: Services communicate via HTTP REST APIs.
- **Validation**: `jsonschema` ensures LLM outputs are valid against the strict application definitions.

## Implementation Details
- **Schema Service**: Serves static schema files from the data directory.
- **Values Service**: Serves current configuration states.
- **Bot Service**: Orchestrates the process. It uses `extract_app_name_jk` to parse intent and `process_config_update` to generate JSONs via Ollama.

## Request Flow
1. User POSTs to `/message`.
2. Bot identifies target app (e.g., "tournament").
3. Bot fetches Schema and Values from respective services.
4. Bot sends context to LLM to apply changes.
5. Bot validates new JSON against Schema.
6. Returns result to user.
