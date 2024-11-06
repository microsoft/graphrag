from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from graphrag.config import GraphRagConfig, LLMType
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType


def get_llm(config: GraphRagConfig) -> ChatOpenAI:
    # """Get the LLM client."""
    # is_azure_client = (
    #     config.llm.type == LLMType.AzureOpenAIChat
    #     or config.llm.type == LLMType.AzureOpenAI
    # )
    # debug_llm_key = config.llm.api_key or ""
    # llm_debug_info = {
    #     **config.llm.model_dump(),
    #     "api_key": f"REDACTED,len={len(debug_llm_key)}",
    # }
    # audience = (
    #     config.llm.audience
    #     if config.llm.audience
    #     else "https://cognitiveservices.azure.com/.default"
    # )
    # print(f"creating llm client with {llm_debug_info}")  # noqa T201
    # return ChatOpenAI(
    #     api_key=config.llm.api_key,
    #     azure_ad_token_provider=(
    #         get_bearer_token_provider(DefaultAzureCredential(), audience)
    #         if is_azure_client and not config.llm.api_key
    #         else None
    #     ),
    #     api_base=config.llm.api_base,
    #     organization=config.llm.organization,
    #     model=config.llm.model,
    #     api_type=OpenaiApiType.AzureOpenAI if is_azure_client else OpenaiApiType.OpenAI,
    #     deployment_name=config.llm.deployment_name,
    #     api_version=config.llm.api_version,
    #     max_retries=config.llm.max_retries,
    #     request_timeout=config.llm.request_timeout,
    # )
    import os

    api_key = os.getenv("AP_OPENAI_API_KEY")
    llm_model = llm_deployment_name = config.llm.model

    llm_init_params = {
        "api_key": api_key,
        "model": llm_model,
        "deployment_name": llm_deployment_name,
        "api_type": OpenaiApiType.OpenAI,
        "max_retries": 50,
    }

    llm_gen_params = {
        "max_tokens": 1000,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    llm = ChatOpenAI(**llm_init_params)

    return llm
