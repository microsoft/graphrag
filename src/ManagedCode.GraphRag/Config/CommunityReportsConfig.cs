using System.Collections.Generic;

namespace GraphRag.Config;

public sealed class CommunityReportsConfig
{
    public string ModelId { get; set; } = "default_chat_model";

    public string? GraphPrompt { get; set; }
        = "prompts/community_graph.txt";

    public string? TextPrompt { get; set; }
        = "prompts/community_text.txt";

    public int MaxLength { get; set; } = 2000;

    public int MaxInputLength { get; set; } = 8000;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new();
}
