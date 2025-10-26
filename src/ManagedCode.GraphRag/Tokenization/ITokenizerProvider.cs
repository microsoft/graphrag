namespace GraphRag.Tokenization;

public interface ITokenizerProvider
{
    ITextTokenizer GetTokenizer(string encodingName);
}
