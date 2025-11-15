using GraphRag.Storage.Postgres.ApacheAge.Converters;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using Npgsql.Internal;
using Npgsql.Internal.Postgres;

namespace GraphRag.Storage.Postgres.ApacheAge.Resolvers;

#pragma warning disable NPG9001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
/// <summary>
/// Factory class to resolve type information and specify which converters should be used
/// to convert the PostgreSQL type 'ag_catalog.agtype' to our CLR <see cref="Agtype"/>.
/// </summary>
/// <remarks>
/// <seealso href="https://medium.com/@dsylebee/nethereums-bigdecimal-support-for-npgsql-c21ec48897de">
/// This article
/// </seealso> was of great help.
/// </remarks>
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
#pragma warning restore NPG9001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
