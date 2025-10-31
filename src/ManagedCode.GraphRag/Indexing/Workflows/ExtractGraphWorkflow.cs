using System.Text.Json;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Data;
using GraphRag.Entities;
using GraphRag.Finalization;
using GraphRag.Indexing.Heuristics;
using GraphRag.Indexing.Runtime;
using GraphRag.LanguageModels;
using GraphRag.Relationships;
using GraphRag.Storage;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Indexing.Workflows;

internal static class ExtractGraphWorkflow
{
    public const string Name = "extract_graph";

    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private const string EntityCountKey = "extract_graph:entity_count";
    private const string RelationshipCountKey = "extract_graph:relationship_count";

    public static WorkflowDelegate Create()
    {
        return async (config, context, cancellationToken) =>
        {
            var textUnits = await context.OutputStorage
                .LoadTableAsync<TextUnitRecord>(PipelineTableNames.TextUnits, cancellationToken)
                .ConfigureAwait(false);

            if (textUnits.Count == 0)
            {
                return new WorkflowResult(Array.Empty<EntityRecord>());
            }

            var loggerFactory = context.Services.GetService<ILoggerFactory>();
            var logger = loggerFactory?.CreateLogger(typeof(ExtractGraphWorkflow));

            var extractionConfig = config.ExtractGraph ?? new ExtractGraphConfig();
            var allowedTypes = extractionConfig.EntityTypes ?? new List<string>();
            var entityAggregator = new EntityAggregator();
            var relationshipAggregator = new RelationshipAggregator();

            var chatClient = ResolveChatClient(context.Services, extractionConfig.ModelId, logger);
            var promptLoader = PromptTemplateLoader.Create(config);
            var systemPrompt = promptLoader.ResolveOrDefault(
                PromptTemplateKeys.ExtractGraphSystem,
                extractionConfig.SystemPrompt,
                GraphRagPromptLibrary.ExtractGraphSystemPrompt);
            var userPromptTemplate = promptLoader.ResolveOptional(
                PromptTemplateKeys.ExtractGraphUser,
                extractionConfig.Prompt);

            foreach (var unit in textUnits)
            {
                cancellationToken.ThrowIfCancellationRequested();

                if (string.IsNullOrWhiteSpace(unit.Text))
                {
                    continue;
                }

                try
                {
                    var extraction = await GenerateExtractionAsync(
                        chatClient,
                        systemPrompt,
                        GraphRagPromptLibrary.BuildExtractGraphUserPrompt(
                            unit.Text,
                            Math.Max(1, allowedTypes.Count + 5),
                            userPromptTemplate),
                        logger,
                        cancellationToken).ConfigureAwait(false);

                    if (extraction is null)
                    {
                        continue;
                    }

                    foreach (var entity in extraction.Entities)
                    {
                        if (IsEntityTypeAllowed(entity.Type, allowedTypes))
                        {
                            entityAggregator.AddOrUpdate(entity, unit.Id);
                        }
                    }

                    foreach (var relationship in extraction.Relationships)
                    {
                        relationshipAggregator.AddOrUpdate(relationship, unit.Id);
                    }
                }
                catch (Exception ex)
                {
                    logger?.LogWarning(ex, "Failed to extract graph information from text unit {TextUnitId}", unit.Id);
                }
            }

            var entitySeeds = entityAggregator.ToSeeds().ToList();
            var relationshipSeeds = relationshipAggregator.ToSeeds().ToList();

            var heuristics = config.Heuristics ?? new HeuristicMaintenanceConfig();
            if ((heuristics.EnhanceRelationships && relationshipSeeds.Count > 0) || heuristics.LinkOrphanEntities)
            {
                var adjusted = GraphExtractionHeuristics.Apply(entitySeeds, relationshipSeeds, textUnits, heuristics, logger);
                entitySeeds = adjusted.Entities.ToList();
                relationshipSeeds = adjusted.Relationships.ToList();
            }

            var finalization = GraphFinalizer.Finalize(entitySeeds, relationshipSeeds);

            await context.OutputStorage
                .WriteTableAsync(PipelineTableNames.Entities, finalization.Entities, cancellationToken)
                .ConfigureAwait(false);
            await context.OutputStorage
                .WriteTableAsync(PipelineTableNames.Relationships, finalization.Relationships, cancellationToken)
                .ConfigureAwait(false);

            context.Items[EntityCountKey] = finalization.Entities.Count;
            context.Items[RelationshipCountKey] = finalization.Relationships.Count;

            return new WorkflowResult(finalization.Entities);
        };
    }

    private static bool IsEntityTypeAllowed(string? entityType, IReadOnlyCollection<string> allowedTypes)
    {
        if (allowedTypes.Count == 0 || string.IsNullOrWhiteSpace(entityType))
        {
            return true;
        }

        return allowedTypes.Contains(entityType, StringComparer.OrdinalIgnoreCase);
    }

    private static ExtractionResponse? ParseResponse(string payload, ILogger? logger)
    {
        try
        {
            var response = JsonSerializer.Deserialize<ExtractionResponse>(payload, SerializerOptions);
            if (response is null)
            {
                return null;
            }

            response.Entities.RemoveAll(static entity => string.IsNullOrWhiteSpace(entity.Title));
            response.Relationships.RemoveAll(static rel => string.IsNullOrWhiteSpace(rel.Source) || string.IsNullOrWhiteSpace(rel.Target));
            return response;
        }
        catch (JsonException ex)
        {
            logger?.LogWarning(ex, "Unable to parse extraction payload: {Payload}", payload);
            return null;
        }
    }

    private sealed class EntityAggregator
    {
        private readonly Dictionary<string, EntityAggregation> _entities = new(StringComparer.OrdinalIgnoreCase);

