using DotNet.Testcontainers.Builders;
using GraphRag;
using GraphRag.Graphs;
using GraphRag.Indexing.Runtime;
using GraphRag.Storage.Cosmos;
using GraphRag.Storage.Neo4j;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;
using Testcontainers.Neo4j;
using Testcontainers.PostgreSql;

namespace ManagedCode.GraphRag.Tests.Integration;

public sealed class GraphRagApplicationFixture : IAsyncLifetime
{
    private const string Neo4jPassword = "test1234";
    private const string PostgresPassword = "postgres";
    private const string PostgresDatabase = "graphragdb";

    private ServiceProvider _serviceProvider = null!;
    private AsyncServiceScope? _scope;
    private Neo4jContainer? _neo4jContainer;
    private PostgreSqlContainer? _postgresContainer;

    public IServiceProvider Services => _scope?.ServiceProvider ?? throw new InvalidOperationException("The fixture has not been initialized.");
    public string PostgresConnectionString => _postgresContainer?.GetConnectionString() ?? throw new InvalidOperationException("PostgreSQL container is not available.");

    public async Task InitializeAsync()
    {
        var skipContainers = string.Equals(
            Environment.GetEnvironmentVariable("GRAPHRAG_SKIP_TESTCONTAINERS"),
            "1",
            StringComparison.OrdinalIgnoreCase);

        Uri? boltEndpoint = null;
        string? postgresConnection = null;

        if (!skipContainers)
        {
            _neo4jContainer = new Neo4jBuilder()
                .WithImage("neo4j:5.23.0-community")
                .WithEnvironment("NEO4J_ACCEPT_LICENSE_AGREEMENT", "yes")
                .WithEnvironment("NEO4J_PLUGINS", "[\"apoc\"]")
                .WithEnvironment("NEO4J_dbms_default__listen__address", "0.0.0.0")
                .WithEnvironment("NEO4J_dbms_default__advertised__address", "localhost")
                .WithEnvironment("NEO4J_AUTH", $"neo4j/{Neo4jPassword}")
                .WithWaitStrategy(Wait.ForUnixContainer().UntilInternalTcpPortIsAvailable(7687))
                .Build();

            _postgresContainer = new PostgreSqlBuilder()
                .WithImage("apache/age:latest")
                .WithDatabase(PostgresDatabase)
                .WithUsername("postgres")
                .WithPassword(PostgresPassword)
                .WithCleanUp(true)
                .WithWaitStrategy(Wait.ForUnixContainer().UntilInternalTcpPortIsAvailable(5432))
                .Build();

            await Task.WhenAll(_neo4jContainer.StartAsync(), _postgresContainer.StartAsync()).ConfigureAwait(false);
            await EnsurePostgresDatabaseAsync().ConfigureAwait(false);

            boltEndpoint = new Uri(_neo4jContainer.GetConnectionString(), UriKind.Absolute);
            postgresConnection = _postgresContainer.GetConnectionString();
        }

        var cosmosConnectionString = Environment.GetEnvironmentVariable("COSMOS_EMULATOR_CONNECTION_STRING");
        var includeCosmos = !string.IsNullOrWhiteSpace(cosmosConnectionString);

        var configuration = new ConfigurationBuilder().AddInMemoryCollection().Build();

        var services = new ServiceCollection();
        services.AddSingleton<IConfiguration>(configuration);
        services.AddLogging();
        services.AddOptions();

        services.AddGraphRag();

        if (!skipContainers && boltEndpoint is not null && postgresConnection is not null)
        {
            services.AddKeyedSingleton<WorkflowDelegate>("neo4j-seed", static (_, _) => async (config, context, token) =>
            {
                var graph = context.Services.GetRequiredKeyedService<IGraphStore>("neo4j");
                await graph.InitializeAsync(token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("alice", "Person", new Dictionary<string, object?> { ["name"] = "Alice" }, token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("bob", "Person", new Dictionary<string, object?> { ["name"] = "Bob" }, token).ConfigureAwait(false);
                await graph.UpsertRelationshipAsync("alice", "bob", "KNOWS", new Dictionary<string, object?> { ["since"] = 2024 }, token).ConfigureAwait(false);
                var relationships = new List<GraphRelationship>();
                await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("alice", token).ConfigureAwait(false))
                {
                    relationships.Add(relationship);
                }

                context.Items["neo4j:relationship-count"] = relationships.Count;
                return new WorkflowResult(null);
            });

            services.AddKeyedSingleton<WorkflowDelegate>("postgres-seed", static (_, _) => async (config, context, token) =>
            {
                var graph = context.Services.GetRequiredKeyedService<IGraphStore>("postgres");
                await graph.InitializeAsync(token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("chapter-1", "Chapter", new Dictionary<string, object?> { ["title"] = "Origins" }, token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("chapter-2", "Chapter", new Dictionary<string, object?> { ["title"] = "Discovery" }, token).ConfigureAwait(false);
                await graph.UpsertRelationshipAsync("chapter-1", "chapter-2", "LEADS_TO", new Dictionary<string, object?> { ["weight"] = 0.9 }, token).ConfigureAwait(false);
                var relationships = new List<GraphRelationship>();
                await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("chapter-1", token).ConfigureAwait(false))
                {
                    relationships.Add(relationship);
                }

                context.Items["postgres:relationship-count"] = relationships.Count;
                return new WorkflowResult(null);
            });

            services.AddNeo4jGraphStore("neo4j", options =>
            {
                options.Uri = boltEndpoint.ToString();
                options.Username = "neo4j";
                options.Password = Neo4jPassword;
            });

            services.AddPostgresGraphStore("postgres", options =>
            {
                options.ConnectionString = ConfigurePostgresConnection(postgresConnection!);
                options.GraphName = "graphrag";
            });
        }

        if (includeCosmos)
        {
            services.AddKeyedSingleton<WorkflowDelegate>("cosmos-seed", static (_, _) => async (config, context, token) =>
            {
                var graph = context.Services.GetRequiredKeyedService<IGraphStore>("cosmos");
                await graph.InitializeAsync(token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("c1", "Content", new Dictionary<string, object?> { ["title"] = "Doc" }, token).ConfigureAwait(false);
                await graph.UpsertNodeAsync("c2", "Content", new Dictionary<string, object?> { ["title"] = "Attachment" }, token).ConfigureAwait(false);
                await graph.UpsertRelationshipAsync("c1", "c2", "EMBEDS", new Dictionary<string, object?> { ["score"] = 0.42 }, token).ConfigureAwait(false);
                var relationships = new List<GraphRelationship>();
                await foreach (var relationship in graph.GetOutgoingRelationshipsAsync("c1", token).ConfigureAwait(false))
                {
                    relationships.Add(relationship);
                }

                context.Items["cosmos:relationship-count"] = relationships.Count;
                return new WorkflowResult(null);
            });
        }

        if (includeCosmos)
        {
            services.AddCosmosGraphStore("cosmos", options =>
            {
                options.ConnectionString = cosmosConnectionString!;
                options.DatabaseId = "GraphRagIntegration";
                options.NodesContainerId = "nodes";
                options.EdgesContainerId = "edges";
            });
        }

        _serviceProvider = services.BuildServiceProvider();
        _scope = _serviceProvider.CreateAsyncScope();
    }

    private static string ConfigurePostgresConnection(string connectionString)
    {
        var builder = new NpgsqlConnectionStringBuilder(connectionString)
        {
            MaxPoolSize = 40,
            MinPoolSize = 10
        };

        return builder.ConnectionString;
    }

    private async Task EnsurePostgresDatabaseAsync()
    {
        if (_postgresContainer is null)
        {
            return;
        }

        var builder = new NpgsqlConnectionStringBuilder(_postgresContainer.GetConnectionString())
        {
            Database = "postgres"
        };

        await using var connection = new NpgsqlConnection(builder.ConnectionString);
        await connection.OpenAsync().ConfigureAwait(false);

        await using (var setLibraries = connection.CreateCommand())
        {
            setLibraries.CommandText = "ALTER SYSTEM SET shared_preload_libraries = 'age';";
            await setLibraries.ExecuteNonQueryAsync().ConfigureAwait(false);
        }

        await using (var reload = connection.CreateCommand())
        {
            reload.CommandText = "SELECT pg_reload_conf();";
            await reload.ExecuteNonQueryAsync().ConfigureAwait(false);
        }

        await using var createDatabase = connection.CreateCommand();
        createDatabase.CommandText = $"CREATE DATABASE \"{PostgresDatabase}\"";
        try
        {
            await createDatabase.ExecuteNonQueryAsync().ConfigureAwait(false);
        }
        catch (PostgresException ex) when (ex.SqlState == "42P04")
        {
            // database already exists
        }
    }

    public async Task DisposeAsync()
    {
        if (_scope is AsyncServiceScope scope)
        {
            await scope.DisposeAsync().ConfigureAwait(false);
            _scope = null;
        }

        if (_serviceProvider is not null)
        {
            await _serviceProvider.DisposeAsync().ConfigureAwait(false);
        }

        if (_neo4jContainer is not null)
        {
            await _neo4jContainer.DisposeAsync().ConfigureAwait(false);
        }

        if (_postgresContainer is not null)
        {
            await _postgresContainer.DisposeAsync().ConfigureAwait(false);
        }
    }
}
