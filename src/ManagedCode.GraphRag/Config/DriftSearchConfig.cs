namespace GraphRag.Config;

public sealed class DriftSearchConfig
{
    public string? Prompt { get; set; }

    public string? ReducePrompt { get; set; }

    public string ChatModelId { get; set; } = "default_chat_model";

    public string EmbeddingModelId { get; set; } = "default_embedding_model";

    public int DataMaxTokens { get; set; } = 12_000;

    public int? ReduceMaxTokens { get; set; }

    public double ReduceTemperature { get; set; }

    public int? ReduceMaxCompletionTokens { get; set; }

    public int Concurrency { get; set; } = 32;

    public int DriftFollowupCount { get; set; } = 20;

    public int PrimerFolds { get; set; } = 5;

    public int PrimerMaxTokens { get; set; } = 12_000;

    public int Depth { get; set; } = 3;

    public double LocalSearchTextUnitProportion { get; set; } = 0.9;

    public double LocalSearchCommunityProportion { get; set; } = 0.1;

    public int LocalSearchTopKEntities { get; set; } = 10;

    public int LocalSearchTopKRelationships { get; set; } = 10;

    public int LocalSearchMaxDataTokens { get; set; } = 12_000;

    public double LocalSearchTemperature { get; set; }

    public double LocalSearchTopP { get; set; } = 1.0;

    public int LocalSearchSampleCount { get; set; } = 1;

    public int? LocalSearchMaxGeneratedTokens { get; set; }

    public int? LocalSearchMaxCompletionTokens { get; set; }
}
