using System.Text;
using System.Text.RegularExpressions;
using GraphRag.Storage;

namespace ManagedCode.GraphRag.Tests.Storage;

public sealed class MemoryPipelineStorageTests
{
    [Fact]
    public async Task FindAsync_ReturnsMetadataFromRegexGroups()
    {
        var storage = new MemoryPipelineStorage();
        await storage.SetAsync("reports/doc-1.json", new MemoryStream(Encoding.UTF8.GetBytes("{}")));
        await storage.SetAsync("news/doc-2.json", new MemoryStream(Encoding.UTF8.GetBytes("{}")));

        var pattern = new Regex("^(?<category>[^/]+)/(?<file>.+\\.json)$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
        var filter = new Dictionary<string, object?> { ["category"] = "news" };

        var matches = new List<PipelineStorageItem>();
        await foreach (var item in storage.FindAsync(pattern, fileFilter: filter))
        {
            matches.Add(item);
        }

        Assert.Single(matches);
        var match = matches[0];
        Assert.Equal("news/doc-2.json", match.Path);
        Assert.Equal("news", match.Metadata["category"]);
        Assert.Equal("doc-2.json", match.Metadata["file"]);
    }

    [Fact]
    public async Task GetAsync_ReturnsStoredContent()
    {
        var storage = new MemoryPipelineStorage();
        await storage.SetAsync("data/file.txt", new MemoryStream(Encoding.UTF8.GetBytes("payload")));

        await using var binaryStream = await storage.GetAsync("data/file.txt", asBytes: true);
        Assert.NotNull(binaryStream);
        using var reader = new StreamReader(binaryStream!, Encoding.UTF8);
        Assert.Equal("payload", await reader.ReadToEndAsync());

        await using var textStream = await storage.GetAsync("data/file.txt", encoding: Encoding.UTF8);
        Assert.NotNull(textStream);
        using var textReader = new StreamReader(textStream!, Encoding.UTF8);
        Assert.Equal("payload", await textReader.ReadToEndAsync());
    }

    [Fact]
    public async Task DeleteAsync_RemovesEntries()
    {
        var storage = new MemoryPipelineStorage();
        await storage.SetAsync("item.bin", new MemoryStream([1, 2, 3]));

        Assert.True(await storage.HasAsync("item.bin"));
        await storage.DeleteAsync("item.bin");
        Assert.False(await storage.HasAsync("item.bin"));
    }

    [Fact]
    public async Task ClearAsync_RemovesScopedEntriesOnly()
    {
        var root = new MemoryPipelineStorage();
        await root.SetAsync("root.txt", new MemoryStream(Encoding.UTF8.GetBytes("root")));

        var child = root.CreateChild("nested");
        await child.SetAsync("child.txt", new MemoryStream(Encoding.UTF8.GetBytes("child")));

        await child.ClearAsync();

        Assert.True(await root.HasAsync("root.txt"));
        Assert.False(await child.HasAsync("child.txt"));
    }
}
