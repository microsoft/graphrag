namespace GraphRag.Constants;

public static class TokenizerDefaults
{
    public const string DefaultModel = "gpt-4";
    public const string DefaultEncoding = "o200k_base";

    public static readonly string[] PreferredModels =
    [
        "gpt-4",
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-4-turbo-preview"
    ];

    public static readonly string[] PreferredEncodings =
    [
        "o200k_base",
        "cl100k_base"
    ];
}
