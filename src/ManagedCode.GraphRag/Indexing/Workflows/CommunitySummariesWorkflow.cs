using System.Text;
using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.LanguageModels;
using GraphRag.Relationships;
using GraphRag.Storage;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Workflows;

internal static class CommunitySummariesWorkflow
{
    public const string Name = "community_summaries";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var entities = await context.OutputStorage
                .LoadTableAsync<EntityRecord>(PipelineTableNames.Entities, cancellationToken)
                .ConfigureAwait(false);

            if (entities.Count == 0)
            {
                await context.OutputStorage
                    .WriteTableAsync(PipelineTableNames.CommunityReports, Array.Empty<CommunityReportRecord>(), cancellationToken)
                    .ConfigureAwait(false);
                return new WorkflowResult(Array.Empty<CommunityReportRecord>());
            }

            IReadOnlyList<RelationshipRecord> relationships;
            if (await context.OutputStorage.TableExistsAsync(PipelineTableNames.Relationships, cancellationToken).ConfigureAwait(false))
            {
                relationships = await context.OutputStorage
                    .LoadTableAsync<RelationshipRecord>(PipelineTableNames.Relationships, cancellationToken)
                    .ConfigureAwait(false);
            }
            else
            {
                relationships = Array.Empty<RelationshipRecord>();
            }

            IReadOnlyList<CommunityRecord> communities;
            if (await context.OutputStorage.TableExistsAsync(PipelineTableNames.Communities, cancellationToken).ConfigureAwait(false))
            {
                communities = await context.OutputStorage
                    .LoadTableAsync<CommunityRecord>(PipelineTableNames.Communities, cancellationToken)
                    .ConfigureAwait(false);
            }
            else
            {
                communities = CommunityBuilder.Build(entities, relationships, config.ClusterGraph);
            }

            if (communities.Count == 0)
            {
                await context.OutputStorage
                    .WriteTableAsync(PipelineTableNames.CommunityReports, Array.Empty<CommunityReportRecord>(), cancellationToken)
                    .ConfigureAwait(false);
                return new WorkflowResult(Array.Empty<CommunityReportRecord>());
            }

            var entityLookup = entities.ToDictionary(entity => entity.Id, StringComparer.OrdinalIgnoreCase);
            var logger = context.Services.GetService<ILoggerFactory>()?.CreateLogger(typeof(CommunitySummariesWorkflow));
            var reportsConfig = config.CommunityReports ?? new CommunityReportsConfig();
            var chatClient = ResolveChatClient(context.Services, reportsConfig.ModelId, logger);
            var reports = new List<CommunityReportRecord>(communities.Count);

            for (var index = 0; index < communities.Count; index++)
            {
                cancellationToken.ThrowIfCancellationRequested();

                var community = communities[index];
                var members = community.EntityIds
                    .Select(id => entityLookup.TryGetValue(id, out var entity) ? entity : null)
                    .Where(static entity => entity is not null)
                    .Cast<EntityRecord>()
                    .ToArray();

                if (members.Length == 0)
                {
                    continue;
                }

                var summary = string.Empty;

                try
                {
                    summary = await GenerateCommunitySummaryAsync(
                        chatClient,
                        GraphRagPromptLibrary.CommunitySummarySystemPrompt,
                        GraphRagPromptLibrary.BuildCommunitySummaryUserPrompt(members, reportsConfig.MaxLength),
                        cancellationToken).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    logger?.LogWarning(ex, "Failed to generate community summary for community {CommunityId}", index + 1);
                }

                if (string.IsNullOrWhiteSpace(summary))
                {
                    summary = BuildFallbackSummary(members);
                }

                var keywords = ExtractKeywords(summary);
                reports.Add(new CommunityReportRecord(
                    CommunityId: $"community_{community.CommunityId}",
                    Level: 0,
                    EntityTitles: members.Select(static e => e.Title).ToArray(),
                    Summary: summary.Trim(),
                    Keywords: keywords));
            }

            await context.OutputStorage
                .WriteTableAsync(PipelineTableNames.CommunityReports, reports, cancellationToken)
                .ConfigureAwait(false);

            context.Items["community_reports:count"] = reports.Count;
            return new WorkflowResult(reports);
        };
    }

    private static IReadOnlyList<string> ExtractKeywords(string summary)
    {
        if (string.IsNullOrWhiteSpace(summary))
        {
            return Array.Empty<string>();
        }

        var tokens = summary
            .Split(new[] { ' ', '\n', '\r', '\t', '.', ',', ';', ':', '!' }, StringSplitOptions.RemoveEmptyEntries)
            .Select(static token => token.Trim('"', '\'', '(', ')', '[', ']', '{', '}', '#', '*', '`'))
            .Where(token => token.Length > 2 && token.Any(char.IsLetterOrDigit))
            .Select(token => token.ToLowerInvariant());

        return tokens
            .GroupBy(token => token, StringComparer.OrdinalIgnoreCase)
            .OrderByDescending(group => group.Count())
            .ThenBy(group => group.Key, StringComparer.OrdinalIgnoreCase)
            .Take(10)
            .Select(group => group.Key)
            .ToArray();
    }

    private static async Task<string> GenerateCommunitySummaryAsync(
        IChatClient? chatClient,
        string systemPrompt,
        string userPrompt,
        CancellationToken cancellationToken)
    {
        if (chatClient is null)
        {
            return string.Empty;
        }

        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, systemPrompt),
            new(ChatRole.User, userPrompt)
        };

        var response = await chatClient.GetResponseAsync(messages, cancellationToken: cancellationToken).ConfigureAwait(false);
        return response.Text ?? string.Empty;
    }

    private static IChatClient? ResolveChatClient(IServiceProvider services, string? modelId, ILogger? logger)
    {
        IChatClient? chatClient = null;

        if (!string.IsNullOrWhiteSpace(modelId))
        {
            chatClient = services.GetKeyedService<IChatClient>(modelId);
            if (chatClient is null)
            {
                logger?.LogWarning("GraphRAG could not resolve keyed chat client '{ModelId}'. Falling back to default chat client registration.", modelId);
            }
        }

        return chatClient ?? services.GetService<IChatClient>();
    }

    private static string BuildFallbackSummary(IEnumerable<EntityRecord> community)
    {
        var builder = new StringBuilder();
        builder.Append("Community containing: ");
        builder.Append(string.Join(", ", community.Select(static e => e.Title)));
        builder.Append(". Relationships indicate shared context across the documents.");
        return builder.ToString();
    }
}
