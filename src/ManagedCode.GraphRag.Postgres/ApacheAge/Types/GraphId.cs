using System.Diagnostics.CodeAnalysis;
using System.Globalization;

namespace GraphRag.Storage.Postgres.ApacheAge.Types;

/// <summary>
/// Represents the <c>ag_catalog.graphid</c> PostgreSQL type.
/// </summary>
/// <remarks>
/// Creates a new instance of <see cref="GraphId"/>.
/// </remarks>
/// <param name="value"></param>
public readonly struct GraphId(ulong value) : IComparable, IComparable<GraphId>
{

    /// <summary>
    /// Internal value of the graphid.
    /// </summary>
    public ulong Value { get; } = value;

    public int CompareTo(GraphId other)
    {
        if (this < other)
        {
            return -1;
        }

        if (this > other)
        {
            return 1;
        }

        return 0;
    }

    public int CompareTo(object? obj)
    {
        if (obj is null || obj is not GraphId)
        {
            throw new ArgumentException("obj is not a GraphId", nameof(obj));
        }

        return CompareTo((GraphId)obj);
    }

    public override bool Equals([NotNullWhen(true)] object? obj)
    {
        if (obj is null || obj is not GraphId)
        {
            return false;
        }

        var input = (GraphId)obj;

        return this == input;
    }

    public override int GetHashCode() => Value.GetHashCode();

    public override string ToString() => Value.ToString(CultureInfo.InvariantCulture);

    #region Operators
    public static bool operator <(GraphId left, GraphId right)
    {
        return left.Value < right.Value;
    }

    public static bool operator >(GraphId left, GraphId right)
    {
        return left.Value > right.Value;
    }

    public static bool operator <=(GraphId left, GraphId right)
    {
        return left.Value <= right.Value;
    }

    public static bool operator >=(GraphId left, GraphId right)
    {
        return left.Value >= right.Value;
    }

    public static bool operator ==(GraphId left, GraphId right)
    {
        return left.Value == right.Value;
    }

    public static bool operator !=(GraphId left, GraphId right)
    {
        return left.Value != right.Value;
    }
    #endregion
}
