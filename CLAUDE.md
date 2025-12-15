# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Dify plugin that integrates Tencent LKEAP International Station into the Dify platform. It provides access to:
- **Text embedding**: lke-text-embedding-v1
- **Reranking**: lke-reranker-base

**Note**: LLM models are NOT available on LKEAP International Station.

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
  text_embedding/text_embedding.py  # TextEmbeddingModel implementation
  rerank/rerank.py         # RerankModel implementation
  */[model].yaml           # Individual model configurations
  */_position.yaml         # Model ordering for UI
```

**Key Design Patterns:**

1. **Tencent Cloud SDK Integration**: All model implementations use `tencentcloud-sdk-python-lkeap` to communicate with LKEAP APIs
   - Endpoint: `lkeap.intl.tencentcloudapi.com` (international station)
   - Client setup: `lkeap_client.LkeapClient(credentials, "ap-jakarta", profile)`
   - Credentials: `secret_id` and `secret_key` from Tencent Cloud CAM

2. **Model Configuration** (YAML files):
   - Each model has its own YAML defining: label, model_type, features, context_size, parameter_rules, pricing
   - `_position.yaml` files control model ordering in Dify UI
   - Provider YAML links Python implementations via `extra.python.model_sources`

3. **Credential Validation**:
   - Provider validation (provider/lkeap.py:20): Tests with lke-reranker-base model
   - Individual model validation: Each model type implements its own validate_credentials()
   - Text embedding validation uses GetEmbedding API
   - Rerank validation uses RunRerank API

## Important Implementation Notes

- **MAX_REQUEST_TIMEOUT**: Set to 120 seconds in main.py to accommodate longer model inference times
- **Error Mapping**: All models map `TencentCloudSDKException` to Dify's `InvokeError`
- **Token Counting**: Uses GPT-2 tokenizer (`_get_num_tokens_by_gpt2`) for estimation since LKEAP doesn't provide a native tokenizer
- **International Station**: Uses `lkeap.intl.tencentcloudapi.com` endpoint with "ap-jakarta" region for all API calls
- **No LLM Support**: LKEAP International Station only provides text embedding and reranking services

## Adding New Models

1. Create model YAML in appropriate models/ subdirectory (text_embedding/ or rerank/)
2. Add model name to corresponding `_position.yaml` file
3. Update manifest.yaml version
4. No code changes needed unless the model requires different API parameters

## Credentials

Required from users:
- **Secret ID**: Tencent Cloud API credential
- **Secret Key**: Tencent Cloud API credential
- Obtain from: https://console.cloud.tencent.com/cam/capi
