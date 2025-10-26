using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using GraphRag.Config;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Executes workflow pipelines, mirroring the semantics of the Python runner.
/// </summary>
public sealed class PipelineExecutor
{
    private readonly ILogger<PipelineExecutor> _logger;

    public PipelineExecutor(ILogger<PipelineExecutor> logger)
    {
        _logger = logger ?? throw new ArgumentNullException(nameof(logger));
    }

    public async IAsyncEnumerable<PipelineRunResult> ExecuteAsync(
        WorkflowPipeline pipeline,
        GraphRagConfig config,
        PipelineRunContext context,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(pipeline);
        ArgumentNullException.ThrowIfNull(config);
        ArgumentNullException.ThrowIfNull(context);

        var results = new List<PipelineRunResult>();
        var startTimestamp = Stopwatch.GetTimestamp();

        context.Callbacks.PipelineStart(pipeline.Names);

        foreach (var step in pipeline.Steps)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var workflowStart = Stopwatch.GetTimestamp();
            context.Callbacks.WorkflowStart(step.Name, step);

            WorkflowResult? workflowResult = null;
            Exception? exception = null;

            try
            {
                _logger.LogInformation("Executing workflow {Workflow}", step.Name);
                workflowResult = await step.Delegate(config, context, cancellationToken).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                exception = ex;
                _logger.LogError(ex, "Workflow {Workflow} failed", step.Name);
            }
            finally
            {
                context.Callbacks.WorkflowEnd(step.Name, step);
            }

            var elapsed = Stopwatch.GetElapsedTime(workflowStart);
            context.Stats.GetOrAddWorkflowStats(step.Name)["overall"] = elapsed.TotalSeconds;

            PipelineRunResult runResult;
            if (exception is not null)
            {
                runResult = new PipelineRunResult(step.Name, null, context.State, new[] { exception });
                results.Add(runResult);
                yield return runResult;
                break;
            }

            runResult = new PipelineRunResult(step.Name, workflowResult?.Result, context.State, null);
            results.Add(runResult);
            yield return runResult;

            if (workflowResult?.Stop == true)
            {
                _logger.LogInformation("Workflow {Workflow} requested pipeline halt", step.Name);
                break;
            }
        }

        var totalElapsed = Stopwatch.GetElapsedTime(startTimestamp);
        context.Stats.TotalRuntime = totalElapsed.TotalSeconds;

        context.Callbacks.PipelineEnd(results);
    }
}
