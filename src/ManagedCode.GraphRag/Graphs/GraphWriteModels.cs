namespace GraphRag.Graphs;

public sealed record GraphNodeUpsert(
    string Id,
    string Label,
    IReadOnlyDictionary<string, object?> Properties);

public sealed record GraphRelationshipUpsert(
    string SourceId,
    string TargetId,
    string Type,
    IReadOnlyDictionary<string, object?> Properties,
    bool Bidirectional = false);
