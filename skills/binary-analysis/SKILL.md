---
name: binary-analysis
description: Binary analysis and reverse engineering workflow using checksec, strings, binwalk, radare2, ropgadget, and gdb for CTF and vulnerability research
---

# binary-analysis

Binary analysis and reverse engineering workflow for NyxStrike. Use this skill when a user has a binary file to analyse, wants to find vulnerabilities, extract strings/firmware, build ROP chains, or debug execution.

## Workflow

### Step 1 — Security properties (checksec)

Always run checksec first to understand what mitigations are active:

```
run_tool(tool="checksec", file="/path/to/binary")
```

Key properties and what they mean:

| Property | Enabled = harder to exploit |
|---|---|
| NX / DEP | Stack is non-executable (no shellcode on stack) |
| PIE | Base address randomised (ASLR applies) |
| RELRO (Full) | GOT is read-only (no GOT overwrite) |
| Stack Canary | Stack overflow detection |
| FORTIFY | Safer libc functions enforced |

If **no PIE + no NX + no canary** → classic buffer overflow / ret2shellcode.
If **PIE + NX + Full RELRO** → likely needs ret2libc or ROP chain.

### Step 2 — String extraction (strings)

Extract human-readable strings — often reveals passwords, flags, URLs, function names:

```
run_tool(tool="strings", file="/path/to/binary")

# Filter for interesting strings
run_tool(tool="strings", file="/path/to/binary",
         additional_args="-n 8")
```

Look for: hardcoded credentials, flag format strings, file paths, debug messages.

### Step 3 — Firmware / embedded binary analysis (binwalk)

For firmware images, compressed archives, or unknown file formats:

```
# Scan and identify embedded content
run_tool(tool="binwalk", file="/path/to/firmware.bin")

# Extract all identified content
run_tool(tool="binwalk", file="/path/to/firmware.bin",
         additional_args="-e --run-as=root")
```

### Step 4 — Static disassembly and analysis (radare2)

Disassemble functions, find references, examine imports and exports:

```
# Auto-analyse and list functions
run_tool(tool="radare2", file="/path/to/binary",
         commands="aaa; afl")

# Disassemble main
run_tool(tool="radare2", file="/path/to/binary",
         commands="aaa; pdf @main")

# Find cross-references to a string or function
run_tool(tool="radare2", file="/path/to/binary",
         commands="aaa; axt @str.<string_name>")

# Check imports/exports
run_tool(tool="radare2", file="/path/to/binary",
         commands="ii; ie")
```

Useful radare2 command reference:

| Command | Description |
|---|---|
| `aaa` | Auto-analyse all |
| `afl` | List all functions |
| `pdf @<func>` | Disassemble function |
| `iz` | List strings in data section |
| `ii` | List imports |
| `ie` | List exports |
| `axt @<addr>` | Find cross-references to address |

### Step 5 — ROP gadget discovery (ropgadget)

When NX is enabled and you need a ROP chain:

```
run_tool(tool="ropgadget", file="/path/to/binary")

# Find specific gadget types
run_tool(tool="ropgadget", file="/path/to/binary",
         additional_args="--rop --badbytes '00'")
```

Common gadgets to look for:
- `pop rdi; ret` — set first argument (x64 calling convention)
- `pop rsi; ret` — set second argument
- `ret` — stack alignment (needed before some libc calls)
- `syscall` — for sigrop/syscall chains

### Step 6 — Dynamic debugging (gdb / gdb-peda)

Run the binary under gdb to observe runtime behaviour, find offsets, and test exploits:

```
# Basic gdb run
run_tool(tool="gdb", file="/path/to/binary",
         commands="run < input.txt")

# With PEDA enhancements (pattern offset finding)
run_tool(tool="gdb_peda", file="/path/to/binary",
         commands="pattern create 200; run")
```

Typical gdb workflow for buffer overflow:
1. `pattern create 200` → create cyclic pattern
2. `run` with pattern as input → binary crashes
3. `pattern offset <crash_value>` → find offset to return address
4. Craft exploit with correct padding + ROP chain / shellcode

## CTF pwn decision tree

```
checksec
  ├── No NX + No PIE + No canary → ret2shellcode
  ├── NX only (no PIE) → ret2libc (fixed addresses)
  ├── NX + PIE → leak libc/base address first, then ret2libc
  └── Full protection → advanced: SROP, heap exploit, format string
```

## Tips

- Run `strings` before anything else — flags are sometimes just stored plaintext.
- Always check `checksec` before spending time on ROP chain building — you may not need it.
- Use radare2 `pdf @main` to quickly orient yourself in the binary without a GUI.
- ROP gadgets from libc are often more useful than gadgets in the binary itself — run ropgadget on libc too.

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `checksec` | Binary security properties |
| `strings` | Extract printable strings |
| `binwalk` | Firmware analysis and extraction |
| `radare2` | Static disassembly and analysis |
| `ropgadget` | ROP gadget discovery |
| `gdb` | Dynamic debugging |
| `gdb_peda` | GDB with PEDA exploit dev enhancements |
