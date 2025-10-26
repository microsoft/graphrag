namespace GraphRag.Logging;

public sealed record ProgressSnapshot(string? Description, int? TotalItems, int? CompletedItems);
