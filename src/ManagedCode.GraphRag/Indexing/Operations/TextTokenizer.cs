using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace GraphRag.Indexing.Operations;

internal static class TextTokenizer
{
    private static readonly Regex TokenRegex = new("\\w+|[^\\w\\s]+|\\s+", RegexOptions.Compiled | RegexOptions.CultureInvariant);

    public static IReadOnlyList<Token> Tokenize(string text)
    {
        if (text is null)
        {
            return Array.Empty<Token>();
        }

        var matches = TokenRegex.Matches(text);
        var tokens = new Token[matches.Count];
        for (var i = 0; i < matches.Count; i++)
        {
            var value = matches[i].Value;
            tokens[i] = new Token(value, !string.IsNullOrWhiteSpace(value));
        }

        return tokens;
    }

    public static int CountTokens(string text)
    {
        return Tokenize(text).Count(token => token.CountsTowardsLimit);
    }

    internal readonly record struct Token(string Value, bool CountsTowardsLimit);
}
