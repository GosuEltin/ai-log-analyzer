# Apache Access Control: Require Directive

The `Require` directive is the primary way to control access in Apache 2.4.

- `Require all granted`: Open access.
- `Require all denied`: Block all access.
- `Require ip 10.0.0.1`: Restrict to specific IP.
- `Require host example.com`: Restrict to specific hostname.

If a request is blocked, the Error Log will often show `AH01630: client denied by server configuration`.
