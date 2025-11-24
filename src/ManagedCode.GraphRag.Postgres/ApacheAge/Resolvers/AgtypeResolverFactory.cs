using GraphRag.Storage.Postgres.ApacheAge.Converters;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using Npgsql.Internal;
using Npgsql.Internal.Postgres;

namespace GraphRag.Storage.Postgres.ApacheAge.Resolvers;

internal sealed class AgtypeResolverFactory : PgTypeInfoResolverFactory
{
    public override IPgTypeInfoResolver CreateResolver() => new Resolver();
    public override IPgTypeInfoResolver? CreateArrayResolver() => new ArrayResolver();

    private class Resolver : IPgTypeInfoResolver
    {
        protected static DataTypeName AgtypeDataTypeName => new("ag_catalog.agtype");

        private static readonly Lazy<TypeInfoMappingCollection> ResolverMappings = new(static () => AddMappings(new()));

        protected static TypeInfoMappingCollection BaseMappings => ResolverMappings.Value;

        protected static TypeInfoMappingCollection Mappings => BaseMappings;

        public PgTypeInfo? GetTypeInfo(Type? type, DataTypeName? dataTypeName, PgSerializerOptions options)
            => Mappings.Find(type, dataTypeName, options);

        private static TypeInfoMappingCollection AddMappings(TypeInfoMappingCollection mappings)
        {
            mappings.AddStructType<Agtype>(AgtypeDataTypeName,
                static (options, mapping, _) => mapping.CreateInfo(options, new AgtypeConverter()), MatchRequirement.DataTypeName);

            return mappings;
        }
    }

    private sealed class ArrayResolver : Resolver, IPgTypeInfoResolver
    {
        private static readonly Lazy<TypeInfoMappingCollection> ArrayMappings = new(static () => AddMappings(new(BaseMappings)));

        private static new TypeInfoMappingCollection Mappings => ArrayMappings.Value;

        public new PgTypeInfo? GetTypeInfo(Type? type, DataTypeName? dataTypeName, PgSerializerOptions options)
            => Mappings.Find(type, dataTypeName, options);

        private static TypeInfoMappingCollection AddMappings(TypeInfoMappingCollection mappings)
        {
            mappings.AddStructArrayType<Agtype>(AgtypeDataTypeName);

            return mappings;
        }
    }
}
