using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Indexing.Heuristics;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Workflows;

internal static class HeuristicMaintenanceWorkflow
{
    public const string Name = "heuristic_maintenance";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var textUnits = await context.OutputStorage
                .LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits, cancellationToken)
                .ConfigureAwait(false);

            if (textUnits.Count == 0)
            {
                return new WorkflowResult(Array.Empty<TextUnitRecord>());
            }

            var loggerFactory = context.Services.GetService<ILoggerFactory>();
            var logger = loggerFactory?.CreateLogger(typeof(HeuristicMaintenanceWorkflow));

            var processed = await TextUnitHeuristicProcessor
                .ApplyAsync(config, textUnits, context.Services, logger, cancellationToken)
                .ConfigureAwait(false);

            await context.OutputStorage
                .WriteTableAsync(PipelineTableNames.TextUnits, processed, cancellationToken)
                .ConfigureAwait(false);

            return new WorkflowResult(processed);
        };
    }
}
