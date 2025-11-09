using System.Text.Json;
using System.Text.Json.Serialization;

namespace GraphRag.Storage.Postgres.ApacheAge.JsonConverters;

internal static class SerializerOptions
{
    public static JsonSerializerOptions Default = new()
    {
        AllowTrailingCommas = true,
        Converters = { new InferredObjectConverter(), new GraphIdConverter() },
        PropertyNameCaseInsensitive = true,
        NumberHandling = JsonNumberHandling.AllowNamedFloatingPointLiterals,
    };

    public static JsonSerializerOptions PathSerializer = new()
    {
        AllowTrailingCommas = true,
        Converters = { new PathObjectConverter() },
        PropertyNameCaseInsensitive = true,
    };
}
