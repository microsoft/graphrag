using System.Collections.Generic;

namespace GraphRag.Tokenization;

public interface ITextTokenizer
{
    int CountTokens(string text);

    IReadOnlyList<int> Encode(string text);

    string Decode(IReadOnlyList<int> tokens);
}
