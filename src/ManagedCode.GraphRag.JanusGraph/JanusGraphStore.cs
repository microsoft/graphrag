using System.Collections;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Collections.Generic;
using System.Linq;
using GraphRag.Graphs;
using Gremlin.Net.Driver;
using Gremlin.Net.Driver.Exceptions;
using Gremlin.Net.Structure.IO.GraphSON;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.JanusGraph;

public sealed class JanusGraphStore : IGraphStore, IAsyncDisposable
{
    private readonly GremlinClient _client;
    private readonly ILogger<JanusGraphStore> _logger;

    public JanusGraphStore(JanusGraphStoreOptions options, ILogger<JanusGraphStore> logger)
    {
        ArgumentNullException.ThrowIfNull(options);
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));

        var server = new GremlinServer(options.Host, options.Port, enableSsl: false);
        _client = new GremlinClient(server, new GraphSON3MessageSerializer());
    }

    public async Task InitializeAsync(CancellationToken cancellationToken = default)
    {
        await SubmitAsync<object>("g.V().limit(1)", null, cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Connected to JanusGraph.");
    }

    public async Task UpsertNodeAsync(string id, string label, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(label);
        ArgumentNullException.ThrowIfNull(properties);

        const string script = @"
node = g.V().hasLabel(label).has('id', id).fold().coalesce(unfold(), addV(label).property('id', id));
props.each { k, v ->
  if (v == null) { node.properties(k).drop(); }
  else { node.property(k, v); }
};
node";

        var bindings = new Dictionary<string, object?>
        {
            ["label"] = label,
            ["id"] = id,
            ["props"] = properties
        };

        await SubmitAsync<object>(script, bindings, cancellationToken).ConfigureAwait(false);
    }

    public async Task UpsertNodesAsync(IReadOnlyCollection<GraphNodeUpsert> nodes, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodes);
        foreach (var node in nodes)
        {
            await UpsertNodeAsync(node.Id, node.Label, node.Properties, cancellationToken).ConfigureAwait(false);
        }
    }

    public async Task UpsertRelationshipAsync(string sourceId, string targetId, string type, IReadOnlyDictionary<string, object?> properties, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);
        ArgumentException.ThrowIfNullOrWhiteSpace(targetId);
        ArgumentException.ThrowIfNullOrWhiteSpace(type);
        ArgumentNullException.ThrowIfNull(properties);

        const string script = @"
