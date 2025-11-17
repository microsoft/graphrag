using GraphRag.Covariates;

namespace ManagedCode.GraphRag.Tests.Covariates;

public sealed class CovariateRecordTests
{
    [Fact]
    public void CovariateRecord_StoresProperties()
    {
        var record = new CovariateRecord(
            "id",
            10,
            "claim",
            "type",
            "description",
            "subject",
            "object",
            "status",
            "2024-01-01",
            "2024-01-02",
            "source",
            "text-unit");

        Assert.Equal("id", record.Id);
        Assert.Equal("subject", record.SubjectId);
        Assert.Equal("text-unit", record.TextUnitId);
    }
}
