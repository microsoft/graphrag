namespace GraphRag.Config;

public sealed class PromptTuningConfig
{
    public ManualPromptTuningConfig Manual { get; set; } = new();

    public AutoPromptTuningConfig Auto { get; set; } = new();
}

public sealed class ManualPromptTuningConfig
{
    public bool Enabled { get; set; }

    public string? Directory { get; set; }
}

public sealed class AutoPromptTuningConfig
{
    public bool Enabled { get; set; }

    public string? Directory { get; set; }

    public string? Strategy { get; set; }
}
