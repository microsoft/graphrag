using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace GraphRag.Graphs;

public interface IGraphStore
{
    Task InitializeAsync(CancellationToken cancellationToken = default);

    Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default);

    Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default);

    IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, CancellationToken cancellationToken = default);
}

public sealed record GraphRelationship(
    string SourceId,
    string TargetId,
    string Type,
    IReadOnlyDictionary<string, object?> Properties);