source = g.V().has('id', sourceId).tryNext().orElse(null);
target = g.V().has('id', targetId).tryNext().orElse(null);
if (source == null || target == null) {
  throw new RuntimeException('Source or target vertex not found.');
}
sourceVertex = source;
targetVertex = target;
sourceVertex.outE(type).where(inV().has('id', targetId)).drop().iterate();
edge = sourceVertex.addE(type).to(targetVertex).next();
props.each { k, v ->
  if (v == null) { edge.properties(k).drop(); }
  else { edge.property(k, v); }
};
edge";

        var bindings = new Dictionary<string, object?>
        {
            ["sourceId"] = sourceId,
            ["targetId"] = targetId,
            ["type"] = type,
            ["props"] = properties
        };

        await SubmitAsync<object>(script, bindings, cancellationToken).ConfigureAwait(false);
    }

    public async Task UpsertRelationshipsAsync(IReadOnlyCollection<GraphRelationshipUpsert> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        foreach (var relationship in relationships)
        {
            await UpsertRelationshipAsync(
                relationship.SourceId,
                relationship.TargetId,
                relationship.Type,
                relationship.Properties,
                cancellationToken).ConfigureAwait(false);

            if (relationship.Bidirectional)
            {
                await UpsertRelationshipAsync(
                    relationship.TargetId,
                    relationship.SourceId,
                    relationship.Type,
                    relationship.Properties,
                    cancellationToken).ConfigureAwait(false);
            }
        }
    }

    public async IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);

        const string script = "g.V().has('id', sourceId).outE().elementMap()";
        var bindings = new Dictionary<string, object?> { ["sourceId"] = sourceId };
        var edges = await SubmitAsync<IDictionary<string, object?>>(script, bindings, cancellationToken).ConfigureAwait(false);

        foreach (var edge in edges)
        {
            yield return ToRelationship(edge);
        }
    }

    public async IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options?.Validate();
        var (skip, take) = (options?.Skip, options?.Take);

        var script = BuildRangeScript("g.V()", skip, take, out var parameters);
        script += ".valueMap(true)";

        var nodes = await SubmitAsync<IDictionary<string, object?>>(script, parameters, cancellationToken).ConfigureAwait(false);
        foreach (var node in nodes)
        {
            yield return ToNode(node);
        }
    }

    public async IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options?.Validate();
        var script = BuildRangeScript("g.E()", options?.Skip, options?.Take, out var parameters);
        script += ".elementMap()";

        var edges = await SubmitAsync<IDictionary<string, object?>>(script, parameters, cancellationToken).ConfigureAwait(false);
        foreach (var edge in edges)
        {
            yield return ToRelationship(edge);
        }
    }

    public ValueTask DisposeAsync()
    {
        _client.Dispose();
        return ValueTask.CompletedTask;
    }

    private static string BuildRangeScript(string root, int? skip, int? take, out Dictionary<string, object?> parameters)
    {
        parameters = new Dictionary<string, object?>();
        var script = root;
        if (skip is > 0)
        {
            parameters["skip"] = skip.Value;
            script += ".skip(skip)";
        }

        if (take is > 0)
        {
            parameters["take"] = take.Value;
            script += ".limit(take)";
        }

        return script;
    }

    private async Task<IReadOnlyList<T>> SubmitAsync<T>(string script, IDictionary<string, object?>? parameters, CancellationToken cancellationToken)
    {
        try
        {
            var bindings = ConvertBindings(parameters);
            var result = await _client.SubmitAsync<T>(script, bindings, cancellationToken).ConfigureAwait(false);
            return result.ToList();
        }
        catch (ResponseException ex)
        {
            _logger.LogError(ex, "JanusGraph query failed: {Script}", script);
            throw;
        }
    }

    private static GraphNode ToNode(IDictionary<string, object?> raw)
    {
        var map = NormalizeMap(raw);
        var id = GetMeta(map, "id");
        var label = GetMeta(map, "label");

        var properties = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var (key, value) in map)
        {
            if (IsMetaKey(key))
            {
                continue;
            }

            properties[key] = NormalizeValue(value);
        }

        return new GraphNode(id, label, properties);
    }

    private static GraphRelationship ToRelationship(IDictionary<string, object?> raw)
    {
        var map = NormalizeMap(raw);
        var label = GetMeta(map, "label");
        var source = ExtractVertexId(map, "outV");
        var target = ExtractVertexId(map, "inV");

        var properties = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var (key, value) in map)
        {
            if (IsMetaKey(key))
            {
                continue;
            }

            properties[key] = NormalizeValue(value);
        }

        return new GraphRelationship(source, target, label, properties);
    }

    private static Dictionary<string, object?> NormalizeMap(IDictionary<string, object?> raw)
    {
        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var entry in raw)
        {
            var key = entry.Key?.ToString() ?? string.Empty;
            result[key] = entry.Value;
        }

        return result;
    }

    private static bool IsMetaKey(string key) =>
        key is "id" or "label" or "~id" or "~label" or "~inV" or "~outV" or "inV" or "outV";

    private static string GetMeta(IReadOnlyDictionary<string, object?> map, string key)
    {
        if (map.TryGetValue(key, out var value) && value is not null)
        {
            return Convert.ToString(value, CultureInfo.InvariantCulture) ?? string.Empty;
        }

        var metaKey = "~" + key;
        if (map.TryGetValue(metaKey, out value) && value is not null)
        {
            return Convert.ToString(value, CultureInfo.InvariantCulture) ?? string.Empty;
        }

        return string.Empty;
    }

    private static string ExtractVertexId(IReadOnlyDictionary<string, object?> map, string key)
    {
        if (map.TryGetValue(key, out var value) || map.TryGetValue("~" + key, out value))
        {
            return value switch
            {
                null => string.Empty,
                IDictionary<string, object?> dict => GetMeta((IReadOnlyDictionary<string, object?>)dict, "id"),
                _ => Convert.ToString(value, CultureInfo.InvariantCulture) ?? string.Empty
            };
        }

        return string.Empty;
    }

    private static object? NormalizeValue(object? value) => value switch
    {
        null => null,
        JsonElement element => element.ValueKind switch
        {
            JsonValueKind.Object => NormalizeJsonObject(element),
            JsonValueKind.Array => element.EnumerateArray().Select(item => NormalizeValue(item)).ToArray(),
            JsonValueKind.String => element.GetString(),
            JsonValueKind.Number => element.TryGetInt64(out var i64) ? i64 : element.GetDouble(),
            JsonValueKind.True => true,
            JsonValueKind.False => false,
            JsonValueKind.Null => null,
            _ => element.GetRawText()
        },
        IDictionary<string, object?> dict => dict.ToDictionary(pair => pair.Key, pair => (object?)NormalizeValue(pair.Value), StringComparer.OrdinalIgnoreCase),
        IList list when list.Count == 1 => NormalizeValue(list[0]),
        IEnumerable enumerable when enumerable is not string => enumerable.Cast<object?>().Select(item => NormalizeValue(item)).ToArray(),
        DateTime dateTime => dateTime.ToUniversalTime(),
        DateTimeOffset dto => dto.ToUniversalTime(),
        byte[] bytes => Convert.ToBase64String(bytes),
        _ => value
    };

    private static Dictionary<string, object> ConvertBindings(IDictionary<string, object?>? source)
    {
        var result = new Dictionary<string, object>();
        if (source is null)
        {
            return result;
        }

        foreach (var (key, value) in source)
        {
            result[key] = value!;
        }

        return result;
    }

    private static IDictionary<string, object?> NormalizeJsonObject(JsonElement element)
    {
        var dict = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var property in element.EnumerateObject())
        {
            dict[property.Name] = NormalizeValue(property.Value);
        }

        return dict;
    }
}

public sealed class JanusGraphStoreOptions
{
    public string Host { get; set; } = "localhost";
    public int Port { get; set; } = 8182;
    public string TraversalSource { get; set; } = "g";
}
