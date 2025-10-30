using System.Collections.Immutable;
using GraphRag;
using GraphRag.Callbacks;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.Indexing.Workflows;
using GraphRag.Relationships;
using GraphRag.Storage;
using ManagedCode.GraphRag.Tests.Infrastructure;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;

namespace ManagedCode.GraphRag.Tests.Integration;

public sealed class CommunitySummariesIntegrationTests : IDisposable
{
    private readonly string _rootDir;

    public CommunitySummariesIntegrationTests()
    {
        _rootDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(_rootDir);
    }

    [Fact]
    public async Task CommunitySummariesWorkflow_UsesManualPromptOverrides()
    {
        var outputDir = Path.Combine(_rootDir, "output");
        var inputDir = Path.Combine(_rootDir, "input");
        var previousDir = Path.Combine(_rootDir, "previous");
        Directory.CreateDirectory(outputDir);
        Directory.CreateDirectory(inputDir);
        Directory.CreateDirectory(previousDir);

        var manualDirectory = Path.Combine(_rootDir, "prompt_overrides");
        var systemOverride = Path.Combine(manualDirectory, "index", "community_reports", "system.txt");
        var userOverride = Path.Combine(manualDirectory, "index", "community_reports", "user.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(systemOverride)!);
        Directory.CreateDirectory(Path.GetDirectoryName(userOverride)!);

        const string systemTemplate = "Manual system guidance";
        const string userTemplate = "Manual template for {{entities}} within {{max_length}} characters.";
        File.WriteAllText(systemOverride, systemTemplate);
        File.WriteAllText(userOverride, userTemplate);

        var outputStorage = new FilePipelineStorage(outputDir);
        await outputStorage.WriteTableAsync(PipelineTableNames.Entities, new[]
        {
            new EntityRecord("entity-1", 0, "Alice", "Person", "Researcher", new[] { "unit-1" }.ToImmutableArray(), 2, 1, 0, 0),
            new EntityRecord("entity-2", 1, "Bob", "Person", "Policy expert", new[] { "unit-2" }.ToImmutableArray(), 1, 1, 0, 0)
        });

        await outputStorage.WriteTableAsync(PipelineTableNames.Relationships, new[]
        {
            new RelationshipRecord("rel-1", 0, "Alice", "Bob", "collaborates_with", "Joint work", 0.8, 2, new[] { "unit-1" }.ToImmutableArray(), true)
        });

        var capturedSystem = string.Empty;
        var capturedUser = string.Empty;
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory(messages =>
            {
                var system = messages.First(m => m.Role == ChatRole.System);
                var user = messages.First(m => m.Role == ChatRole.User);
                capturedSystem = system.Text ?? string.Empty;
                capturedUser = user.Text ?? string.Empty;
                return new ChatResponse(new ChatMessage(ChatRole.Assistant, "Manual summary output"));
            }).CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var config = new GraphRagConfig
        {
            RootDir = _rootDir,
            PromptTuning = new PromptTuningConfig
            {
                Manual = new ManualPromptTuningConfig
                {
                    Enabled = true,
                    Directory = "prompt_overrides"
                }
            },
            CommunityReports = new CommunityReportsConfig
            {
                GraphPrompt = null,
                TextPrompt = null,
                MaxLength = 512
            }
        };

        var context = new PipelineRunContext(
            inputStorage: new FilePipelineStorage(inputDir),
            outputStorage: outputStorage,
            previousStorage: new FilePipelineStorage(previousDir),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var createCommunities = CreateCommunitiesWorkflow.Create();
        await createCommunities(config, context, CancellationToken.None);

        var summaries = CommunitySummariesWorkflow.Create();
        await summaries(config, context, CancellationToken.None);

        Assert.Equal(systemTemplate, capturedSystem);
        Assert.DoesNotContain("{{", capturedUser, StringComparison.Ordinal);
        Assert.Contains("Alice", capturedUser, StringComparison.Ordinal);
        Assert.Contains("Bob", capturedUser, StringComparison.Ordinal);

        var reports = await outputStorage.LoadTableAsync<CommunityReportRecord>(PipelineTableNames.CommunityReports);
        var report = Assert.Single(reports);
        Assert.Equal("Manual summary output", report.Summary);
        Assert.Equal(2, report.EntityTitles.Count);
        Assert.Equal(1, context.Items["community_reports:count"]);
        Assert.True(File.Exists(Path.Combine(outputDir, $"{PipelineTableNames.CommunityReports}.json")));
    }

    [Fact]
    public async Task CommunitySummariesWorkflow_PrefersManualOverAutoPrompts()
    {
        var outputDir = Path.Combine(_rootDir, "output-auto");
        var inputDir = Path.Combine(_rootDir, "input-auto");
        var previousDir = Path.Combine(_rootDir, "previous-auto");
        Directory.CreateDirectory(outputDir);
        Directory.CreateDirectory(inputDir);
        Directory.CreateDirectory(previousDir);

        var manualDirectory = Path.Combine(_rootDir, "prompt_manual");
        var autoDirectory = Path.Combine(_rootDir, "prompt_auto");

        var manualSystem = Path.Combine(manualDirectory, "index", "community_reports", "system.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(manualSystem)!);
        File.WriteAllText(manualSystem, "Manual system override");

        var autoSystem = Path.Combine(autoDirectory, "index", "community_reports", "system.txt");
        var autoUser = Path.Combine(autoDirectory, "index", "community_reports", "user.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(autoSystem)!);
        File.WriteAllText(autoSystem, "Auto system value");
        File.WriteAllText(autoUser, "Auto template for {{entities}} within {{max_length}} characters.");

        var outputStorage = new FilePipelineStorage(outputDir);
        await outputStorage.WriteTableAsync(PipelineTableNames.Entities, new[]
        {
            new EntityRecord("entity-1", 0, "Alice", "Person", "Investigator", new[] { "unit-1" }.ToImmutableArray(), 2, 1, 0, 0),
            new EntityRecord("entity-2", 1, "Eve", "Person", "Analyst", new[] { "unit-2" }.ToImmutableArray(), 1, 1, 0, 0)
        });

        await outputStorage.WriteTableAsync(PipelineTableNames.Relationships, new[]
        {
            new RelationshipRecord("rel-1", 0, "Alice", "Eve", "collaborates_with", "Joint research", 0.7, 2, new[] { "unit-1" }.ToImmutableArray(), true)
        });

        var capturedSystem = string.Empty;
        var capturedUser = string.Empty;
        var services = new ServiceCollection()
            .AddSingleton<IChatClient>(new TestChatClientFactory(messages =>
            {
                var system = messages.First(m => m.Role == ChatRole.System);
                var user = messages.First(m => m.Role == ChatRole.User);
                capturedSystem = system.Text ?? string.Empty;
                capturedUser = user.Text ?? string.Empty;
                return new ChatResponse(new ChatMessage(ChatRole.Assistant, "Combined summary"));
            }).CreateClient())
            .AddGraphRag()
            .BuildServiceProvider();

        var config = new GraphRagConfig
        {
            RootDir = _rootDir,
            PromptTuning = new PromptTuningConfig
            {
                Manual = new ManualPromptTuningConfig
                {
                    Enabled = true,
                    Directory = "prompt_manual"
                },
                Auto = new AutoPromptTuningConfig
                {
                    Enabled = true,
                    Directory = "prompt_auto"
                }
            },
            CommunityReports = new CommunityReportsConfig
            {
                GraphPrompt = null,
                TextPrompt = null,
                MaxLength = 256
            }
        };

        var context = new PipelineRunContext(
            inputStorage: new FilePipelineStorage(inputDir),
            outputStorage: outputStorage,
            previousStorage: new FilePipelineStorage(previousDir),
            cache: new StubPipelineCache(),
            callbacks: NoopWorkflowCallbacks.Instance,
            stats: new PipelineRunStats(),
            state: new PipelineState(),
            services: services);

        var createCommunities = CreateCommunitiesWorkflow.Create();
        await createCommunities(config, context, CancellationToken.None);

        var summaries = CommunitySummariesWorkflow.Create();
        await summaries(config, context, CancellationToken.None);

        Assert.Equal("Manual system override", capturedSystem);
        Assert.Contains("Auto template", capturedUser, StringComparison.Ordinal);
        Assert.DoesNotContain("{{", capturedUser, StringComparison.Ordinal);

        var reports = await outputStorage.LoadTableAsync<CommunityReportRecord>(PipelineTableNames.CommunityReports);
        var report = Assert.Single(reports);
        Assert.Equal("Combined summary", report.Summary);
        Assert.Equal(2, report.EntityTitles.Count);
    }

    public void Dispose()
    {
        try
        {
            if (Directory.Exists(_rootDir))
            {
                Directory.Delete(_rootDir, recursive: true);
            }
        }
        catch
        {
        }
    }
}
