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

            var logger = context.Services.GetService<ILoggerFactory>()?.CreateLogger(typeof(CommunitySummariesWorkflow));
            var reportsConfig = config.CommunityReports ?? new CommunityReportsConfig();
            var chatClient = ResolveChatClient(context.Services, reportsConfig.ModelId, logger);
            var communities = DetectCommunities(entities, relationships);
            var reports = new List<CommunityReportRecord>(communities.Count);

            for (var index = 0; index < communities.Count; index++)
            {
                cancellationToken.ThrowIfCancellationRequested();

                var community = communities[index];
                var summary = string.Empty;

                try
                {
                    summary = await GenerateCommunitySummaryAsync(
                        chatClient,
                        GraphRagPromptLibrary.CommunitySummarySystemPrompt,
                        GraphRagPromptLibrary.BuildCommunitySummaryUserPrompt(community, reportsConfig.MaxLength),
                        cancellationToken).ConfigureAwait(false);
                }
                catch (Exception ex)
                {
                    logger?.LogWarning(ex, "Failed to generate community summary for community {CommunityId}", index + 1);
                }

                if (string.IsNullOrWhiteSpace(summary))
                {
                    summary = BuildFallbackSummary(community);
                }

                var keywords = ExtractKeywords(summary);
                reports.Add(new CommunityReportRecord(
                    CommunityId: $"community_{index + 1}",
                    Level: 0,
                    EntityTitles: community.Select(static e => e.Title).ToArray(),
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

    private static List<IReadOnlyList<EntityRecord>> DetectCommunities(
        IReadOnlyList<EntityRecord> entities,
        IReadOnlyList<RelationshipRecord> relationships)
    {
        var adjacency = new Dictionary<string, HashSet<string>>(StringComparer.OrdinalIgnoreCase);
        foreach (var entity in entities)
        {
            adjacency.TryAdd(entity.Title, new HashSet<string>(StringComparer.OrdinalIgnoreCase));
        }

        foreach (var relationship in relationships)
        {
            if (!adjacency.TryGetValue(relationship.Source, out var sourceNeighbors))
            {
                sourceNeighbors = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                adjacency[relationship.Source] = sourceNeighbors;
            }

            if (!adjacency.TryGetValue(relationship.Target, out var targetNeighbors))
            {
                targetNeighbors = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                adjacency[relationship.Target] = targetNeighbors;
            }

            sourceNeighbors.Add(relationship.Target);
            targetNeighbors.Add(relationship.Source);
        }

        var entityLookup = entities.ToDictionary(entity => entity.Title, StringComparer.OrdinalIgnoreCase);
        var visited = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var communities = new List<IReadOnlyList<EntityRecord>>();

        foreach (var entity in entities)
        {
            if (!visited.Add(entity.Title))
            {
                continue;
            }

            var queue = new Queue<string>();
            queue.Enqueue(entity.Title);

            var members = new List<EntityRecord>();

            while (queue.Count > 0)
            {
                var current = queue.Dequeue();
                if (!entityLookup.TryGetValue(current, out var record))
                {
                    continue;
                }

                members.Add(record);

                if (!adjacency.TryGetValue(current, out var neighbors))
                {
                    continue;
                }

                foreach (var neighbor in neighbors)
                {
                    if (visited.Add(neighbor))
                    {
                        queue.Enqueue(neighbor);
                    }
                }
            }

            communities.Add(members);
        }

        return communities;
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
