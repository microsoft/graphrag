using System;
using Aspire.Hosting;
using Aspire.Hosting.Testing;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

namespace ManagedCode.GraphRag.Tests.Integration;

public sealed class GraphRagApplicationFixture : IAsyncLifetime
{
    private AsyncServiceScope _scope;

    public DistributedApplication Application { get; private set; } = null!;

    public IServiceProvider Services => _scope.ServiceProvider;

    public async Task InitializeAsync()
    {
        var builder = await DistributedApplicationTestingBuilder.CreateAsync<GraphRagApplicationFixture>().ConfigureAwait(false);
        GraphRagAspireAppHost.Configure((IDistributedApplicationBuilder)builder);

        Application = await builder.BuildAsync().ConfigureAwait(false);
        await Application.StartAsync().ConfigureAwait(false);

        _scope = Application.Services.CreateAsyncScope();
    }

    public async Task DisposeAsync()
    {
        await _scope.DisposeAsync().ConfigureAwait(false);
        await Application.DisposeAsync().ConfigureAwait(false);
    }
}
