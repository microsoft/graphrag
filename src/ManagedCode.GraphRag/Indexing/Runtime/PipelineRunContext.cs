using GraphRag.Cache;
using GraphRag.Callbacks;
using GraphRag.Storage;

namespace GraphRag.Indexing.Runtime;

/// <summary>
/// Provides contextual services to workflow implementations.
/// </summary>
public sealed class PipelineRunContext(
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
    public IPipelineStorage InputStorage { get; } = inputStorage ?? throw new ArgumentNullException(nameof(inputStorage));

    public IPipelineStorage OutputStorage { get; } = outputStorage ?? throw new ArgumentNullException(nameof(outputStorage));

    public IPipelineStorage PreviousStorage { get; } = previousStorage ?? throw new ArgumentNullException(nameof(previousStorage));

    public IPipelineCache Cache { get; } = cache ?? throw new ArgumentNullException(nameof(cache));

    public IWorkflowCallbacks Callbacks { get; } = callbacks ?? throw new ArgumentNullException(nameof(callbacks));

    public PipelineRunStats Stats { get; } = stats ?? throw new ArgumentNullException(nameof(stats));

    public PipelineState State { get; } = state ?? throw new ArgumentNullException(nameof(state));

    public IServiceProvider Services { get; } = services ?? throw new ArgumentNullException(nameof(services));

    public IDictionary<string, object?> Items { get; } = items ?? new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
}
