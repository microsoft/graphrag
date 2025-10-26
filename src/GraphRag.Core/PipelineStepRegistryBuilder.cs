using System.Threading;
using System.Threading.Tasks;

using GraphRag.Pipelines;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Core;

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

    public PipelineStepRegistryBuilder AddStep(string name, Func<PipelineContext, CancellationToken, ValueTask> handler)
    {
        ArgumentException.ThrowIfNullOrEmpty(name);
        ArgumentNullException.ThrowIfNull(handler);

        _services.AddKeyedSingleton<Func<PipelineContext, CancellationToken, ValueTask>>(name, (_, _) => handler);
        return this;
    }
}
