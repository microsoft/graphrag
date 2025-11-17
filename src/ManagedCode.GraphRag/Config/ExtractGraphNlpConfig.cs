namespace GraphRag.Config;

public sealed class ExtractGraphNlpConfig
{
    public bool NormalizeEdgeWeights { get; set; } = true;

    public TextAnalyzerConfig TextAnalyzer { get; set; } = new();

    public int ConcurrentRequests { get; set; } = 25;

    public AsyncType AsyncMode { get; set; } = AsyncType.Threaded;
}

public sealed class TextAnalyzerConfig
{
    private static readonly string[] DefaultStopWords =
    {
        "stuff",
        "thing",
        "things",
        "bunch",
        "bit",
        "bits",
        "people",
        "person",
        "okay",
        "hey",
        "hi",
        "hello",
        "laughter",
        "oh"
    };

    public NounPhraseExtractorType ExtractorType { get; set; } = NounPhraseExtractorType.RegexEnglish;

    public string ModelName { get; set; } = "en_core_web_md";

    public int MaxWordLength { get; set; } = 15;

    public string WordDelimiter { get; set; } = " ";

    public bool IncludeNamedEntities { get; set; } = true;

    public List<string> ExcludeNouns { get; set; } = new(DefaultStopWords);

    public List<string> ExcludeEntityTags { get; set; } = new() { "DATE" };

    public List<string> ExcludePartOfSpeechTags { get; set; } = new() { "DET", "PRON", "INTJ", "X" };

    public List<string> NounPhraseTags { get; set; } = new() { "PROPN", "NOUNS" };

    public Dictionary<string, string> NounPhraseGrammars { get; set; } = new(StringComparer.OrdinalIgnoreCase)
    {
        ["PROPN,PROPN"] = "PROPN",
        ["NOUN,NOUN"] = "NOUNS",
        ["NOUNS,NOUN"] = "NOUNS",
        ["ADJ,ADJ"] = "ADJ",
        ["ADJ,NOUN"] = "NOUNS"
    };
}
