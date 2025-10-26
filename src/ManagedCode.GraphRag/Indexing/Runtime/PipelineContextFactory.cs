using System;
using System.Collections.Generic;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Storage;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Indexing.Runtime;

public static class PipelineContextFactory
{
    public static PipelineRunContext Create(
        IPipelineStorage? inputStorage = null,
        IPipelineStorage? outputStorage = null,
        IPipelineStorage? previousStorage = null,
        IPipelineCache? cache = null,
        IWorkflowCallbacks? callbacks = null,
        PipelineRunStats? stats = null,
        PipelineState? state = null,
        IServiceProvider? services = null,
        IDictionary<string, object?>? items = null)
    {
        return new PipelineRunContext(
            inputStorage ?? new MemoryPipelineStorage(),
            outputStorage ?? new MemoryPipelineStorage(),
            previousStorage ?? new MemoryPipelineStorage(),
            cache ?? new InMemoryPipelineCache(),
            callbacks ?? NoopWorkflowCallbacks.Instance,
            stats ?? new PipelineRunStats(),
            state ?? new PipelineState(),
            services ?? new ServiceCollection().BuildServiceProvider(),
            items);
    }
}
