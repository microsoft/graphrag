using System.Diagnostics.CodeAnalysis;
using System.Text.Json;

namespace GraphRag.Storage.Postgres.ApacheAge.Types;

public struct Vertex
{
    /// <summary>
    /// Footer added to the end of every agtype vertex.
    /// </summary>
    public const string FOOTER = "::vertex";

    /// <summary>
    /// Vertex's unique identifier.
    /// </summary>
    public GraphId Id { get; set; }

    /// <summary>
    /// Label.
    /// </summary>
    public string Label { get; set; }

    /// <summary>
    /// Other properties of the vertex.
    /// </summary>
    public Dictionary<string, object?> Properties { get; set; }

    public override readonly string ToString()
    {
        var serialisedProperties = JsonSerializer.Serialize(Properties);
        var result = $@"{{""id"": {Id.Value}, ""label"": ""{Label}"", ""properties"": {serialisedProperties}}}::vertex";

        return result;
    }

    public override readonly bool Equals([NotNullWhen(true)] object? obj)
    {
        if (obj is null || obj is not Vertex)
        {
            return false;
        }

        var input = (Vertex)obj;

        return Id == input.Id;
    }

    public override readonly int GetHashCode()
    {
        return Id.GetHashCode();
    }

    public static bool operator ==(Vertex left, Vertex right)
    {
        return left.Equals(right);
    }

    public static bool operator !=(Vertex left, Vertex right)
    {
        return !left.Equals(right);
    }
}
