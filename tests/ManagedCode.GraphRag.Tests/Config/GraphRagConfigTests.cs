using GraphRag.Config;

namespace ManagedCode.GraphRag.Tests.Config;

public sealed class GraphRagConfigTests
{
    [Fact]
    public void CacheConfig_UsesFileDefaults()
    {
        var cache = new CacheConfig();
        Assert.Equal(CacheType.File, cache.Type);
        Assert.Equal("cache", cache.BaseDir);
        Assert.Null(cache.ConnectionString);
    }

    [Fact]
    public void ExtractGraphNlpConfig_HasTextAnalyzerDefaults()
    {
        var config = new ExtractGraphNlpConfig();

        Assert.True(config.NormalizeEdgeWeights);
        Assert.Equal(NounPhraseExtractorType.RegexEnglish, config.TextAnalyzer.ExtractorType);
        Assert.Contains("stuff", config.TextAnalyzer.ExcludeNouns);
        Assert.Equal("PROPN", config.TextAnalyzer.NounPhraseGrammars["PROPN,PROPN"]);
        Assert.Equal(25, config.ConcurrentRequests);
        Assert.Equal(AsyncType.Threaded, config.AsyncMode);
    }

    [Fact]
    public void ClaimExtractionConfig_ReadsPromptFromRoot()
    {
        var tempRoot = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(tempRoot);
        var promptPath = Path.Combine(tempRoot, "claims.txt");
        File.WriteAllText(promptPath, "Prompt Body");

        try
        {
            var config = new ClaimExtractionConfig
            {
                Prompt = "claims.txt",
                Description = "desc",
                MaxGleanings = 2,
                ModelId = "chat"
            };

            var strategy = config.GetResolvedStrategy(tempRoot);
            Assert.Equal("chat", strategy["model_id"]);
            Assert.Equal("Prompt Body", strategy["extraction_prompt"]);
            Assert.Equal("desc", strategy["claim_description"]);
            Assert.Equal(2, strategy["max_gleanings"]);
        }
        finally
        {
            Directory.Delete(tempRoot, recursive: true);
        }
    }
}
