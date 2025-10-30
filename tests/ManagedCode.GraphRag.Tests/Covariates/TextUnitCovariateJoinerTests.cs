using GraphRag.Covariates;
using GraphRag.Data;

namespace ManagedCode.GraphRag.Tests.Covariates;

public sealed class TextUnitCovariateJoinerTests
{
    [Fact]
    public void Attach_MergesCovariateIdentifiersOntoTextUnits()
    {
        var textUnits = new[]
        {
            new TextUnitRecord
            {
                Id = "unit-1",
                Text = "Alpha",
                DocumentIds = new[] { "doc-1" },
                TokenCount = 12,
                CovariateIds = Array.Empty<string>()
            },
            new TextUnitRecord
            {
                Id = "unit-2",
                Text = "Beta",
                DocumentIds = new[] { "doc-2" },
                TokenCount = 15,
                CovariateIds = new[] { "existing" }
            },
            new TextUnitRecord
            {
                Id = "unit-3",
                Text = "Gamma",
                DocumentIds = new[] { "doc-3" },
                TokenCount = 9
            }
        };

        var covariates = new[]
        {
            new CovariateRecord("cov-1", 0, "claim", "fraud", "", "entity-1", null, "OPEN", null, null, null, "unit-1"),
            new CovariateRecord("cov-2", 1, "claim", "fraud", "", "entity-1", null, "OPEN", null, null, null, "unit-1"),
            new CovariateRecord("cov-3", 2, "claim", "audit", "", "entity-2", null, "OPEN", null, null, null, "unit-2")
        };

        var updated = TextUnitCovariateJoiner.Attach(textUnits, covariates);

        var first = Assert.Single(updated, unit => unit.Id == "unit-1");
        Assert.Equal(new[] { "cov-1", "cov-2" }, first.CovariateIds);

        var second = Assert.Single(updated, unit => unit.Id == "unit-2");
        Assert.Equal(new[] { "cov-3", "existing" }, second.CovariateIds);

        var third = Assert.Single(updated, unit => unit.Id == "unit-3");
        Assert.Empty(third.CovariateIds);
    }
}
