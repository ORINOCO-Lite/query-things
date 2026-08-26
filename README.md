# query-things

Query, reshape, and export metadata represented using the
[Things](https://concepts.datalad.org) data model.

`query-things` provides a small Python-based extraction layer for
Things-compatible metadata backends. It selects records and properties,
resolves linked objects, and converts graph-oriented metadata into structures
that can be consumed by templates, websites, reports, catalogs, and other
automated workflows.  Its main purpose is therefore *controlled
denormalization*: preserving the semantics of a linked metadata graph while
making selected portions convenient to use in structure data workflows.


## Supported operations

The following operations are supported via individual `query-things` subcommands:

| Subcommand | Synopsis |
|---|---|
| `cache` | Read JSON lines from standard input, cache records by their `pid`, and pass the original input unchanged to standard output. |
| `filter-linked-pid` | Keep input records whose `pid` appears in a specified property of one reference record fetched from a Things API. |
| `filter-links-pid` | Keep input records that link to one or more specified PIDs through specified properties, optionally following links recursively. |
| `inject-links-pid` | Find records that link to the current input record and inject those linker records into a named property. |
| `inline-things` | Resolve PID references at one or more nested paths and replace them with fetched Things records. |
| `render-record` | Render each input metadata record through a Jinja template and write the result to a filename derived from one or more filename templates. |
| `list` | List records currently held in the record cache, optionally restricted by PID or schema class. |


## Related solutions

- [dump-things-service](https://hub.psychoinformatics.de/orinoco/dump-things-service) metadata backend
- [dump-things-pyclient](https://hub.psychoinformatics.de/orinoco/dump-things-pyclient) CLI for accessing a dump-things-service
- [shacl-vue](https://hub.psychoinformatics.de/orinoco/shacl-vue) metadata editor/frontend


## License

MIT
