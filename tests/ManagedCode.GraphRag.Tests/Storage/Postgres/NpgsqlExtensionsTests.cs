using Npgsql;

namespace ManagedCode.GraphRag.Tests.Storage.Postgres;

public sealed class NpgsqlExtensionsTests
{
    [Fact]
    public void UseAge_ReturnsSameMapper()
    {
#pragma warning disable CS0618
        var mapper = NpgsqlConnection.GlobalTypeMapper;
        var returned = mapper.UseAge();
#pragma warning restore CS0618
        Assert.Same(mapper, returned);
    }
}
