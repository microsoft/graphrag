using GraphRag.Storage.Postgres.ApacheAge.Resolvers;
using Npgsql.TypeMapping;

namespace Npgsql;

public static class NpgsqlExtensions
{
    /// <summary>
    /// Use Apache AGE types.
    /// </summary>
    /// <param name="mapper">Npgsql type mapper.</param>
    /// <returns></returns>
    public static INpgsqlTypeMapper UseAge(this INpgsqlTypeMapper mapper)
    {
        mapper.AddTypeInfoResolverFactory(new AgtypeResolverFactory());
        return mapper;
    }
}
