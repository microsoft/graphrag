using System;
using GraphRag.Indexing.Runtime;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Indexing;

/// <summary>
/// Fluent helper to register pipeline steps backed by keyed delegates.
/// </summary>
public sealed class PipelineStepRegistryBuilder
{
    private readonly IServiceCollection _services;

    internal PipelineStepRegistryBuilder(IServiceCollection services)
    {
        _services = services;
    }

    public PipelineStepRegistryBuilder AddStep(string name, WorkflowDelegate handler)
    {
        ArgumentException.ThrowIfNullOrEmpty(name);
        ArgumentNullException.ThrowIfNull(handler);

        _services.AddKeyedSingleton<WorkflowDelegate>(name, (_, _) => handler);
        return this;
    }
}
