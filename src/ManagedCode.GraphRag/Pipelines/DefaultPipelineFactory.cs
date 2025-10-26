using GraphRag.Pipelines;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Core.Pipelines;

public sealed class DefaultPipelineFactory(IServiceProvider services, ILoggerFactory loggerFactory) : IPipelineFactory
{
    public IPipeline BuildIndexingPipeline(IndexingPipelineDescriptor descriptor)
    {
        return BuildPipeline(descriptor.Name, descriptor.Steps);
    }

    public IPipeline BuildQueryPipeline(QueryPipelineDescriptor descriptor)
    {
        return BuildPipeline(descriptor.Name, descriptor.Steps);
    }

    private IPipeline BuildPipeline(string name, IReadOnlyList<string> steps)
    {
        var builder = new PipelineBuilder().Named(name);
        foreach (var step in steps)
        {
            builder.Step(CreateStep(step));
        }

        return builder.Build(loggerFactory);
    }

    private Func<PipelineContext, CancellationToken, ValueTask> CreateStep(string stepName)
    {
        return async (context, token) =>
        {
            var step = services.GetRequiredKeyedService<Func<PipelineContext, CancellationToken, ValueTask>>(stepName);
            await step(context, token).ConfigureAwait(false);
        };
    }
}
