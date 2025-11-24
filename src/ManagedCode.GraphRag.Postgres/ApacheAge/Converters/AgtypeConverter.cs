using System.Text;
using GraphRag.Storage.Postgres.ApacheAge.Types;
using Npgsql.Internal;

namespace GraphRag.Storage.Postgres.ApacheAge.Converters;

internal sealed class AgtypeConverter : PgBufferedConverter<Agtype>
{
    public override Size GetSize(SizeContext context, Agtype value, ref object? writeState)
    {
        var byteCount = Encoding.UTF8.GetByteCount(value.GetString());
        return byteCount;
    }

    public override bool CanConvert(DataFormat format, out BufferRequirements bufferRequirements)
    {
        bufferRequirements = BufferRequirements.None;
        return format is DataFormat.Text;
    }

    protected override Agtype ReadCore(PgReader reader)
    {
        var textBytes = reader.ReadBytes(reader.CurrentRemaining);
        var text = Encoding.UTF8.GetString(textBytes);

        return new(text);
    }

    protected override void WriteCore(PgWriter writer, Agtype value)
    {
        var bytes = Encoding.UTF8.GetBytes(value.GetString());
        writer.WriteBytes(bytes);
    }
}
