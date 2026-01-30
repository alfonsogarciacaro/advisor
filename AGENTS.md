# Agent Rules

## Python Dependencies and Execution
- **ALWAYS** use `uv` for Python dependency management and execution from `backend/` directory.
- Use `uv add <package>` to add dependencies.
- Use `uv run <script>` or `uv run pytest` for Python execution.

## Documentation
- For project context, see [docs/tech/AGENT_CONTEXT.md](docs/tech/AGENT_CONTEXT.md).
- For technical details, check the `docs/tech/` directory.
- For user guides, check the `docs/user/` directory.

## Testing
When adding a new feature, **ALWAYS** add tests for it and make sure they pass.
We prefer integration tests, don't mock any internal service and assume Firestore emulator is running (warn user if that's not the case).
Only 3rd party providers will be mocked, but this is handled automatically in the code by env vars (e.g. if no api key is set for news provider, mock is used). Check `backend/.env.test` for env vars for testing.

- For backend features, add pytest tests in `backend/tests/` directory.
> If necessary, you can create manual test scripts in `backend/tests/manual/` directory, but if possible, convert them to pytest later.

- If a new endpoint is added, add a test for it in `backend/tests/test_endpoints.py`.

- If a new fronted feature is added, first add a story to `docs/USER_STORIES.md` and later add tests for it in `frontend/tests/`.
> Use good practices (e.g. aria labels) to locate elements instead of brittle style classes. Make the changes necessary in the code to make tests work, but if some require too much contorsion, skip them and leave a comment for future revisit.
> Note frontend tests are actually integration tests using playwright and a test backend server, which will usually be running in the background (warn user if that's not the case, don't start it by yourself as it can mess with other agents), see `backend/start_test_server.py`. Run frontend tests with `npx playwright test` (plus arg to filter by file) until all test run. 

