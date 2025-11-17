namespace GraphRag.Config;

public sealed class ClaimExtractionConfig
{
    private const string DefaultDescription = "Any claims or facts that could be relevant to information discovery.";

    public bool Enabled { get; set; }

    public string ModelId { get; set; } = "default_chat_model";

    public string? Prompt { get; set; }

    public string Description { get; set; } = DefaultDescription;

    public int MaxGleanings { get; set; } = 1;

    public Dictionary<string, object?>? Strategy { get; set; }
        = new(StringComparer.OrdinalIgnoreCase);

    public Dictionary<string, object?> GetResolvedStrategy(string? rootDirectory = null)
    {
        if (Strategy is { Count: > 0 })
        {
            return new Dictionary<string, object?>(Strategy, StringComparer.OrdinalIgnoreCase);
        }

        string? promptPayload = null;
        if (!string.IsNullOrWhiteSpace(Prompt))
        {
            var baseDir = string.IsNullOrWhiteSpace(rootDirectory)
                ? Directory.GetCurrentDirectory()
                : rootDirectory!;
            var fullPath = Path.IsPathRooted(Prompt!)
                ? Prompt!
                : Path.Combine(baseDir, Prompt!);

            if (!File.Exists(fullPath))
            {
                throw new FileNotFoundException($"Claim extraction prompt '{fullPath}' could not be found.", fullPath);
            }

            promptPayload = File.ReadAllText(fullPath);
        }

        return new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
        {
            ["model_id"] = ModelId,
            ["extraction_prompt"] = promptPayload,
            ["claim_description"] = Description,
            ["max_gleanings"] = MaxGleanings
        };
    }
}
