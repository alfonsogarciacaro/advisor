# Agent Rules

## Python Dependencies and Execution
- **ALWAYS** use `uv` for Python dependency management and execution from `backend/` directory.
- Use `uv add <package>` to add dependencies.
- Use `scripts/install_deps.sh` to install all dependencies (backend + frontend).

## Documentation
- For project context, see [docs/tech/AGENT_CONTEXT.md](docs/tech/AGENT_CONTEXT.md).
- For technical details, check the `docs/tech/` directory.
- For user guides, check the `docs/user/` directory.

## Testing
When adding a new feature, **ALWAYS** add tests for it and make sure they pass.
We prefer integration tests, don't mock any internal service and assume Firestore emulator is running (warn user if that's not the case).
Only 3rd party providers will be mocked, but this is handled automatically in the code by env vars (e.g. if no api key is set for news provider, mock is used). Check `backend/.env.test` for env vars for testing.

- **Backend Tests**: Run with `bash scripts/test_backend.sh`. Add pytest tests in `backend/tests/` directory.
  - If a new endpoint is added, add a test for it in `backend/tests/test_endpoints.py`.

- **Frontend Tests**: Run with `bash scripts/test_frontend.sh`. This script automatically manages the test server and data clearing. Add tests in `frontend/tests/`.
  - If a new fronted feature is added, first add a story to `docs/USER_STORIES.md` and later add tests for it.

> If necessary, you can create manual test scripts in `backend/tests/manual/` directory, but if possible, convert them to pytest later.
> Use good practices (e.g. aria labels) to locate elements instead of brittle style classes.
 

