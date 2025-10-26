using System;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Indexing;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddGraphRagCore(this IServiceCollection services, Action<PipelineStepRegistryBuilder>? configure = null)
    {
        services.AddSingleton<IPipelineFactory, DefaultPipelineFactory>();
        services.AddKeyedSingleton<WorkflowDelegate>("noop", (_, _) => static (config, context, cancellationToken) => ValueTask.FromResult(new WorkflowResult(null)));
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CreateBaseTextUnitsWorkflow.Name, (_, _) => Indexing.Workflows.CreateBaseTextUnitsWorkflow.Create());

        if (configure is not null)
        {
            configure(new PipelineStepRegistryBuilder(services));
        }

        return services;
    }
}
