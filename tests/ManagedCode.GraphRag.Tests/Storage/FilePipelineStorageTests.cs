using System.Text;
using System.Text.RegularExpressions;
using GraphRag.Storage;

namespace ManagedCode.GraphRag.Tests.Storage;

public sealed class FilePipelineStorageTests
{
    [Fact]
    public async Task FindAsync_AppliesRegexMetadataAndFilter()
    {
        var root = Path.Combine(Path.GetTempPath(), $"graphrag-tests-{Guid.NewGuid():N}");
        var storage = new FilePipelineStorage(root);

        try
        {
            await storage.SetAsync("reports/doc-1.json", new MemoryStream(Encoding.UTF8.GetBytes("{}")));
            await storage.SetAsync("news/doc-2.json", new MemoryStream(Encoding.UTF8.GetBytes("{}")));

            var pattern = new Regex("^(?<category>[^/]+)/(?<file>.+\\.json)$", RegexOptions.IgnoreCase | RegexOptions.CultureInvariant);
            var filter = new Dictionary<string, object?> { ["category"] = "reports" };

            var matches = new List<PipelineStorageItem>();
            await foreach (var item in storage.FindAsync(pattern, fileFilter: filter))
            {
                matches.Add(item);
            }

            Assert.Single(matches);
            var match = matches[0];
            Assert.Equal("reports/doc-1.json", match.Path);
            Assert.Equal("reports", match.Metadata["category"]);
            Assert.Equal("doc-1.json", match.Metadata["file"]);
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    [Fact]
    public async Task GetAsync_ReadsTextWithEncoding()
    {
        var root = Path.Combine(Path.GetTempPath(), $"graphrag-tests-{Guid.NewGuid():N}");
        var storage = new FilePipelineStorage(root);

        try
        {
            const string content = "file payload";
            await storage.SetAsync("notes/doc.txt", new MemoryStream(Encoding.UTF8.GetBytes(content)));

            await using var stream = await storage.GetAsync("notes/doc.txt", encoding: Encoding.UTF8);
            Assert.NotNull(stream);
            using var reader = new StreamReader(stream!, Encoding.UTF8);
            Assert.Equal(content, await reader.ReadToEndAsync());
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    [Fact]
    public async Task ClearAsync_RemovesAllFiles()
    {
        var root = Path.Combine(Path.GetTempPath(), $"graphrag-tests-{Guid.NewGuid():N}");
        var storage = new FilePipelineStorage(root);

        try
        {
            await storage.SetAsync("a/file1.txt", new MemoryStream(Encoding.UTF8.GetBytes("a")));
            await storage.SetAsync("b/file2.txt", new MemoryStream(Encoding.UTF8.GetBytes("b")));

            await storage.ClearAsync();

            var matches = new List<PipelineStorageItem>();
            await foreach (var item in storage.FindAsync(new Regex(".*")))
            {
                matches.Add(item);
            }

            Assert.Empty(matches);
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }
}
