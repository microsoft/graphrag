using System;
using System.Collections.Generic;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Indexing.Runtime;

public sealed class DefaultPipelineFactory(IServiceProvider services) : IPipelineFactory
{
    public WorkflowPipeline BuildIndexingPipeline(IndexingPipelineDescriptor descriptor)
    {
        return BuildPipeline(descriptor.Name, descriptor.Steps);
    }

    public WorkflowPipeline BuildQueryPipeline(QueryPipelineDescriptor descriptor)
    {
        return BuildPipeline(descriptor.Name, descriptor.Steps);
    }

    private WorkflowPipeline BuildPipeline(string name, IReadOnlyList<string> steps)
    {
        var builder = new PipelineBuilder().Named(name);
        foreach (var step in steps)
        {
            builder.Step(step, ResolveStep(step));
        }

        return builder.Build();
    }

    private WorkflowDelegate ResolveStep(string stepName)
    {
        return services.GetRequiredKeyedService<WorkflowDelegate>(stepName);
    }
}
