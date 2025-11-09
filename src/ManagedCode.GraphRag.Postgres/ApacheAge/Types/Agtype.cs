using System.Globalization;
using System.Text.Json;
using GraphRag.Storage.Postgres.ApacheAge.JsonConverters;

namespace GraphRag.Storage.Postgres.ApacheAge.Types;

/// <summary>
/// Represent the <c>ag_catalog.agtype</c> PostgreSQL type.
/// </summary>
/// <remarks>
/// Initialises a new instance of <see cref="Agtype"/>.
/// </remarks>
/// <param name="value"></param>
public readonly struct Agtype(string value)
{
    private readonly string _value = value;

    #region Public methods
    /// <summary>
    /// Return the agtype value as a string.
    /// </summary>
    /// <returns>
    /// String value.
    /// </returns>
    public string GetString() => _value;

    /// <summary>
    /// Return the agtype value as a boolean.
    /// </summary>
    /// <returns>
    /// Boolean value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public bool GetBoolean() => bool.Parse(_value);

    /// <summary>
    /// Return the agtype value as a float.
    /// </summary>
    /// <returns>
    /// Float value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public float GetFloat()
    {
        if (_value.Equals("-Infinity", StringComparison.OrdinalIgnoreCase))
        {
            return float.NegativeInfinity;
        }

        if (_value.Equals("Infinity", StringComparison.OrdinalIgnoreCase))
        {
            return float.PositiveInfinity;
        }

        if (_value.Equals("NaN", StringComparison.OrdinalIgnoreCase))
        {
            return float.NaN;
        }

        return float.Parse(_value, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Return the agtype value as a double.
    /// </summary>
    /// <returns>
    /// Double value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public double GetDouble()
    {
        if (_value.Equals("-Infinity", StringComparison.OrdinalIgnoreCase))
        {
            return double.NegativeInfinity;
        }

        if (_value.Equals("Infinity", StringComparison.OrdinalIgnoreCase))
        {
            return double.PositiveInfinity;
        }

        if (_value.Equals("NaN", StringComparison.OrdinalIgnoreCase))
        {
            return double.NaN;
        }

        return double.Parse(_value, CultureInfo.InvariantCulture);
    }

    /// <summary>
    /// Return the agtype value as a byte.
    /// </summary>
    /// <returns>
    /// Byte value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public byte GetByte() => byte.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as an sbyte.
    /// </summary>
    /// <returns>
    /// SByte value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public sbyte GetSByte() => sbyte.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a short.
    /// </summary>
    /// <returns>
    /// Short value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public short GetInt16() => short.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a ushort.
    /// </summary>
    /// <returns>
    /// UShort value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public ushort GetUInt16() => ushort.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as an integer.
    /// </summary>
    /// <returns>
    /// Integer value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public int GetInt32() => int.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a uint.
    /// </summary>
    /// <returns>
    /// UInt value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public uint GetUInt32() => uint.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a long.
    /// </summary>
    /// <returns>
    /// Long value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public long GetInt64() => long.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a ulong.
    /// </summary>
    /// <returns>
    /// ULong value.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the value of the agtype cannot be correctly parsed.
    /// </exception>
    public ulong GetUInt64() => ulong.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a decimal.
    /// </summary>
    /// <returns>
    /// Decimal value.
    /// </returns>
    public decimal GetDecimal() => decimal.Parse(_value, CultureInfo.InvariantCulture);

    /// <summary>
    /// Return the agtype value as a list.
    /// </summary>
    /// 
    /// <remarks>
    /// The list may contain mixed data types.
    /// Example: [1, 2, "string", null].
    /// </remarks>
    /// 
    /// <param name="readFloatingPointLiterals">
    /// Indicates if the reserved floating values "-Infinity", "Infinity",
    /// and "NaN" should be parsed to <see cref="double.NegativeInfinity"/>,
    /// <see cref="double.PositiveInfinity"/>, and <see cref="double.NaN"/>
    /// respectively.
    /// <para>
    /// If <see langword="false"/>, the reserved floating values are parsed as
    /// strings.
    /// </para>
    /// </param>
    /// 
    /// <returns>
    /// List of objects.
    /// </returns>
    public List<object?> GetList(bool readFloatingPointLiterals = true)
    {
        var result = JsonSerializer.Deserialize<List<object?>>(_value, SerializerOptions.Default);

        return result!;
    }

    /// <summary>
    /// Return the agtype value as a <see cref="Vertex"/>.
    /// </summary>
    /// <returns>
    /// Vertex.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the agtype cannot be converted to a vertex.
    /// </exception>
    public Vertex GetVertex()
    {
        var isValidVertex = _value.EndsWith(Vertex.FOOTER);
        if (!isValidVertex)
        {
            throw new FormatException("Cannot convert agtype to vertex. Agtype is not a valid vertex.");
        }

        var json = _value.Replace(Vertex.FOOTER, "");
        var vertex = JsonSerializer.Deserialize<Vertex>(json, SerializerOptions.Default);

        return vertex!;
    }

    /// <summary>
    /// Return the agtype value as a <see cref="Edge"/>.
    /// </summary>
    /// <returns>
    /// Edge.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the agtype cannot be converted to an edge.
    /// </exception>
    public Edge GetEdge()
    {
        var isValidEdge = _value.EndsWith(Edge.FOOTER);
        if (!isValidEdge)
        {
            throw new FormatException("Cannot convert agtype to edge. Agtype is not a valid edge.");
        }

        var json = _value.Replace(Edge.FOOTER, "");
        var edge = JsonSerializer.Deserialize<Edge>(json, SerializerOptions.Default);

        return edge!;
    }

    /// <summary>
    /// Return the agtype value as a path containing vertices and edges.
    /// </summary>
    /// <returns>
    /// A <see cref="Path"/>.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown when the agtype cannot be converted to a path.
    /// </exception>
    public Path GetPath()
    {
        var isValidEdge = _value.EndsWith(Path.FOOTER);
        if (!isValidEdge)
        {
            throw new FormatException("Cannot convert agtype to path. Agtype is not a valid path.");
        }

        try
        {
            var json = _value
                .Replace(Vertex.FOOTER, "")
                .Replace(Path.FOOTER, "")
                .Replace(Edge.FOOTER, "");
            var path = JsonSerializer.Deserialize<object[]>(json, SerializerOptions.PathSerializer);

            return path is null
                ? throw new AgeException("Path cannot be null.")
                : new Path(path);
        }
        catch (JsonException e)
        {
            throw new FormatException("Path may be in the wrong format and cannot be parsed correctly.", e);
        }
    }
    #endregion

    #region Explicit operators
    public static explicit operator byte(Agtype agtype) => agtype.GetByte();

    public static explicit operator sbyte(Agtype agtype) => agtype.GetSByte();

    public static explicit operator short(Agtype agtype) => agtype.GetInt16();

    public static explicit operator ushort(Agtype agtype) => agtype.GetUInt16();

    public static explicit operator int(Agtype agtype) => agtype.GetInt32();

    public static explicit operator uint(Agtype agtype) => agtype.GetUInt32();

    public static explicit operator long(Agtype agtype) => agtype.GetInt64();

    public static explicit operator ulong(Agtype agtype) => agtype.GetUInt64();

    public static explicit operator decimal(Agtype agtype) => agtype.GetDecimal();

    public static explicit operator float(Agtype agtype) => agtype.GetFloat();

    public static explicit operator double(Agtype agtype) => agtype.GetDouble();

    public static explicit operator string(Agtype agtype) => agtype.GetString();

    public static explicit operator List<object?>(Agtype agtype) => agtype.GetList();

    public static explicit operator Vertex(Agtype agtype) => agtype.GetVertex();

    public static explicit operator Edge(Agtype agtype) => agtype.GetEdge();
    #endregion

}
