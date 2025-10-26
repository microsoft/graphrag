using GraphRag.Constants;
using GraphRag.Tokenization;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Tokenization;

public sealed class TokenizerRegistryTests
{
    [Fact]
    public void GetTokenizer_DefaultsToPreferredEncoding()
    {
        var defaultTokenizer = TokenizerRegistry.GetTokenizer();
        var explicitTokenizer = TokenizerRegistry.GetTokenizer(TokenizerDefaults.DefaultEncoding);

        Assert.Same(explicitTokenizer, TokenizerRegistry.GetTokenizer());
        Assert.Same(defaultTokenizer, explicitTokenizer);
        Assert.Equal(
            explicitTokenizer.CountTokens("GraphRAG validates default encoding selection."),
            defaultTokenizer.CountTokens("GraphRAG validates default encoding selection."));
    }

    [Fact]
    public void GetTokenizer_FallsBackForUnknownModel()
    {
        var fallbackTokenizer = TokenizerRegistry.GetTokenizer(TokenizerDefaults.DefaultModel);
        var unknownTokenizer = TokenizerRegistry.GetTokenizer("unknown-model-name");

        var sample = "Fallback tokens should match GPT-4 encoding.";
        Assert.Equal(fallbackTokenizer.CountTokens(sample), unknownTokenizer.CountTokens(sample));
    }
}
