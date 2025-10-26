using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Logging.Abstractions;

namespace ManagedCode.GraphRag.Tests.Postgres;

internal sealed class FakePostgresGraphStore : PostgresGraphStore
{
    private readonly IReadOnlyList<string> _plan;

    public FakePostgresGraphStore(Action<PostgresGraphStoreOptions>? configure = null, IReadOnlyList<string>? explainPlan = null)
        : base(CreateOptions(configure), NullLogger<PostgresGraphStore>.Instance)
    {
        _plan = explainPlan ?? Array.Empty<string>();
    }

    public string? CapturedQuery { get; private set; }

    public IReadOnlyDictionary<string, object?>? CapturedParameters { get; private set; }

    public List<string> ExecutedIndexCommands { get; } = new();

    public List<(string Query, string Parameters)> CapturedExplainInvocations { get; } = new();

    public int CypherExecutions { get; private set; }

    public int NodeUpserts { get; private set; }

    public int RelationshipUpserts { get; private set; }

    public List<IReadOnlyDictionary<string, object?>> LoggedParameters { get; } = new();

    protected override Task ExecuteCypherAsync(string query, IReadOnlyDictionary<string, object?> parameters, CancellationToken cancellationToken)
    {
        CapturedQuery = query;
        CapturedParameters = parameters;
        CypherExecutions++;
        LoggedParameters.Add(parameters);

        if (query.Contains("MERGE (n:", StringComparison.Ordinal))
        {
            NodeUpserts++;
        }
        else if (query.Contains("MERGE (source", StringComparison.Ordinal))
        {
            RelationshipUpserts++;
        }

        return Task.CompletedTask;
    }

    protected override Task<string?> ResolveLabelRelationAsync(string label, bool isEdge, CancellationToken cancellationToken)
    {
        var prefix = isEdge ? "edge" : "vertex";
        return Task.FromResult<string?>($"\"graph\".\"{prefix}_{label.ToLowerInvariant()}\"");
    }

    protected override Task ExecuteIndexCommandsAsync(IEnumerable<string> commands, CancellationToken cancellationToken)
    {
        ExecutedIndexCommands.AddRange(commands);
        return Task.CompletedTask;
    }

    protected override Task<IReadOnlyList<string>> ExecuteExplainAsync(string explainQuery, string parameterJson, CancellationToken cancellationToken)
    {
        CapturedExplainInvocations.Add((explainQuery, parameterJson));
        return Task.FromResult(_plan);
    }

    private static PostgresGraphStoreOptions CreateOptions(Action<PostgresGraphStoreOptions>? configure)
    {
        var options = new PostgresGraphStoreOptions
        {
            ConnectionString = "Host=localhost;Username=test;Password=test;Database=test",
            GraphName = "graph",
            AutoCreateIndexes = true
        };

        configure?.Invoke(options);
        return options;
    }
}
