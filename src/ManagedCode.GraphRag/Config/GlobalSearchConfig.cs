namespace GraphRag.Config;

public sealed class GlobalSearchConfig
{
    public string? MapPrompt { get; set; }

    public string? ReducePrompt { get; set; }

    public string? KnowledgePrompt { get; set; }

    public string ChatModelId { get; set; } = "default_chat_model";

    public int MaxContextTokens { get; set; } = 12_000;

    public int DataMaxTokens { get; set; } = 12_000;

    public int MapMaxLength { get; set; } = 1_000;

    public int ReduceMaxLength { get; set; } = 2_000;

    public int DynamicSearchThreshold { get; set; } = 1;

    public bool DynamicSearchKeepParent { get; set; }

    public int DynamicSearchRepeats { get; set; } = 1;

    public bool DynamicSearchUseSummary { get; set; }

    public int DynamicSearchMaxLevel { get; set; } = 2;
}
