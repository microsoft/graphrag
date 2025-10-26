using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage;

namespace GraphRag.Indexing;

public sealed class IndexingPipelineRunner
{
    private readonly IServiceProvider _services;
    private readonly IPipelineFactory _pipelineFactory;
    private readonly PipelineExecutor _executor;

    public IndexingPipelineRunner(IServiceProvider services, IPipelineFactory pipelineFactory, PipelineExecutor executor)
    {
        _services = services ?? throw new ArgumentNullException(nameof(services));
        _pipelineFactory = pipelineFactory ?? throw new ArgumentNullException(nameof(pipelineFactory));
        _executor = executor ?? throw new ArgumentNullException(nameof(executor));
    }

    public async Task<IReadOnlyList<PipelineRunResult>> RunAsync(GraphRagConfig config, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(config);

        var pipelineDescriptor = IndexingPipelineDefinitions.Standard;
        var pipeline = _pipelineFactory.BuildIndexingPipeline(pipelineDescriptor);

        var inputStorage = PipelineStorageFactory.Create(config.Input.Storage);
        var outputStorage = PipelineStorageFactory.Create(config.Output);
        var previousStorage = PipelineStorageFactory.Create(config.UpdateIndexOutput);
        var cache = new InMemoryPipelineCache();
        var callbacks = NoopWorkflowCallbacks.Instance;
        var stats = new PipelineRunStats();
        var state = new PipelineState();

        var context = new PipelineRunContext(
            inputStorage,
            outputStorage,
            previousStorage,
            cache,
            callbacks,
            stats,
            state,
            _services);

        var results = new List<PipelineRunResult>();
        await foreach (var result in _executor.ExecuteAsync(pipeline, config, context, cancellationToken).ConfigureAwait(false))
        {
            results.Add(result);
        }

        return results;
    }
}
