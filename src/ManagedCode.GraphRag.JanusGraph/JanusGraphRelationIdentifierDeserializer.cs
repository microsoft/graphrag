using System.Text.Json;
using Gremlin.Net.Structure.IO.GraphSON;

namespace GraphRag.Storage.JanusGraph;

internal sealed class JanusGraphRelationIdentifierDeserializer : IGraphSONDeserializer
{
    public dynamic Objectify(JsonElement graphsonObject, GraphSONReader _)
    {
        if (graphsonObject.ValueKind != JsonValueKind.Object)
        {
            return Normalize(graphsonObject) ?? string.Empty;
        }

        if (graphsonObject.TryGetProperty("relationId", out var relationId) &&
            TryGetString(relationId, out var identifier))
        {
            return identifier ?? string.Empty;
        }

        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var property in graphsonObject.EnumerateObject())
        {
            result[property.Name] = Normalize(property.Value);
        }

        return result;
    }

    private static bool TryGetString(JsonElement element, out string? value)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.String:
                value = element.GetString();
                return true;
            case JsonValueKind.Object when element.TryGetProperty("@value", out var nested):
                return TryGetString(nested, out value);
            default:
                value = null;
                return false;
        }
    }

    private static object? Normalize(JsonElement element)
    {
        return element.ValueKind switch
        {
            JsonValueKind.Object when element.TryGetProperty("@value", out var inner) => Normalize(inner),
            JsonValueKind.Object => NormalizeObject(element),
            JsonValueKind.Array => NormalizeArray(element),
            JsonValueKind.String => element.GetString(),
            JsonValueKind.Number => element.TryGetInt64(out var i64) ? i64 : element.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => null,
            _ => element.GetRawText()
        };
    }

    private static object?[] NormalizeArray(JsonElement element)
    {
        var items = new List<object?>(element.GetArrayLength());
        foreach (var child in element.EnumerateArray())
        {
            items.Add(Normalize(child));
        }

        return items.ToArray();
    }

    private static IDictionary<string, object?> NormalizeObject(JsonElement element)
    {
        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var property in element.EnumerateObject())
        {
            result[property.Name] = Normalize(property.Value);
        }

        return result;
    }
}
