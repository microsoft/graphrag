"""
Ollama大模型
"""

from langchain_core.embeddings.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel, BaseLanguageModel
from langchain_core.messages import BaseMessage
from langchain_ollama import ChatOllama, OllamaEmbeddings, OllamaLLM

INSTRUCT_MODEL = "llama3.1:8b"
CHAT_MODEL = INSTRUCT_MODEL
EMBEDDINGS_MODEL = "quentinz/bge-large-zh-v1.5:latest"
_llm, _chat_llm, _embeddings = None, None, None


def create_llm(**kwargs) -> BaseLanguageModel[str] | BaseLanguageModel[BaseMessage]:
    """创建 OllamaLLM，可以用来替换 OpenAI"""
    global _llm
    if len(kwargs) == 0:
        if _llm is None:
            _llm = OllamaLLM(model=INSTRUCT_MODEL)
        return _llm
    options = {"model": INSTRUCT_MODEL, **kwargs}
    return OllamaLLM(**options)


def create_chat_llm(**kwargs) -> BaseChatModel:
    """创建 ChatOllama，可以用来替换 ChatOpenAI"""
    global _chat_llm
    if len(kwargs) == 0:
        if _chat_llm is None:
            _chat_llm = ChatOllama(model=CHAT_MODEL)
        return _chat_llm
    options = {"model": CHAT_MODEL, **kwargs}
    return ChatOllama(**options)


def create_embeddings(**kwargs) -> Embeddings:
    """创建 OllamaEmbeddings，可以用来替换 OpenAIEmbeddings"""
    global _embeddings
    if len(kwargs) == 0:
        if _embeddings is None:
            _embeddings = OllamaEmbeddings(model=EMBEDDINGS_MODEL)
        return _embeddings
    options = {"model": EMBEDDINGS_MODEL, **kwargs}
    return OllamaEmbeddings(**options)


creators = (create_llm, create_chat_llm, create_embeddings)
