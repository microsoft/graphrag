using GraphRag.Chunking;
using GraphRag.Indexing;
using GraphRag.Indexing.Runtime;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddGraphRag(this IServiceCollection services)
    {
        services.AddSingleton<TokenTextChunker>();
        services.AddSingleton<MarkdownTextChunker>();
        services.AddSingleton<IChunkerResolver, ChunkerResolver>();
        services.AddSingleton<IPipelineFactory, DefaultPipelineFactory>();
        services.AddSingleton<PipelineExecutor>();
        services.AddSingleton<IndexingPipelineRunner>();
        services.AddKeyedSingleton<WorkflowDelegate>("noop", static (_, _) => (config, context, cancellationToken) => ValueTask.FromResult(new WorkflowResult(null)));
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.LoadInputDocumentsWorkflow.Name, static (_, _) => Indexing.Workflows.LoadInputDocumentsWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CreateBaseTextUnitsWorkflow.Name, static (_, _) => Indexing.Workflows.CreateBaseTextUnitsWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.ExtractGraphWorkflow.Name, static (_, _) => Indexing.Workflows.ExtractGraphWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CommunitySummariesWorkflow.Name, static (_, _) => Indexing.Workflows.CommunitySummariesWorkflow.Create());
        services.AddKeyedSingleton<WorkflowDelegate>(Indexing.Workflows.CreateFinalDocumentsWorkflow.Name, static (_, _) => Indexing.Workflows.CreateFinalDocumentsWorkflow.Create());

        return services;
    }
}
