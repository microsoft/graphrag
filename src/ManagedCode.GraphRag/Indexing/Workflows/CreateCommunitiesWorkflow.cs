using GraphRag.Community;
using GraphRag.Config;
using GraphRag.Constants;
using GraphRag.Entities;
using GraphRag.Indexing.Runtime;
using GraphRag.Relationships;
using GraphRag.Storage;

namespace GraphRag.Indexing.Workflows;

internal static class CreateCommunitiesWorkflow
{
    public const string Name = "create_communities";

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
                    .WriteTableAsync(PipelineTableNames.Communities, Array.Empty<CommunityRecord>(), cancellationToken)
                    .ConfigureAwait(false);
                return new WorkflowResult(Array.Empty<CommunityRecord>());
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

            var clusterConfig = config.ClusterGraph ?? new ClusterGraphConfig();
            var communities = CommunityBuilder.Build(entities, relationships, clusterConfig);

            await context.OutputStorage
                .WriteTableAsync(PipelineTableNames.Communities, communities, cancellationToken)
                .ConfigureAwait(false);

            context.Items["create_communities:count"] = communities.Count;
            return new WorkflowResult(communities);
        };
    }
}
