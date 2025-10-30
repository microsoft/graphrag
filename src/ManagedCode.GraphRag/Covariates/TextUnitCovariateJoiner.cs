using GraphRag.Data;

namespace GraphRag.Covariates;

/// <summary>
/// Provides helpers for attaching extracted covariates back onto text unit records.
/// </summary>
public static class TextUnitCovariateJoiner
{
    public static IReadOnlyList<TextUnitRecord> Attach(
        IReadOnlyList<TextUnitRecord> textUnits,
        IReadOnlyList<CovariateRecord> covariates)
    {
        ArgumentNullException.ThrowIfNull(textUnits);
        ArgumentNullException.ThrowIfNull(covariates);

        if (textUnits.Count == 0 || covariates.Count == 0)
        {
            return textUnits;
        }

        var lookup = new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);
        foreach (var covariate in covariates)
        {
            if (string.IsNullOrWhiteSpace(covariate.TextUnitId))
            {
                continue;
            }

            if (!lookup.TryGetValue(covariate.TextUnitId, out var ids))
            {
                ids = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                lookup[covariate.TextUnitId] = ids;
            }

            if (!string.IsNullOrWhiteSpace(covariate.Id))
            {
                ids.Add(covariate.Id);
            }
        }

        if (lookup.Count == 0)
        {
            return textUnits;
        }

        var results = new List<TextUnitRecord>(textUnits.Count);
        foreach (var unit in textUnits)
        {
            if (!lookup.TryGetValue(unit.Id, out var ids))
            {
                results.Add(unit);
                continue;
            }

            var existing = unit.CovariateIds ?? Array.Empty<string>();
            var combined = new HashSet<string>(existing, StringComparer.OrdinalIgnoreCase);
            foreach (var id in ids)
            {
                combined.Add(id);
            }

            var ordered = combined
                .OrderBy(value => value, StringComparer.Ordinal)
                .ToArray();

            results.Add(unit with { CovariateIds = ordered });
        }

        return results;
    }
}
