using System;
using System.Collections.Generic;
using Aspire.Hosting;
using GraphRag.Core;
using GraphRag.Graphs;
using GraphRag.Storage.Cosmos;
using GraphRag.Storage.Neo4j;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.DependencyInjection;

namespace GraphRag.Tests.Integration;

public static class GraphRagAspireAppHost
{
    public static void Configure(IDistributedApplicationBuilder builder)
    {
        builder.AddContainer("neo4j", "neo4j", tag: "5")
            .WithEndpoint(targetPort: 7687, port: 7687, scheme: "bolt", name: "bolt", env: "NEO4J_BOLT_URI", isProxied: false)
            .WithEnvironment("NEO4J_AUTH", "neo4j/test");

        builder.AddContainer("postgres", "postgres", tag: "16-alpine")
            .WithEnvironment("POSTGRES_USER", "postgres")
            .WithEnvironment("POSTGRES_PASSWORD", "postgres")
            .WithEnvironment("POSTGRES_DB", "graphrag")
            .WithEndpoint(targetPort: 5432, port: 5432, scheme: "tcp", name: "postgres", isProxied: false);

        var cosmosConnectionString = Environment.GetEnvironmentVariable("COSMOS_EMULATOR_CONNECTION_STRING");
        var includeCosmos = !string.IsNullOrWhiteSpace(cosmosConnectionString);

        builder.Services.AddGraphRagCore(steps =>
        {
            steps.AddStep("neo4j-seed", async (context, token) =>
            {
                var graph = context.Services.GetRequiredKeyedService<IGraphStore>("neo4j");
                await graph.InitializeAsync(token);
                await graph.UpsertNodeAsync("alice", "Person", new Dictionary<string, object?> { ["name"] = "Alice" }, token);
                await graph.UpsertNodeAsync("bob", "Person", new Dictionary<string, object?> { ["name"] = "Bob" }, token);
                await graph.UpsertRelationshipAsync("alice", "bob", "KNOWS", new Dictionary<string, object?> { ["since"] = 2024 }, token);
                var relationships = new List<GraphRelationship>();
                await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("alice", token))
                {
                    relationships.Add(relationship);
                }

                context.Items["neo4j:relationship-count"] = relationships.Count;
            });

            steps.AddStep("postgres-seed", async (context, token) =>
            {
                var graph = context.Services.GetRequiredKeyedService<IGraphStore>("postgres");
                await graph.InitializeAsync(token);
                await graph.UpsertNodeAsync("chapter-1", "Chapter", new Dictionary<string, object?> { ["title"] = "Origins" }, token);
                await graph.UpsertNodeAsync("chapter-2", "Chapter", new Dictionary<string, object?> { ["title"] = "Discovery" }, token);
                await graph.UpsertRelationshipAsync("chapter-1", "chapter-2", "LEADS_TO", new Dictionary<string, object?> { ["weight"] = 0.9 }, token);
                var relationships = new List<GraphRelationship>();
                await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("chapter-1", token))
                {
                    relationships.Add(relationship);
                }

                context.Items["postgres:relationship-count"] = relationships.Count;
            });

            if (includeCosmos)
            {
                steps.AddStep("cosmos-seed", async (context, token) =>
                {
                    var graph = context.Services.GetRequiredKeyedService<IGraphStore>("cosmos");
                    await graph.InitializeAsync(token);
                    await graph.UpsertNodeAsync("c1", "Content", new Dictionary<string, object?> { ["title"] = "Doc" }, token);
                    await graph.UpsertNodeAsync("c2", "Content", new Dictionary<string, object?> { ["title"] = "Attachment" }, token);
                    await graph.UpsertRelationshipAsync("c1", "c2", "EMBEDS", new Dictionary<string, object?> { ["score"] = 0.42 }, token);
                    var relationships = new List<GraphRelationship>();
                    await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("c1", token))
                    {
                        relationships.Add(relationship);
                    }

                    context.Items["cosmos:relationship-count"] = relationships.Count;
                });
            }
        });

        builder.Services.AddNeo4jGraphStore("neo4j", options =>
        {
            options.Uri = "bolt://localhost:7687";
            options.Username = "neo4j";
            options.Password = "test";
        }, makeDefault: true);

        builder.Services.AddPostgresGraphStore("postgres", options =>
        {
            options.ConnectionString = "Host=localhost;Port=5432;Username=postgres;Password=postgres;Database=graphrag";
        });

        if (includeCosmos)
        {
            builder.Services.AddCosmosGraphStore("cosmos", options =>
            {
                options.ConnectionString = cosmosConnectionString!;
                options.DatabaseId = "GraphRagIntegration";
                options.NodesContainerId = "nodes";
                options.EdgesContainerId = "edges";
            });
        }
    }
}
