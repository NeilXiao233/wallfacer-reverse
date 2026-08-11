using System.Text;
using Il2CppDumper;

var fullDump = args.Contains("--full");
args = args.Where(a => a != "--full").ToArray();
if (args.Length < 2)
{
    Console.Error.WriteLine("usage: MetadataDump <global-metadata.dat> <output.json> [--full]");
    return 1;
}

using var fs = new FileStream(args[0], FileMode.Open, FileAccess.ReadWrite, FileShare.Read);
var metadata = new Metadata(fs);

var interesting = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
{
    "griddle", "level", "clue", "item", "puzzle", "cheer", "builder", "session",
    "decision", "downloader", "repository", "model", "config", "catalog", "saga",
    "grid", "column", "row", "hint", "mechanic", "logic"
};

var stringKeywords = new[]
{
    "level", "clue", "grid", "saga", "cheer", "cdn", "catalog", "difficulty",
    "tutorial", "hint", "eraser", "item", "column", "row", "complete", "reveal",
    "fail", "hash", "revision", "mechanic", "booster", "solution", "poster", "curtain"
};

var result = new Dictionary<string, object>
{
    ["metadataVersion"] = metadata.Version,
    ["assemblyCount"] = metadata.assemblyDefs.Length,
    ["imageCount"] = metadata.imageDefs.Length,
    ["typeCount"] = metadata.typeDefs.Length,
    ["methodCount"] = metadata.methodDefs.Length,
    ["fieldCount"] = metadata.fieldDefs.Length,
    ["propertyCount"] = metadata.propertyDefs.Length,
};

var types = new List<object>();
for (var imageIndex = 0; imageIndex < metadata.imageDefs.Length; imageIndex++)
{
    var image = metadata.imageDefs[imageIndex];
    var imageName = metadata.GetStringFromIndex(image.nameIndex);
    for (var typeIndex = image.typeStart; typeIndex < image.typeStart + image.typeCount; typeIndex++)
    {
        if (typeIndex < 0 || typeIndex >= metadata.typeDefs.Length)
        {
            continue;
        }
        var td = metadata.typeDefs[typeIndex];
        var ns = metadata.GetStringFromIndex(td.namespaceIndex);
        var name = metadata.GetStringFromIndex(td.nameIndex);
        var fullName = string.IsNullOrEmpty(ns) ? name : $"{ns}.{name}";
        if (!fullDump && !interesting.Any(term => fullName.Contains(term, StringComparison.OrdinalIgnoreCase)))
        {
            continue;
        }
        var parentName = td.parentIndex >= 0 && td.parentIndex < metadata.typeDefs.Length
            ? metadata.GetStringFromIndex(metadata.typeDefs[td.parentIndex].nameIndex)
            : "";
        var declaringName = td.declaringTypeIndex >= 0 && td.declaringTypeIndex < metadata.typeDefs.Length
            ? metadata.GetStringFromIndex(metadata.typeDefs[td.declaringTypeIndex].nameIndex)
            : "";

        var fields = new List<object>();
        for (var i = 0; i < td.field_count; i++)
        {
            var fieldIndex = td.fieldStart + i;
            if (fieldIndex < 0 || fieldIndex >= metadata.fieldDefs.Length)
            {
                continue;
            }
            var fd = metadata.fieldDefs[fieldIndex];
            fields.Add(new
            {
                index = fieldIndex,
                name = metadata.GetStringFromIndex(fd.nameIndex),
                typeIndex = fd.typeIndex,
                token = fd.token,
            });
        }

        var methods = new List<object>();
        for (var i = 0; i < td.method_count; i++)
        {
            var methodIndex = td.methodStart + i;
            if (methodIndex < 0 || methodIndex >= metadata.methodDefs.Length)
            {
                continue;
            }
            var md = metadata.methodDefs[methodIndex];
            var parameters = new List<object>();
            for (var p = 0; p < md.parameterCount; p++)
            {
                var parameterIndex = md.parameterStart + p;
                if (parameterIndex < 0 || parameterIndex >= metadata.parameterDefs.Length)
                {
                    continue;
                }
                var pd = metadata.parameterDefs[parameterIndex];
                parameters.Add(new
                {
                    index = parameterIndex,
                    name = metadata.GetStringFromIndex(pd.nameIndex),
                    typeIndex = pd.typeIndex,
                    token = pd.token,
                });
            }
            methods.Add(new
            {
                index = methodIndex,
                name = metadata.GetStringFromIndex(md.nameIndex),
                returnTypeIndex = md.returnType,
                flags = md.flags,
                iflags = md.iflags,
                slot = md.slot,
                token = md.token,
                parameters,
            });
        }

        var properties = new List<object>();
        for (var i = 0; i < td.property_count; i++)
        {
            var propertyIndex = td.propertyStart + i;
            if (propertyIndex < 0 || propertyIndex >= metadata.propertyDefs.Length)
            {
                continue;
            }
            var pd = metadata.propertyDefs[propertyIndex];
            properties.Add(new
            {
                index = propertyIndex,
                name = metadata.GetStringFromIndex(pd.nameIndex),
                get = pd.get,
                set = pd.set,
                attrs = pd.attrs,
                token = pd.token,
            });
        }

        types.Add(new
        {
            image = imageName,
            imageIndex,
            typeIndex,
            name = fullName,
            simpleName = name,
            namespaceName = ns,
            parent = parentName,
            declaringType = declaringName,
            flags = td.flags,
            token = td.token,
            isValueType = td.IsValueType,
            isEnum = td.IsEnum,
            fieldCount = td.field_count,
            methodCount = td.method_count,
            propertyCount = td.property_count,
            fields,
            methods,
            properties,
        });
    }
}

result["types"] = types;
if (!fullDump)
{
    var literals = new List<object>();
    for (var i = 0; i < metadata.stringLiterals.Length; i++)
    {
        try
        {
            var literal = metadata.GetStringLiteralFromIndex((uint)i);
            if (stringKeywords.Any(keyword => literal.Contains(keyword, StringComparison.OrdinalIgnoreCase)))
            {
                literals.Add(new { index = i, value = literal });
            }
        }
        catch
        {
            // Ignore literals that cannot be decoded.
        }
    }
    result["stringLiterals"] = literals;
}
File.WriteAllText(
    args[1],
    System.Text.Json.JsonSerializer.Serialize(result, new System.Text.Json.JsonSerializerOptions
    {
        WriteIndented = true,
        Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
    }),
    new UTF8Encoding(false)
);
Console.WriteLine($"types={types.Count}");
return 0;
