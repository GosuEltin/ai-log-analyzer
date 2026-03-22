# DirectoryIndex Forbidden

This error occurs when a client requests a directory (e.g., `http://example.com/images/`) and:
1. No file matching the `DirectoryIndex` (like `index.html`) exists.
2. `Options -Indexes` is configured, preventing a directory listing.

## Troubleshooting
- Check if `index.html` exists in the target directory.
- Check `DirectoryIndex` directive in `httpd.conf` or `.htaccess`.
- Verify `Options +Indexes` if directory listing is intended.
