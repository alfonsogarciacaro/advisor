
import os
import uvicorn

if __name__ == "__main__":
    # Set environment variables for testing
    os.environ["GCP_PROJECT_ID"] = "test-project"
    os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"
    
    # Ensure no external API keys are set so we use internal mocks
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
    if "OPENAI_API_KEY" in os.environ:
        del os.environ["OPENAI_API_KEY"]
    if "ALPHA_VANTAGE_API_KEY" in os.environ:
        del os.environ["ALPHA_VANTAGE_API_KEY"]

    print("Starting backend for integration tests with mocked services...")
    print(f"GCP_PROJECT_ID: {os.environ.get('GCP_PROJECT_ID')}")
    print(f"FIRESTORE_EMULATOR_HOST: {os.environ.get('FIRESTORE_EMULATOR_HOST')}")
    
    # Run the server
    port = int(os.environ.get("PORT", "8000"))
    print(f"Starting server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
