# authz_host_notes.md

`mod_authz_host` handles authorization based on the client's network identity.

## Common Issues
- **DNS Lookup Delays**: If `Require host` is used, Apache must perform a reverse DNS lookup, which can slow down requests.
- **IP Masking**: Load balancers or proxies might mask the real client IP, requiring the use of `mod_remoteip`.
- **Require local**: Useful for restricting access to tools (like server-status) to the server itself.
