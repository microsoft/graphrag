using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Postgres;

public sealed class PostgresExplainService([FromKeyedServices] PostgresGraphStore graphStore, ILogger<PostgresExplainService> logger)
{
    private readonly PostgresGraphStore _graphStore = graphStore ?? throw new ArgumentNullException(nameof(graphStore));
    private readonly ILogger<PostgresExplainService> _logger = logger ?? throw new ArgumentNullException(nameof(logger));

    public async Task<string> GetFormattedPlanAsync(string cypherQuery, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(cypherQuery);

        var planLines = await _graphStore.ExplainAsync(cypherQuery, parameters, cancellationToken).ConfigureAwait(false);
        if (planLines.Count == 0)
        {
            return "EXPLAIN returned no plan.";
        }

        var builder = new StringBuilder();
        builder.AppendLine("EXPLAIN plan:");
        foreach (var line in planLines)
        {
            builder.Append("  ");
            builder.AppendLine(line);
        }

        return builder.ToString();
    }

    public async Task WritePlanAsync(string cypherQuery, TextWriter writer, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(writer);

        var formattedPlan = await GetFormattedPlanAsync(cypherQuery, parameters, cancellationToken).ConfigureAwait(false);
        await writer.WriteAsync(formattedPlan.AsMemory(), cancellationToken).ConfigureAwait(false);
        if (!formattedPlan.EndsWith(Environment.NewLine, StringComparison.Ordinal))
        {
            await writer.WriteLineAsync().ConfigureAwait(false);
        }
    }

    public async Task<int> ExecuteAsync(string cypherQuery, IReadOnlyDictionary<string, object?>? parameters = null, CancellationToken cancellationToken = default)
    {
        await WritePlanAsync(cypherQuery, Console.Out, parameters, cancellationToken).ConfigureAwait(false);
        _logger.LogInformation("Executed EXPLAIN for query on graph store: {Graph}", _graphStore.GetType().Name);
        return 0;
    }
}
