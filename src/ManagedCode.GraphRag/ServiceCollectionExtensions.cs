using System;
using System.Threading;
using System.Threading.Tasks;

using GraphRag.Core.Pipelines;
using GraphRag.Pipelines;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Core;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddGraphRagCore(this IServiceCollection services, Action<PipelineStepRegistryBuilder>? configure = null)
    {
        services.AddSingleton<IPipelineFactory, DefaultPipelineFactory>();
        services.AddKeyedSingleton<Func<PipelineContext, CancellationToken, ValueTask>>("noop", (_, _) => ValueTask.CompletedTask);

        if (configure is not null)
        {
            configure(new PipelineStepRegistryBuilder(services));
        }

        return services;
    }
}
