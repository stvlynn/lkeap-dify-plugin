# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Dify plugin that integrates Tencent LKEAP International Station into the Dify platform. It provides access to:
- **LLM models**: DeepSeek series (deepseek-r1, deepseek-r1-0528, deepseek-v3, deepseek-v3-0324, deepseek-v3.1-terminus)
- **Text embedding**: lke-text-embedding-v1
- **Reranking**: lke-reranker-base

**Note**: LKEAP provides two different API systems, both using the same Tencent Cloud credentials:
- **OpenAI-compatible API** for LLM models (base_url: https://api.lkeap.tencentcloud.com/v1, uses secret_key as API key)
- **Tencent Cloud SDK API** for embedding and reranking models (uses secret_id + secret_key)

## Development Commands

Since this is a Dify plugin, there's no traditional build/test infrastructure. The plugin runs within the Dify platform runtime.

**Local Development Setup:**
```bash
# Create .env file with remote install credentials
cp .env.example .env
# Edit .env with your REMOTE_INSTALL_HOST, REMOTE_INSTALL_PORT, and REMOTE_INSTALL_KEY

# Package the plugin (requires dify-plugin CLI tool)
dify-plugin package . -o lkeap-<version>.difypkg
```

**Publishing:**
- The GitHub Actions workflow (.github/workflows/plugin-publish.yml) automatically packages and creates PRs to the dify-plugins repository when pushing to main
- Workflow extracts plugin name, version, and author from manifest.yaml

## Architecture

**Plugin Structure:**
```
main.py                     # Entry point - creates Plugin instance with 120s timeout
provider/
  lkeap.py                  # LkeapModelProvider - credential validation
  lkeap.yaml               # Provider schema (credentials, supported models)
models/
  llm/llm.py               # LargeLanguageModel implementation (OpenAI-compatible)
  text_embedding/text_embedding.py  # TextEmbeddingModel implementation (Tencent SDK)
  rerank/rerank.py         # RerankModel implementation (Tencent SDK)
  */[model].yaml           # Individual model configurations
  */_position.yaml         # Model ordering for UI
```

**Key Design Patterns:**

1. **Dual API System**:
   - **LLM Models** (models/llm/llm.py): Uses OpenAI Python SDK with OpenAI-compatible API
     - Base URL: `https://api.lkeap.tencentcloud.com/v1`
     - Authentication: Uses `secret_key` as OpenAI API key
     - Supports streaming, function calling (V3 models only), reasoning content (R1 models)
   - **Embedding/Rerank Models**: Uses Tencent Cloud SDK
     - Endpoint: `lkeap.intl.tencentcloudapi.com` (international station)
     - Client setup: `lkeap_client.LkeapClient(credentials, "ap-jakarta", profile)`
     - Credentials: Both `secret_id` and `secret_key` from Tencent Cloud CAM

2. **Model Configuration** (YAML files):
   - Each model has its own YAML defining: label, model_type, features, context_size, parameter_rules, pricing
   - `_position.yaml` files control model ordering in Dify UI
   - Provider YAML links Python implementations via `extra.python.model_sources`

3. **Credential Validation**:
   - Provider validation (provider/lkeap.py:19-29): Uses unified Tencent Cloud credentials
     - Validates with LLM model (deepseek-v3) using OpenAI-compatible API
     - Same `secret_id` and `secret_key` work for all model types
   - Individual model validation: Each model type implements its own validate_credentials()
   - LLM validation uses OpenAI chat completions API (secret_key as API key)
   - Text embedding validation uses GetEmbedding API (secret_id + secret_key)
   - Rerank validation uses RunRerank API (secret_id + secret_key)

4. **LLM-Specific Features**:
   - **Reasoning Content** (R1 models): Special handling for `reasoning_content` field, wrapped in `<think></think>` tags
   - **Function Calling** (V3 models only): Supports tool/function calling via OpenAI tools format
   - **Streaming**: Full streaming support with proper chunk handling for both regular and reasoning content
   - **Model-Specific Parameters**:
     - R1 models: temperature, top_p, max_tokens (no function calling, no JSON output)
     - V3 models: temperature, top_p, max_tokens + function calling support
     - V3.1-Terminus: adds presence_penalty, frequency_penalty + JSON output support

## Important Implementation Notes

- **MAX_REQUEST_TIMEOUT**: Set to 120 seconds in main.py to accommodate longer model inference times
- **Dependencies**:
  - `openai>=1.0.0` for LLM models (OpenAI-compatible API)
  - `tencentcloud-sdk-python-lkeap~=3.0.1340` for embedding/rerank models
- **Error Mapping**:
  - LLM models map `OpenAIError` to Dify's `InvokeError`
  - Embedding/Rerank models map `TencentCloudSDKException` to Dify's `InvokeError`
- **Token Counting**: Uses GPT-2 tokenizer (`_get_num_tokens_by_gpt2`) for estimation
- **Unified Credential System**: Uses Tencent Cloud CAM credentials for all models
  - `secret_id`: Tencent Cloud Secret ID
  - `secret_key`: Tencent Cloud Secret Key (also used as API key for LLM OpenAI-compatible API)
- **LLM API Limitations** (from official docs):
  - R1 models: No function calling, no JSON output, no system prompt recommended
  - V3 models: No JSON output, no dialogue prefix continuation
  - V3.1-Terminus: Supports JSON output, no function calling, no dialogue prefix continuation
  - Streaming recommended for R1 models due to long reasoning process

## Adding New Models

1. Create model YAML in appropriate models/ subdirectory (llm/, text_embedding/, or rerank/)
2. Add model name to corresponding `_position.yaml` file
3. Update manifest.yaml version
4. For LLM models: No code changes needed if using OpenAI-compatible API
5. For embedding/rerank models: No code changes needed unless API parameters differ

## Credentials

Users need to configure Tencent Cloud CAM credentials to access all models:

- **Secret ID**: Tencent Cloud API Secret ID
- **Secret Key**: Tencent Cloud API Secret Key
- Obtain from: https://console.cloud.tencent.com/cam/capi

**Important Notes**:
- The same credentials work for all model types (LLM, embedding, rerank)
- For LLM models: `secret_key` is used as the API key for OpenAI-compatible API
- For Embedding/Rerank models: Both `secret_id` and `secret_key` are used with Tencent Cloud SDK
- Users only need to configure credentials once to access all capabilities
