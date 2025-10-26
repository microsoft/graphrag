using System.IO;
using System.Text;
using System.Text.Json;
using Microsoft.Azure.Cosmos;

namespace GraphRag.Storage.Cosmos;

internal sealed class SystemTextJsonCosmosSerializer : CosmosSerializer
{
    private static readonly JsonSerializerOptions DefaultOptions = new(JsonSerializerDefaults.Web)
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        WriteIndented = false
    };

    private readonly JsonSerializerOptions _options;

    public SystemTextJsonCosmosSerializer(JsonSerializerOptions? options = null)
    {
        _options = options ?? DefaultOptions;
    }

    public override T FromStream<T>(Stream stream)
    {
        if (stream is null)
        {
            throw new ArgumentNullException(nameof(stream));
        }

        if (typeof(T) == typeof(Stream))
        {
            return (T)(object)stream;
        }

        if (stream.CanRead && stream.Length == 0)
        {
            return default!;
        }

        return JsonSerializer.Deserialize<T>(stream, _options)!;
    }

    public override Stream ToStream<T>(T input)
    {
        var stream = new MemoryStream();
        if (input is null)
        {
            return stream;
        }

        using var writer = new Utf8JsonWriter(stream, new JsonWriterOptions { SkipValidation = false, Indented = false });
        JsonSerializer.Serialize(writer, input, _options);
        writer.Flush();
        stream.Position = 0;
        return stream;
    }
}
