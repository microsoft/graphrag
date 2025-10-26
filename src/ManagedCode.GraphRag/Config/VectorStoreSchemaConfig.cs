namespace GraphRag.Config;

public sealed class VectorStoreSchemaConfig
{
    public string IdField { get; set; } = "id";

    public string VectorField { get; set; } = "vector";

    public string TextField { get; set; } = "text";

    public string AttributesField { get; set; } = "attributes";

    public int VectorSize { get; set; } = 1536;

    public string? IndexName { get; set; }
        = null;
}
