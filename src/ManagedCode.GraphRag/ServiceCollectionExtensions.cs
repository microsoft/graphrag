using System;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Chunking;
using GraphRag.Indexing;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddGraphRag(this IServiceCollection services, Action<PipelineStepRegistryBuilder>? configure = null)
    {
        services.AddSingleton<TokenTextChunker>();
        services.AddSingleton<MarkdownTextChunker>();
        services.AddSingleton<IChunkerResolver, ChunkerResolver>();
        services.AddSingleton<IPipelineFactory, DefaultPipelineFactory>();
        services.AddSingleton<PipelineExecutor>();
        services.AddSingleton<IndexingPipelineRunner>();
        services.AddKeyedSingleton<WorkflowDelegate>("noop", (_, _) => static (config, context, cancellationToken) => ValueTask.FromResult(new WorkflowResult(null)));
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.LoadInputDocumentsWorkflow.Name, (_, _) => Indexing.Workflows.LoadInputDocumentsWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CreateBaseTextUnitsWorkflow.Name, (_, _) => Indexing.Workflows.CreateBaseTextUnitsWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CreateFinalDocumentsWorkflow.Name, (_, _) => Indexing.Workflows.CreateFinalDocumentsWorkflow.Create());

        if (configure is not null)
        {
            configure(new PipelineStepRegistryBuilder(services));
        }

        return services;
    }
}
