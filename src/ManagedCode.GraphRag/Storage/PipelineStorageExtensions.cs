using System.IO;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Storage;

public static class PipelineStorageExtensions
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true,
        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
    };

    public static async Task<IReadOnlyList<T>> LoadTableAsync<T>(this IPipelineStorage storage, string name, CancellationToken cancellationToken = default)
    {
        var stream = await storage.GetAsync(ToFileName(name), asBytes: true, cancellationToken: cancellationToken).ConfigureAwait(false);
        if (stream is null)
        {
            throw new FileNotFoundException($"Table '{name}' not found in pipeline storage.");
        }

        await using (stream.ConfigureAwait(false))
        {
            return await JsonSerializer.DeserializeAsync<IReadOnlyList<T>>(stream, SerializerOptions, cancellationToken).ConfigureAwait(false)
                ?? Array.Empty<T>();
        }
    }

    public static async Task WriteTableAsync<T>(this IPipelineStorage storage, string name, IReadOnlyCollection<T> rows, CancellationToken cancellationToken = default)
    {
        var ms = new MemoryStream();
        await JsonSerializer.SerializeAsync(ms, rows, SerializerOptions, cancellationToken).ConfigureAwait(false);
        ms.Position = 0;
        await storage.SetAsync(ToFileName(name), ms, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    public static async Task DeleteTableAsync(this IPipelineStorage storage, string name, CancellationToken cancellationToken = default)
    {
        await storage.DeleteAsync(ToFileName(name), cancellationToken).ConfigureAwait(false);
    }

    public static async Task<bool> TableExistsAsync(this IPipelineStorage storage, string name, CancellationToken cancellationToken = default)
    {
        return await storage.HasAsync(ToFileName(name), cancellationToken).ConfigureAwait(false);
    }

    private static string ToFileName(string name) => $"{name}.json";
}
