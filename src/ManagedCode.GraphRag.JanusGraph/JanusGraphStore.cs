using System.Collections;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text.Json;
using GraphRag.Graphs;
using Gremlin.Net.Driver;
using Gremlin.Net.Driver.Exceptions;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.JanusGraph;

public sealed class JanusGraphStore : IGraphStore, IAsyncDisposable
{
    private const string PropertyBagKey = "gr_props";
    private static readonly string[] TransientMarkers =
    {
        "Local lock contention",
        "Expected value mismatch",
        "violates a uniqueness constraint"
    };
    private readonly GremlinClient _client;
    private readonly ILogger<JanusGraphStore> _logger;

    public JanusGraphStore(JanusGraphStoreOptions options, ILogger<JanusGraphStore> logger)
    {
        ArgumentNullException.ThrowIfNull(options);
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));

        var server = new GremlinServer(options.Host, options.Port, enableSsl: false);
        var serializer = JanusGraphGraphSONSerializerFactory.Create();
        var poolSettings = BuildConnectionPoolSettings(options);
        _client = new GremlinClient(server, serializer, poolSettings);
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
nodeTraversal = g.V().hasLabel(nodeLabel).has('id', nodeId).fold().coalesce(unfold(), addV(nodeLabel).property('id', nodeId));
node = nodeTraversal.next();
propValue = node.property('gr_props').orElse(null);
propBag = propValue == null ? [:] : new groovy.json.JsonSlurper().parseText(propValue);
props.each { k, v ->
  if (v == null) { propBag.remove(k); }
  else { propBag[k] = v; }
};
node.property('gr_props', groovy.json.JsonOutput.toJson(propBag));
node;
null";

        var bindings = new Dictionary<string, object?>
        {
            ["nodeLabel"] = label,
            ["nodeId"] = id,
            ["props"] = PreparePropertyPayload(properties)
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
sourceTraversal = g.V().has('id', sourceVertexId).limit(1);
targetTraversal = g.V().has('id', targetVertexId).limit(1);
if (!sourceTraversal.hasNext() || !targetTraversal.hasNext()) {
  throw new RuntimeException('Source or target vertex not found.');
}
g.V().has('id', sourceVertexId).outE(edgeLabel).where(inV().has('id', targetVertexId)).drop().iterate();
sourceVertex = sourceTraversal.next();
targetVertex = targetTraversal.next();
edge = sourceVertex.addEdge(edgeLabel, targetVertex);
propBag = [:];
props.each { k, v ->
  if (v == null) { propBag.remove(k); }
  else { propBag[k] = v; }
};
edge.property('gr_props', groovy.json.JsonOutput.toJson(propBag));
edge;
null";

        var bindings = new Dictionary<string, object?>
        {
            ["sourceVertexId"] = sourceId,
            ["targetVertexId"] = targetId,
            ["edgeLabel"] = type,
            ["props"] = PreparePropertyPayload(properties)
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

    public async Task DeleteNodesAsync(IReadOnlyCollection<string> nodeIds, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(nodeIds);
        if (nodeIds.Count == 0)
        {
            return;
        }

        const string script = @"
if (nodeIds == null || nodeIds.isEmpty()) {
  return [];
}
g.V().has('id', within(nodeIds)).drop().iterate();";

        var bindings = new Dictionary<string, object?>
        {
            ["nodeIds"] = nodeIds.ToArray()
        };

        await SubmitAsync<object>(script, bindings, cancellationToken).ConfigureAwait(false);
    }

    public async Task DeleteRelationshipsAsync(IReadOnlyCollection<GraphRelationshipKey> relationships, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(relationships);
        if (relationships.Count == 0)
        {
            return;
        }

        const string script = @"
edges.each { rel ->
  g.V().has('id', rel.sourceId)
    .outE(rel.type)
    .where(inV().has('id', rel.targetId))
    .drop()
    .iterate();
}";

        foreach (var batch in relationships.Chunk(64))
        {
            var payload = batch.Select(rel => new Dictionary<string, object?>
            {
                ["sourceId"] = rel.SourceId,
                ["targetId"] = rel.TargetId,
                ["type"] = rel.Type
            }).ToList();

            var bindings = new Dictionary<string, object?>
            {
                ["edges"] = payload
            };

            await SubmitAsync<object>(script, bindings, cancellationToken).ConfigureAwait(false);
        }
    }

    public async IAsyncEnumerable<GraphRelationship> GetOutgoingRelationshipsAsync(string sourceId, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourceId);

        const string script = @"
g.V().has('id', sourceId)
 .outE()
 .project('sourceId','targetId','type','properties')
 .by(outV().values('id'))
 .by(inV().values('id'))
 .by(label())
 .by(coalesce(values('gr_props'), constant([:])))";
        var bindings = new Dictionary<string, object?> { ["sourceId"] = sourceId };
        var edges = await SubmitAsync<IDictionary<object, object?>>(script, bindings, cancellationToken).ConfigureAwait(false);

        foreach (var edge in edges)
        {
            yield return ToRelationship((IDictionary)edge);
        }
    }

    public async IAsyncEnumerable<GraphNode> GetNodesAsync(GraphTraversalOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options?.Validate();
        var (skip, take) = (options?.Skip, options?.Take);

        var script = BuildRangeScript("g.V()", skip, take, out var parameters);
        script += ".valueMap(true)";

        var nodes = await SubmitAsync<IDictionary<object, object?>>(script, parameters, cancellationToken).ConfigureAwait(false);
        foreach (var node in nodes)
        {
            yield return ToNode((IDictionary)node);
        }
    }

    public async IAsyncEnumerable<GraphRelationship> GetRelationshipsAsync(GraphTraversalOptions? options = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        options?.Validate();
        var script = BuildRangeScript("g.E()", options?.Skip, options?.Take, out var parameters);
        script += @".project('sourceId','targetId','type','properties')
            .by(outV().values('id'))
            .by(inV().values('id'))
            .by(label())
            .by(coalesce(values('gr_props'), constant([:])))";

        var edges = await SubmitAsync<IDictionary<object, object?>>(script, parameters, cancellationToken).ConfigureAwait(false);
        foreach (var edge in edges)
        {
            yield return ToRelationship((IDictionary)edge);
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
        const int MaxRetries = 5;
        var attempt = 0;

        while (true)
        {
            try
            {
                var bindings = ConvertBindings(parameters);
                var result = await _client.SubmitAsync<T>(script, bindings, cancellationToken).ConfigureAwait(false);
                return result.ToList();
            }
            catch (ResponseException ex) when (attempt < MaxRetries && IsTransient(ex))
            {
                attempt++;
                var delay = TimeSpan.FromMilliseconds(100 * attempt);
                _logger.LogWarning(ex, "Transient JanusGraph error, retrying attempt {Attempt} of {MaxAttempts} for script {Script}", attempt, MaxRetries, script);
                await Task.Delay(delay, cancellationToken).ConfigureAwait(false);
            }
            catch (ResponseException ex)
            {
                _logger.LogError(ex, "JanusGraph query failed: {Script}", script);
                throw;
            }
        }
    }

    private static GraphNode ToNode(IDictionary raw)
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

            if (string.Equals(key, PropertyBagKey, StringComparison.OrdinalIgnoreCase))
            {
                ApplyJsonPropertyBag(properties, value);
                continue;
            }

            properties[key] = NormalizeValue(value);
        }

        return new GraphNode(id, label, properties);
    }

    private static GraphRelationship ToRelationship(IDictionary raw)
    {
        var map = NormalizeMap(raw);
        if (map.TryGetValue("sourceId", out var simpleSource) &&
            map.TryGetValue("targetId", out var simpleTarget) &&
            map.TryGetValue("type", out var simpleType))
        {
            var props = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
            if (map.TryGetValue("properties", out var propsValue))
            {
                ApplyJsonPropertyBag(props, propsValue);
            }

            return new GraphRelationship(
                ToScalarString(simpleSource),
                ToScalarString(simpleTarget),
                ToScalarString(simpleType),
                props);
        }

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

            if (string.Equals(key, PropertyBagKey, StringComparison.OrdinalIgnoreCase))
            {
                ApplyJsonPropertyBag(properties, value);
                continue;
            }

            properties[key] = NormalizeValue(value);
        }

        return new GraphRelationship(source, target, label, properties);
    }

    private static Dictionary<string, object?> NormalizeMap(IDictionary raw)
    {
        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (DictionaryEntry entry in raw)
        {
            var key = Convert.ToString(entry.Key, CultureInfo.InvariantCulture) ?? string.Empty;
            result[key] = entry.Value;
        }

        return result;
    }

    private static bool IsMetaKey(string key) =>
        key is "id" or "label" or "~id" or "~label" or "~inV" or "~outV" or "inV" or "outV" or "T.id" or "T.label";

    private static string GetMeta(IReadOnlyDictionary<string, object?> map, string key)
    {
        if (map.TryGetValue(key, out var value) && value is not null)
        {
            return ToScalarString(value);
        }

        var metaKey = "~" + key;
        if (map.TryGetValue(metaKey, out value) && value is not null)
        {
            return ToScalarString(value);
        }

        var tokenKey = "T." + key;
        if (map.TryGetValue(tokenKey, out value) && value is not null)
        {
            return ToScalarString(value);
        }

        return string.Empty;
    }

    private static string ToScalarString(object? value)
    {
        switch (value)
        {
            case null:
                return string.Empty;
            case string s:
                return s;
            case IDictionary:
                return string.Empty;
            case IEnumerable enumerable:
                foreach (var item in enumerable)
                {
                    return ToScalarString(item);
                }

                return string.Empty;
            default:
                return Convert.ToString(value, CultureInfo.InvariantCulture) ?? string.Empty;
        }
    }

    private static string ExtractVertexId(IReadOnlyDictionary<string, object?> map, string key)
    {
        if (map.TryGetValue(key, out var value) || map.TryGetValue("~" + key, out value))
        {
            if (value is IDictionary dictionary)
            {
                var normalized = NormalizeMap(dictionary);
                return GetMeta(normalized, "id");
            }

            return ToScalarString(value);
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
        IDictionary dictionary => dictionary.Cast<DictionaryEntry>()
            .ToDictionary(
                entry => Convert.ToString(entry.Key, CultureInfo.InvariantCulture) ?? string.Empty,
                entry => (object?)NormalizeValue(entry.Value),
                StringComparer.OrdinalIgnoreCase),
        IList list when list.Count == 1 => NormalizeValue(list[0]),
        IEnumerable enumerable when enumerable is not string => enumerable.Cast<object?>().Select(NormalizeValue).ToArray(),
        DateTime dateTime => dateTime.ToUniversalTime(),
        DateTimeOffset dto => dto.ToUniversalTime(),
        byte[] bytes => Convert.ToBase64String(bytes),
        _ => value
    };

    private static bool IsTransient(ResponseException ex)
    {
        foreach (var marker in TransientMarkers)
        {
            if (ContainsMarker(ex.Message, marker))
            {
                return true;
            }

            if (ex.StatusAttributes is not null &&
                ex.StatusAttributes.TryGetValue("message", out var attribute) &&
                attribute is string statusMessage &&
                ContainsMarker(statusMessage, marker))
            {
                return true;
            }
        }

        return false;
    }

    private static bool ContainsMarker(string? source, string marker) =>
        source?.IndexOf(marker, StringComparison.OrdinalIgnoreCase) >= 0;

    private static ConnectionPoolSettings BuildConnectionPoolSettings(JanusGraphStoreOptions options)
    {
        var settings = new ConnectionPoolSettings
        {
            PoolSize = options.ConnectionPoolSize ?? 32,
            MaxInProcessPerConnection = options.MaxInProcessPerConnection ?? 64
        };

        options.ConfigureConnectionPool?.Invoke(settings);
        return settings;
    }

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

    private static Dictionary<string, object?> PreparePropertyPayload(IReadOnlyDictionary<string, object?> properties)
    {
        var result = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        foreach (var (key, value) in properties)
        {
            if (string.Equals(key, "id", StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            result[key] = value;
        }

        return result;
    }

    private static void ApplyJsonPropertyBag(IDictionary<string, object?> target, object? value)
    {
        switch (value)
        {
            case null:
                return;
            case string json when !string.IsNullOrWhiteSpace(json):
                using (var document = JsonDocument.Parse(json))
                {
                    if (document.RootElement.ValueKind == JsonValueKind.Object)
                    {
                        foreach (var property in document.RootElement.EnumerateObject())
                        {
                            target[property.Name] = NormalizeValue(property.Value);
                        }
                    }
                }

                break;
            case IEnumerable enumerable when value is not string:
                foreach (var item in enumerable)
                {
                    ApplyJsonPropertyBag(target, item);
                    break;
                }

                break;
            default:
                break;
        }
    }
}

public sealed class JanusGraphStoreOptions
{
    public string Host { get; set; } = "localhost";
    public int Port { get; set; } = 8182;
    public string TraversalSource { get; set; } = "g";
    public int? ConnectionPoolSize { get; set; }
    public int? MaxInProcessPerConnection { get; set; }
    public Action<ConnectionPoolSettings>? ConfigureConnectionPool { get; set; }
}
