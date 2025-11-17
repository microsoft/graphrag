namespace GraphRag.Config;

public enum InputFileType
{
    Csv,
    Text,
    Json
}

public enum CacheType
{
    File,
    Memory,
    None,
    Blob,
    CosmosDb
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

public enum ChunkStrategyType
{
    Tokens,
    Sentence
}

public enum AsyncType
{
    Threaded,
    AsyncIO
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

public enum CommunityDetectionAlgorithm
{
    FastLabelPropagation,
    ConnectedComponents
}
