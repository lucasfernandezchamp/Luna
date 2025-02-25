# KnowledgeDB-ULD

This project provides Luna ! An AI-powered assistant for assessing ULD air worthiness.

## ToDo/Feature List

### Features

- [x] Implement OneRecord update
- [x] Implement picture upload support
- [ ] Implement audio answer with summarization https://github.com/hexgrad/kokoro
- [x] Apply branding to the whole UI
 - https://docs.chainlit.io/customisation/custom-logo-and-favicon
 - https://docs.chainlit.io/backend/config/ui
- [x] Refine Luna personality

### Improvements

- [x] Move API keys to configuration file
- [x] Update documentation and usage examples
- [x] Add some starters to improve user guidance https://docs.chainlit.io/concepts/starters
- [x] Improve error handling for external API calls
- [x] Refactor code for better modularity
- [ ] Add unit tests for all modules
- [ ] Add integration tests for complete user flows
- [x] Implement caching for llm calls to improve performance

## Environment Setup
Tested with Python 3.11.

Install dependencies:
```
pip install -r requirements.txt
```

## Running Instructions

Create .env file
```
AZURE_OPENAI_ENDPOINT="https://xxxxx.openai.azure.com"
AZURE_OPENAI_DEPLOYMENT="gpt-4o"
AZURE_OPENAI_VERSION="2024-08-01-preview"
AZURE_OPENAI_API_KEY="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

AZURE_COGNITIVE_ENDPOINT="https://xxxxxxx.cognitiveservices.azure.com"
AZURE_COGNITIVE_VERSION="2024-11-15"

CHAINLIT_AUTH_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxx"

KEYCLOCK_ENDPOINT="http://xxxxxxx.cloudapp.azure.com:8990"
KEYCLOCK_TOKEN="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

ONERECORD_BASE_URL = "http://xxxxxxxxxxxxxxxxxxxxxxxx.cloudapp.azure.com:8080"
ONERECORD_GET_PATH = "/logistics-objects/"

GATEKEEPER_ENDPOINT = "http://127.0.0.1:8040/"
VP_SECRET = "xxxxxxxxxxxxxx"
```

For Development
```
chainlit run app.py -w
```

For Development with https (Quick and Dirty)
```
chainlit run app.py -h --ssl-cert ./certs/certificate.crt --ssl-key ./certs/private.key --port 443 --host 0.0.0.0
```
