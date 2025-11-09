using System.Text.Json;
using System.Text.Json.Serialization;
using GraphRag.Storage.Postgres.ApacheAge.Types;

namespace GraphRag.Storage.Postgres.ApacheAge.JsonConverters;

/// <summary>
/// A custom converter to convert JSON objects to vertices and edges in a path and
/// vice versa.
/// </summary>
internal sealed class PathObjectConverter : JsonConverter<object>
{
    private int _counter;

    public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        /*
         * Every path consists of vertices and edges. It is certain that
         * the first and last elements of a path are vertices. Also, it is
         * certain that an edge exists between two contiguous vertices.
         * Therefore, a path will look like this:
         * path = v -> e -> v ->...-> v -> e -> v.
         * 
         * Because of this, if we use a zero-based counter, we can be sure that
         * all vertices will fall on even numbers and edges will fall on odd numbers.
         */

        var json = JsonDocument.ParseValue(ref reader).RootElement.GetRawText();
        object? result;

        if (_counter % 2 == 0)
        {
            result = JsonSerializer.Deserialize<Vertex>(json, SerializerOptions.Default);
        }
        else
        {
            result = JsonSerializer.Deserialize<Edge>(json, SerializerOptions.Default);
        }

        _counter++;
        return result;
    }

    public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
    {
        JsonSerializer.Serialize(writer, value, value.GetType(), options);
    }
}
