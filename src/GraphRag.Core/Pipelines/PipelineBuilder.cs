using GraphRag.Pipelines;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Core.Pipelines;

/// <summary>
/// Lightweight pipeline builder inspired by the Python workflow factory.
/// </summary>
public sealed class PipelineBuilder
{
    private readonly IList<Func<PipelineContext, CancellationToken, ValueTask>> _steps = new List<Func<PipelineContext, CancellationToken, ValueTask>>();
    private string _name = "pipeline";

    public PipelineBuilder Named(string name)
    {
        _name = name;
        return this;
    }

    public PipelineBuilder Step(Func<PipelineContext, CancellationToken, ValueTask> action)
    {
        _steps.Add(action);
        return this;
    }

    public IPipeline Build(ILoggerFactory? loggerFactory = null)
    {
        var steps = _steps.ToArray();
        var name = _name;
        var logger = loggerFactory?.CreateLogger(name);

        return new DelegatedPipeline(name, steps, logger);
    }

    private sealed class DelegatedPipeline(string name, IReadOnlyList<Func<PipelineContext, CancellationToken, ValueTask>> steps, ILogger? logger) : IPipeline
    {
        public async ValueTask ExecuteAsync(PipelineContext context, CancellationToken cancellationToken = default)
        {
            for (var index = 0; index < steps.Count; index++)
            {
                var step = steps[index];
                logger?.LogDebug("Executing {PipelineName} step {StepIndex}", name, index);
                await step(context, cancellationToken).ConfigureAwait(false);
            }
        }
    }
}
