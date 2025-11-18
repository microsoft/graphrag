using Gremlin.Net.Structure.IO.GraphSON;

namespace GraphRag.Storage.JanusGraph;

internal static class JanusGraphGraphSONSerializerFactory
{
    private static readonly IReadOnlyDictionary<string, IGraphSONDeserializer> CustomDeserializers = new Dictionary<string, IGraphSONDeserializer>(StringComparer.Ordinal)
    {
        ["janusgraph:RelationIdentifier"] = new JanusGraphRelationIdentifierDeserializer()
    };

    public static GraphSON3MessageSerializer Create() =>
        new(new GraphSON3Reader(CustomDeserializers), new GraphSON3Writer());
}
