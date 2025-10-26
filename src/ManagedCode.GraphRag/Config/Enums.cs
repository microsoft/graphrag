namespace GraphRag.Config;

public enum CacheType
{
    File,
    Memory,
    None,
    Blob,
    CosmosDb
}

public enum InputFileType
{
    Csv,
    Text,
    Json
}

public enum StorageType
{
    File,
    Memory,
    Blob,
    CosmosDb
}

public enum VectorStoreType
{
    LanceDb,
    AzureAiSearch,
    CosmosDb
}

public enum ReportingType
{
    File,
    Blob
}

public enum ModelType
{
    OpenAiEmbedding,
    AzureOpenAiEmbedding,
    Embedding,
    OpenAiChat,
    AzureOpenAiChat,
    Chat,
    MockChat,
    MockEmbedding
}

public enum AuthType
{
    ApiKey,
    AzureManagedIdentity
}

public enum AsyncType
{
    AsyncIo,
    Threaded
}

public enum ChunkStrategyType
{
    Tokens,
    Sentence
}

public enum SearchMethod
{
    Local,
    Global,
    Drift,
    Basic
}

public enum IndexingMethod
{
    Standard,
    Fast,
    StandardUpdate,
    FastUpdate
}

public enum NounPhraseExtractorType
{
    RegexEnglish,
    Syntactic,
    Cfg
}

public enum ModularityMetric
{
    Graph,
    Lcc,
    WeightedComponents
}
