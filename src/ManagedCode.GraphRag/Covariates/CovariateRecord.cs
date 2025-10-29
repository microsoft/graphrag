namespace GraphRag.Covariates;

/// <summary>
/// Represents a finalized covariate (claim) row emitted by the GraphRAG pipeline.
/// </summary>
public sealed record CovariateRecord(
    string Id,
    int HumanReadableId,
    string CovariateType,
    string? Type,
    string? Description,
    string SubjectId,
    string? ObjectId,
    string? Status,
    string? StartDate,
    string? EndDate,
    string? SourceText,
    string TextUnitId);
