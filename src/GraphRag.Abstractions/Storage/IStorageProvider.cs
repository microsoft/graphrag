namespace GraphRag.Storage;

public interface IStorageProvider
{
    Task InitializeAsync(CancellationToken cancellationToken = default);

    Task<Stream> OpenReadAsync(string path, CancellationToken cancellationToken = default);

    Task WriteAsync(string path, Stream content, CancellationToken cancellationToken = default);
}
