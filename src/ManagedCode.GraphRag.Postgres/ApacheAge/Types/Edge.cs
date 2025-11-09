using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace GraphRag.Storage.Postgres.ApacheAge.Types;

public struct Edge
{
    /// <summary>
    /// Footer added to the end of every agtype edge.
    /// </summary>
    public const string FOOTER = "::edge";

    /// <summary>
    /// Edge's unique identifier.
    /// </summary>
    public GraphId Id { get; set; }

    /// <summary>
    /// Identifier of the edge's start <see cref="Vertex"/>.
    /// </summary>

    [JsonPropertyName("start_id")]
    public GraphId StartId { get; set; }

    /// <summary>
    /// Identifier of the edge's end <see cref="Vertex"/>.
    /// </summary>
    [JsonPropertyName("end_id")]
    public GraphId EndId { get; set; }

    /// <summary>
    /// Label.
    /// </summary>
    public string Label { get; set; }

    /// <summary>
    /// Other properties of the edge.
    /// </summary>
    public Dictionary<string, object?> Properties { get; set; }

    public override readonly string ToString()
    {
        var serialisedProperties = JsonSerializer.Serialize(Properties);
        var result = $@"{{""id"": {Id.Value}, ""label"": ""{Label}"", ""end_id"": {EndId.Value}, ""start_id"": {StartId.Value}, ""properties"": {serialisedProperties}}}::edge";

        return result;
    }

    public override readonly bool Equals([NotNullWhen(true)] object? obj)
    {
        if (obj is null || obj is not Edge)
        {
            return false;
        }

        var input = (Edge)obj;

        return Id == input.Id;
    }

    public override readonly int GetHashCode()
    {
        return Id.GetHashCode();
    }

    public static bool operator ==(Edge left, Edge right)
    {
        return left.Equals(right);
    }

    public static bool operator !=(Edge left, Edge right)
    {
        return !left.Equals(right);
    }
}
