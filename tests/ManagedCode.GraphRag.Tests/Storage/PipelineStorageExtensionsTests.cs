using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using GraphRag.Storage;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Storage;

public sealed class PipelineStorageExtensionsTests
{
    [Fact]
    public async Task WriteAndLoadTable_RoundTripsRecords()
    {
        var storage = new MemoryPipelineStorage();
        var records = new[] { new SampleRecord { Id = 1, Name = "Alice" } };

        await storage.WriteTableAsync("records", records);
        Assert.True(await storage.TableExistsAsync("records"));

        var loaded = await storage.LoadTableAsync<SampleRecord>("records");

        Assert.Single(loaded);
        Assert.Equal(1, loaded[0].Id);
        Assert.Equal("Alice", loaded[0].Name);
    }

    [Fact]
    public async Task DeleteTableAsync_RemovesStoredData()
    {
        var storage = new MemoryPipelineStorage();
        await storage.WriteTableAsync("records", new[] { new SampleRecord { Id = 2, Name = "Bob" } });

        await storage.DeleteTableAsync("records");

        Assert.False(await storage.TableExistsAsync("records"));
    }

    [Fact]
    public async Task LoadTableAsync_ThrowsWhenMissing()
    {
        var storage = new MemoryPipelineStorage();
        var exception = await Assert.ThrowsAsync<FileNotFoundException>(() => storage.LoadTableAsync<SampleRecord>("missing"));
        Assert.Contains("missing", exception.Message, StringComparison.Ordinal);
    }

    private sealed record SampleRecord
    {
        public int Id { get; init; }
        public string? Name { get; init; }
    }
}