        public void AddOrUpdate(RawEntity entity, string textUnitId)
        {
            if (!_entities.TryGetValue(entity.Title, out var aggregation))
            {
                aggregation = new EntityAggregation(entity.Title, entity.Type ?? "other");
                _entities[entity.Title] = aggregation;
            }

            aggregation.Increment(textUnitId, entity.Description, entity.Confidence);
        }

        public IEnumerable<EntitySeed> ToSeeds()
        {
            return _entities.Values.Select(static entity => entity.ToSeed());
        }

        private sealed class EntityAggregation(string title, string type)
        {
            private readonly HashSet<string> _textUnitIds = new(StringComparer.OrdinalIgnoreCase);
            private readonly string _title = title;
            private readonly string _type = string.IsNullOrWhiteSpace(type) ? "other" : type;

            private double _confidenceSum;
            private int _occurrences;
            private string? _bestDescription;

            public void Increment(string textUnitId, string? description, double? confidence)
            {
                if (!string.IsNullOrWhiteSpace(textUnitId))
                {
                    _textUnitIds.Add(textUnitId);
                }

                if (!string.IsNullOrWhiteSpace(description) &&
                    (string.IsNullOrWhiteSpace(_bestDescription) || description.Length < _bestDescription!.Length))
                {
                    _bestDescription = description;
                }

                _occurrences++;
                _confidenceSum += confidence.GetValueOrDefault(0.6);
            }

            public EntitySeed ToSeed()
            {
                _ = _occurrences > 0 ? Math.Clamp(_confidenceSum / _occurrences, 0.0, 1.0) : 0.6;
                var description = _bestDescription ?? $"Entity {_title}";

                return new EntitySeed(
                    _title,
                    _type,
                    description,
                    _textUnitIds.ToArray(),
                    Frequency: Math.Max(1, _occurrences))
                {
                    // We encode confidence inside description metadata; consumers can derive additional stats if required.
                };
            }
        }
    }

    private sealed class RelationshipAggregator
    {
        private readonly Dictionary<string, RelationshipAggregation> _relationships = new(StringComparer.OrdinalIgnoreCase);

        public void AddOrUpdate(RawRelationship relationship, string textUnitId)
        {
            if (string.IsNullOrWhiteSpace(relationship.Source) || string.IsNullOrWhiteSpace(relationship.Target))
            {
                return;
            }

            var key = $"{relationship.Source}::{relationship.Target}::{relationship.Type ?? relationship.Description ?? string.Empty}";
            if (!_relationships.TryGetValue(key, out var aggregation))
            {
                aggregation = new RelationshipAggregation(relationship.Source, relationship.Target, relationship.Description, relationship.Type, relationship.Bidirectional);
                _relationships[key] = aggregation;
            }

            aggregation.Increment(textUnitId, relationship.Weight);
        }

        public IEnumerable<RelationshipSeed> ToSeeds()
        {
            return _relationships.Values.Select(static rel => rel.ToSeed());
        }

        private sealed class RelationshipAggregation(string source, string target, string? description, string? type, bool bidirectional)
        {
            private readonly HashSet<string> _textUnitIds = new(StringComparer.OrdinalIgnoreCase);
            private readonly string _source = source;
            private readonly string _target = target;
            private readonly string _description = string.IsNullOrWhiteSpace(description)
                    ? $"{source} relates to {target}"
                    : description!;
            private readonly string _type = string.IsNullOrWhiteSpace(type) ? "related_to" : type!;
            private readonly bool _bidirectional = bidirectional;

            private double _weightSum;
            private int _occurrences;

            public void Increment(string textUnitId, double? weight)
            {
                if (!string.IsNullOrWhiteSpace(textUnitId))
                {
                    _textUnitIds.Add(textUnitId);
                }

                _occurrences++;
                _weightSum += weight.GetValueOrDefault(0.5);
            }

            public RelationshipSeed ToSeed()
            {
                var averageWeight = _occurrences > 0 ? Math.Clamp(_weightSum / _occurrences, 0.0, 1.0) : 0.5;
                return new RelationshipSeed(
                    _source,
                    _target,
                    _description,
                    averageWeight,
                    _textUnitIds.ToArray())
                {
                    Type = _type,
                    Bidirectional = _bidirectional
                };
            }
        }
    }

    private sealed class ExtractionResponse
    {
        public List<RawEntity> Entities { get; set; } = new();

        public List<RawRelationship> Relationships { get; set; } = new();
    }

    private sealed class RawEntity
    {
        public string Title { get; set; } = string.Empty;

        public string? Type { get; set; }
            = "other";

        public string? Description { get; set; }

        public double? Confidence { get; set; }
            = 0.6;
    }

    private sealed class RawRelationship
    {
        public string Source { get; set; } = string.Empty;

        public string Target { get; set; } = string.Empty;

        public string? Type { get; set; }

        public string? Description { get; set; }

        public double? Weight { get; set; }

        public bool Bidirectional { get; set; }
    }

    private static async Task<ExtractionResponse?> GenerateExtractionAsync(
        IChatClient? chatClient,
        string systemPrompt,
        string userPrompt,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        if (chatClient is null)
        {
            return null;
        }

        var messages = new List<ChatMessage>
        {
            new(ChatRole.System, systemPrompt),
            new(ChatRole.User, userPrompt)
        };

        var response = await chatClient
            .GetResponseAsync<ExtractionResponse>(messages, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        if (response.TryGetResult(out var typedResult) && typedResult is not null)
        {
            typedResult.Entities ??= new();
            typedResult.Relationships ??= new();
            return typedResult;
        }

        if (!string.IsNullOrWhiteSpace(response.Text))
        {
            return ParseResponse(response.Text, logger);
        }

        logger?.LogWarning("Graph extraction response did not include structured content.");
        return null;
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
}
