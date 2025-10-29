using GraphRag.Covariates;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Covariates;

public sealed class CovariateRecordTests
{
    [Fact]
    public void Constructor_PopulatesAllProperties()
    {
        var record = new CovariateRecord(
            Id: "cov-1",
            HumanReadableId: 5,
            CovariateType: "claim",
            Type: "fraud",
            Description: "Alleged false reporting",
            SubjectId: "entity-1",
            ObjectId: "entity-2",
            Status: "SUSPECTED",
            StartDate: "2024-03-01",
            EndDate: "2024-04-01",
            SourceText: "Entity-1 may have misled Entity-2",
            TextUnitId: "unit-1");

        Assert.Equal("cov-1", record.Id);
        Assert.Equal(5, record.HumanReadableId);
        Assert.Equal("claim", record.CovariateType);
        Assert.Equal("fraud", record.Type);
        Assert.Equal("Alleged false reporting", record.Description);
        Assert.Equal("entity-1", record.SubjectId);
        Assert.Equal("entity-2", record.ObjectId);
        Assert.Equal("SUSPECTED", record.Status);
        Assert.Equal("2024-03-01", record.StartDate);
        Assert.Equal("2024-04-01", record.EndDate);
        Assert.Equal("Entity-1 may have misled Entity-2", record.SourceText);
        Assert.Equal("unit-1", record.TextUnitId);
    }
}
