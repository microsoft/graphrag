using GraphRag.Storage.Postgres.ApacheAge.Resolvers;
using Npgsql.TypeMapping;

namespace Npgsql;

public static class NpgsqlExtensions
{
    public static INpgsqlTypeMapper UseAge(this INpgsqlTypeMapper mapper)
    {
        mapper.AddTypeInfoResolverFactory(new AgtypeResolverFactory());
        return mapper;
    }

    public static NpgsqlDataSourceBuilder UseAge(this NpgsqlDataSourceBuilder builder)
    {
        builder.AddTypeInfoResolverFactory(new AgtypeResolverFactory());
        return builder;
    }
}
