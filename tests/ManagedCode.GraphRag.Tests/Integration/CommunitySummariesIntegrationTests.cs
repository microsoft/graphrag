using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.IO;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using GraphRag;
using GraphRag.Cache;
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
using Xunit;

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
            cache: new InMemoryPipelineCache(),
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
