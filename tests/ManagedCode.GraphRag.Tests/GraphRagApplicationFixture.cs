using System.Runtime.InteropServices;
using DotNet.Testcontainers.Builders;
using DotNet.Testcontainers.Configurations;
using GraphRag;
using GraphRag.Storage.Cosmos;
using GraphRag.Storage.JanusGraph;
using GraphRag.Storage.Neo4j;
using GraphRag.Storage.Postgres;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Npgsql;
using Testcontainers.CosmosDb;
using Testcontainers.JanusGraph;
using Testcontainers.Neo4j;
using Testcontainers.PostgreSql;

namespace ManagedCode.GraphRag.Tests.Integration;

public sealed class GraphRagApplicationFixture : IAsyncLifetime
{
    private const string Neo4jPassword = "test1234";
    private const string PostgresPassword = "postgres";
    private const string PostgresDatabase = "graphragdb";
    private static readonly TimeSpan ContainerStartupTimeout = TimeSpan.FromMinutes(10);

    private ServiceProvider _serviceProvider = null!;
    private AsyncServiceScope? _scope;
    private Neo4jContainer? _neo4jContainer;
    private PostgreSqlContainer? _postgresContainer;
    private CosmosDbContainer? _cosmosContainer;
    private JanusGraphContainer? _janusContainer;

    public IServiceProvider Services => _scope?.ServiceProvider ?? throw new InvalidOperationException("The fixture has not been initialized.");
    public string PostgresConnectionString => _postgresContainer?.GetConnectionString() ?? throw new InvalidOperationException("PostgreSQL container is not available.");

    static GraphRagApplicationFixture()
    {
        if (TestcontainersSettings.WaitStrategyTimeout is null || TestcontainersSettings.WaitStrategyTimeout < ContainerStartupTimeout)
        {
            // Pulling these images can easily exceed the default timeout on fresh machines, so relax it globally.
            TestcontainersSettings.WaitStrategyTimeout = ContainerStartupTimeout;
        }
    }

    public async Task InitializeAsync()
    {
        Uri? boltEndpoint = null;
        string? postgresConnection = null;
        string? cosmosConnectionString = null;

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

        if (IsCosmosSupported())
        {
            _cosmosContainer = new CosmosDbBuilder()
                .WithImage("mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-preview")
                .Build();
        }

        if (IsJanusSupported())
        {
            _janusContainer = new JanusGraphBuilder().Build();
        }

        var startTasks = new List<Task>
        {
            _neo4jContainer.StartAsync(),
            _postgresContainer.StartAsync()
        };

        if (_cosmosContainer is not null)
        {
            startTasks.Add(_cosmosContainer.StartAsync());
        }

        if (_janusContainer is not null)
        {
            startTasks.Add(_janusContainer.StartAsync());
        }

        await Task.WhenAll(startTasks).ConfigureAwait(false);
        await EnsurePostgresDatabaseAsync().ConfigureAwait(false);

        boltEndpoint = new Uri(_neo4jContainer.GetConnectionString(), UriKind.Absolute);
        postgresConnection = _postgresContainer.GetConnectionString();
        cosmosConnectionString = _cosmosContainer?.GetConnectionString();

        var janusHost = _janusContainer?.Hostname;
        var janusPort = _janusContainer?.GetMappedPublicPort(8182);

        var configuration = new ConfigurationBuilder().AddInMemoryCollection().Build();

        var services = new ServiceCollection();
        services.AddSingleton<IConfiguration>(configuration);
        services.AddLogging();
        services.AddOptions();

        services.AddGraphRag();

        if (boltEndpoint is not null && postgresConnection is not null)
        {
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

        if (cosmosConnectionString is not null)
        {
            services.AddCosmosGraphStore("cosmos", options =>
            {
                options.ConnectionString = cosmosConnectionString;
                options.DatabaseId = "GraphRagIntegration";
                options.NodesContainerId = "nodes";
                options.EdgesContainerId = "edges";
            });
        }

        if (_janusContainer is not null && janusHost is not null && janusPort is not null)
        {
            services.AddJanusGraphStore("janus", options =>
            {
                options.Host = janusHost;
                options.Port = janusPort.Value;
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

        if (_cosmosContainer is not null)
        {
            await _cosmosContainer.DisposeAsync().ConfigureAwait(false);
        }

        if (_janusContainer is not null)
        {
            await _janusContainer.DisposeAsync().ConfigureAwait(false);
        }
    }

    private static bool IsJanusSupported()
    {
        var flag = Environment.GetEnvironmentVariable("GRAPH_RAG_ENABLE_JANUS");
        return string.Equals(flag, "true", StringComparison.OrdinalIgnoreCase);
    }

    private static bool IsCosmosSupported()
    {
        var flag = Environment.GetEnvironmentVariable("GRAPH_RAG_ENABLE_COSMOS");
        if (string.Equals(flag, "true", StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        return RuntimeInformation.ProcessArchitecture == Architecture.X64;
    }
}
