using System;
using System.Collections.Generic;
using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Storage;

namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Provides contextual services to workflow implementations.
/// </summary>
public sealed class PipelineRunContext
{
    public PipelineRunContext(
        IPipelineStorage inputStorage,
        IPipelineStorage outputStorage,
        IPipelineStorage previousStorage,
        IPipelineCache cache,
        IWorkflowCallbacks callbacks,
        PipelineRunStats stats,
        PipelineState state,
        IServiceProvider services,
        IDictionary<string, object?>? items = null)
    {
        InputStorage = inputStorage ?? throw new ArgumentNullException(nameof(inputStorage));
        OutputStorage = outputStorage ?? throw new ArgumentNullException(nameof(outputStorage));
        PreviousStorage = previousStorage ?? throw new ArgumentNullException(nameof(previousStorage));
        Cache = cache ?? throw new ArgumentNullException(nameof(cache));
        Callbacks = callbacks ?? throw new ArgumentNullException(nameof(callbacks));
        Stats = stats ?? throw new ArgumentNullException(nameof(stats));
        State = state ?? throw new ArgumentNullException(nameof(state));
        Services = services ?? throw new ArgumentNullException(nameof(services));
        Items = items ?? new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
    }

    public IPipelineStorage InputStorage { get; }

    public IPipelineStorage OutputStorage { get; }

    public IPipelineStorage PreviousStorage { get; }

    public IPipelineCache Cache { get; }

    public IWorkflowCallbacks Callbacks { get; }

    public PipelineRunStats Stats { get; }

    public PipelineState State { get; }

    public IServiceProvider Services { get; }

    public IDictionary<string, object?> Items { get; }
}
