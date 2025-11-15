using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace GraphRag.Storage.Postgres.ApacheAge;

public interface IAgeClientFactory
{
    AgeClient CreateClient();
}

internal sealed class AgeClientFactory([FromKeyedServices] IAgeConnectionManager connectionManager, ILoggerFactory loggerFactory) : IAgeClientFactory
{
    private readonly IAgeConnectionManager _connectionManager = connectionManager ?? throw new ArgumentNullException(nameof(connectionManager));
    private readonly ILoggerFactory _loggerFactory = loggerFactory ?? throw new ArgumentNullException(nameof(loggerFactory));

    public AgeClient CreateClient()
    {
        var logger = _loggerFactory.CreateLogger<AgeClient>();
        return new AgeClient(_connectionManager, logger);
    }
}
