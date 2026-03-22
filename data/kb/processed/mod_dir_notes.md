# mod_dir Notes

`mod_dir` provides for "trailing slash" redirects and directory index file serving.

## Directives
- `DirectoryIndex`: Sets the files to look for when a directory is requested.
- `DirectorySlash`: Determines if `mod_dir` should fix URLs missing a trailing slash.

If `DirectorySlash Off` is used, it can lead to security issues or unexpected `403` errors.
