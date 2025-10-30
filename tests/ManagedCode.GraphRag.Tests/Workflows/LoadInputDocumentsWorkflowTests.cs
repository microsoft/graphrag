using System.Text;
using System.Text.Json;
using GraphRag;
using GraphRag.Callbacks;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Workflows;

public sealed class LoadInputDocumentsWorkflowTests
{
    [Fact]
    public async Task RunWorkflow_LoadsTextFiles()
    {
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();
        var inputStorage = new MemoryPipelineStorage();
        await inputStorage.SetAsync("doc1.txt", new MemoryStream(Encoding.UTF8.GetBytes("First document")));
        await inputStorage.SetAsync("doc2.txt", new MemoryStream(Encoding.UTF8.GetBytes("Second document")));

        var outputStorage = new MemoryPipelineStorage();
        var context = new PipelineRunContext(
            inputStorage,
            outputStorage,
            previousStorage: new MemoryPipelineStorage(),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var config = new GraphRagConfig
        {
            Input = new InputConfig
            {
                Storage = new StorageConfig { Type = StorageType.Memory },
                FileType = InputFileType.Text,
                FilePattern = ".*\\.txt$",
                Encoding = "utf-8"
            }
        };

        var workflow = LoadInputDocumentsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents);
        Assert.Equal(2, documents.Count);
        Assert.All(documents, document => Assert.False(string.IsNullOrWhiteSpace(document.Id)));
    }

    [Fact]
    public async Task RunWorkflow_LoadsCsvFiles()
    {
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();
        var inputStorage = new MemoryPipelineStorage();
        const string csv = "id,title,text,category\n1,Intro,Hello world,news\n2,Detail,Second line,updates\n";
        await inputStorage.SetAsync("docs/sample.csv", new MemoryStream(Encoding.UTF8.GetBytes(csv)));

        var outputStorage = new MemoryPipelineStorage();
        var context = new PipelineRunContext(
            inputStorage,
            outputStorage,
            new MemoryPipelineStorage(),
            new StubPipelineCache(),
            NoopWorkflowCallbacks.Instance,
            new PipelineRunStats(),
            new PipelineState(),
            services);

        var config = new GraphRagConfig
        {
            Input = new InputConfig
            {
                Storage = new StorageConfig { Type = StorageType.Memory },
                FileType = InputFileType.Csv,
                FilePattern = ".*\\.csv$",
                TextColumn = "text",
                TitleColumn = "title",
                Metadata = new List<string> { "category" }
            }
        };

        var workflow = LoadInputDocumentsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents);
        Assert.Equal(2, documents.Count);
        Assert.Contains(documents, doc => doc.Title == "Intro" && doc.Metadata?["category"]?.ToString() == "news");
    }

    [Fact]
    public async Task RunWorkflow_LoadsJsonFiles()
    {
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();
        var inputStorage = new MemoryPipelineStorage();
        var jsonArray = JsonSerializer.Serialize(new[]
        {
            new { id = "1", title = "Intro", text = "JSON body", category = "news" },
            new { id = "2", title = "Follow-up", text = "More JSON", category = "updates" }
        });
        await inputStorage.SetAsync("docs/sample.json", new MemoryStream(Encoding.UTF8.GetBytes(jsonArray)));

        var outputStorage = new MemoryPipelineStorage();
        var context = new PipelineRunContext(
            inputStorage,
            outputStorage,
            new MemoryPipelineStorage(),
            new StubPipelineCache(),
            NoopWorkflowCallbacks.Instance,
            new PipelineRunStats(),
            new PipelineState(),
            services);

        var config = new GraphRagConfig
        {
            Input = new InputConfig
            {
                Storage = new StorageConfig { Type = StorageType.Memory },
                FileType = InputFileType.Json,
                FilePattern = ".*\\.json$",
                TextColumn = "text",
                TitleColumn = "title",
                Metadata = new List<string> { "category" }
            }
        };

        var workflow = LoadInputDocumentsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents);
        Assert.Equal(2, documents.Count);
        Assert.Contains(documents, doc => doc.Title == "Follow-up" && doc.Metadata?["category"]?.ToString() == "updates");
    }

    [Fact]
    public async Task RunWorkflow_ParsesJsonLinesFallback()
    {
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory().CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();
        var inputStorage = new MemoryPipelineStorage();
        const string jsonLines = "{\"id\":\"1\",\"title\":\"Line One\",\"text\":\"Alpha body\"}\n{\"id\":\"2\",\"title\":\"Line Two\",\"text\":\"Beta body\"}\n";
        await inputStorage.SetAsync("docs/sample.jsonl", new MemoryStream(Encoding.UTF8.GetBytes(jsonLines)));

        var outputStorage = new MemoryPipelineStorage();
        var context = new PipelineRunContext(
            inputStorage,
            outputStorage,
            new MemoryPipelineStorage(),
            new StubPipelineCache(),
            NoopWorkflowCallbacks.Instance,
            new PipelineRunStats(),
            new PipelineState(),
            services);

        var config = new GraphRagConfig
        {
            Input = new InputConfig
            {
                Storage = new StorageConfig { Type = StorageType.Memory },
                FileType = InputFileType.Json,
                FilePattern = ".*\\.jsonl$",
                TextColumn = "text",
                TitleColumn = "title"
            }
        };

        var workflow = LoadInputDocumentsWorkflow.Create();
        await workflow(config, context, CancellationToken.None);

        var documents = await outputStorage.LoadTableAsync<DocumentRecord>(PipelineTableNames.Documents);
        Assert.Equal(2, documents.Count);
        Assert.Contains(documents, doc => doc.Text.Contains("Alpha", StringComparison.Ordinal));
        Assert.Contains(documents, doc => doc.Text.Contains("Beta", StringComparison.Ordinal));
    }
}
