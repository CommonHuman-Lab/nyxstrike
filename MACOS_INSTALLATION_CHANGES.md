# macOS installation notes

The macOS changes address missing tools, interrupted installations and dependency
conflicts reported during setup, including failures on Intel/macOS 12. Setup and
repair remain part of the existing command:

```bash
./nyxstrike.sh -a -t
```

The launcher prepares the project and starts the server; `-t` enables installation
and validation of external tools. Re-running it retries failures. Installation
details are recorded in `install_log.txt`.

## What changed

`backend/server_core/tool_constants.py` now defines the macOS tool catalog: the
command to look for, installation method, validation probe, upstream source and,
where applicable, the reason a tool is unsupported. The installer and tool
inventory use this information to distinguish missing tools from unsupported ones
and recognize aliases such as `one_gadget`, `testssl.sh` and `analyzeHeadless`.

The installer checks each tool using its command, runtime or required resource
files before reporting success. These checks do not exercise every feature or
launch every GUI. Managed wrappers live in `~/.local/share/nyxstrike-tools/bin`,
preserve quoted arguments and take precedence over older copies in the launcher's
PATH. External tool dependencies use separate runtimes where needed to avoid
conflicts with the server environment.

Homebrew formulas and casks can be repaired when their files or runtime checks
fail. Catalog input uses a separate file descriptor so a package manager cannot
consume the remaining recipes from standard input. Downloads use HTTPS, with
pinned revisions and checksums for the source and archive recipes.

## Tool-specific changes

- **WAFW00F and Sublist3r:** install from their official repositories in private
  Python environments.
- **Wfuzz and WhatWeb:** use managed runtimes. Wfuzz uses corrected upstream
  package metadata and a PycURL wheel; WhatWeb uses Homebrew Ruby and isolated gems.
- **WPScan:** tries the official Homebrew tap first. If that installation fails,
  it falls back to WPScan 4.1.0 with Homebrew Ruby 3.4 and a private gem directory.
- **Patator:** uses a pinned upstream revision with portable dependencies. Its
  optional database adapters are unavailable in this managed macOS runtime.
- **SSLScan:** builds pinned release 2.2.2 against Homebrew OpenSSL.
- **ChromeDriver:** uses Selenium Manager instead of the disabled cask. A missing
  Chrome installation is reported as a failure.
- **testssl.sh:** uses pinned release 3.2.4 and bypasses the duplicate macOS path.
- **Impacket:** checks both `smbclient.py` and `secretsdump.py` before publishing the
  main command, so an interrupted installation is not reported as complete.
- **Burp Suite and Maltego:** check application files and required runtimes.
  Maltego installs and checks Temurin Java 11.
- **Autopsy:** uses the official GStreamer 1.28.7 universal runtime instead of the
  Homebrew dependency chain that failed while building DBus. Its SHA256 is checked;
  this upstream package is not Apple-signed and installs into the required system
  framework location. Validation checks multimedia plugins, Java and Sleuth Kit
  resources without launching Autopsy's GUI.
- **CloudMapper:** uses private Python 3.9 and `setuptools<82` as a build constraint
  for dependencies that still import `pkg_resources`.
- **DIRB:** repairs directory permissions in the upstream archive before building.
- **DotDotPwn:** installs `LWP::UserAgent` and `LWP::Protocol::https` in its Perl
  environment.
- **GDB:** builds release 17.2 with explicit C++ includes and Homebrew's Darwin
  include fix, retaining Python integration and all targets. On Apple Silicon it
  targets x86_64 Darwin. Attaching to macOS processes still requires appropriate
  code signing. The original log omitted the first compiler error, so this fix
  still needs confirmation through an actual Intel build.
- **Kismet:** when Homebrew supports formula trust, trusts only the two formulas
  from Kismet's official tap needed during conflict checks.
- **msfvenom:** accepts help's exit status of 1 only when the expected banner and
  usage text are present, including when checking an existing installation.
- **OutGuess:** uses Apple's archive tools, including the bundled JPEG makefile's
  `AR2` setting, to avoid incompatible static libraries.
- **Steghide:** builds private libmcrypt 2.5.8 with a checksum and pinned MacPorts
  patches because the Homebrew formula is unavailable.
- **TShark:** uses the official Wireshark 4.6.8 universal bundle and its libraries.
  The recipe checks the archive checksum and bundle signature. If the disk image
  cannot be detached, it keeps the staging directory without removing mounted
  contents or replacing the previous command. Live capture still requires the
  appropriate macOS permissions.
- **Vulnx:** checks `version --disable-update-check` and disables update checks
  during subcommand help probes.

## Catalog coverage

The catalog contains 80 entries. These are installation routes, not a claim that
all tools have been tested end to end on each supported architecture.

| Route | Count | Tools |
| --- | ---: | --- |
| Homebrew | 16 | airbase-ng, aircrack-ng, airdecap-ng, aireplay-ng, airodump-ng, bettercap, bulk_extractor, ghidra, hcxpcapngtool, kismet, kube-bench, massdns, ophcrack, rpcclient, sleuthkit, terrascan |
| Native source or application recipe | 20 | autopsy, dirb, dnsenum, dotdotpwn, gdb, hashcat-utils, hashpump, hurl, joomscan, libc-database, msfconsole, msfvenom, nbtscan, outguess, scalpel, sslscan, steghide, testssl, tshark, zaproxy |
| Go | 8 | anew, assetfinder, gospider, httpx, jaeles, qsreplace, shuffledns, vulnx |
| Isolated Python | 7 | impacket-scripts, kube-hunter, pacu, parsero, patator, prowler, scout-suite |
| Dedicated recipe | 7 | enum4linux-ng, nxc, sublist3r, wafw00f, wfuzz, whatweb, wpscan |
| Server Python | 5 | breachsql, phaseaccess, pwntools, stingxss, vaultrip |
| Pinned Python source | 3 | cloudmapper, spiderfoot, xsser |
| Ruby | 2 | evil-winrm, one-gadget |
| Rust | 2 | pwninit, x8 |
| macOS cask | 2 | burpsuite, maltego |
| Unsupported | 8 | airmon-ng, clair, docker-bench-security, eaphammer, falco, hcxdumptool, mdk4, wifite |

The unsupported entries are reported as `NOT SUPPORTED ON MACOS` with an
explanation. Most depend on Linux wireless drivers or kernel facilities. Clair
needs a configured service and PostgreSQL; installing `clairctl` alone would not
provide that service. Docker Bench audits a Linux host rather than the macOS host
of Docker Desktop.

## Sources

Each catalog entry records its upstream `source_url`. Build recipes also pin their
source revisions or archive checksums where needed. Key references include
[WAFW00F](https://github.com/EnableSecurity/wafw00f),
[Sublist3r](https://github.com/aboul3la/Sublist3r),
[WPScan](https://github.com/wpscanteam/wpscan),
[testssl.sh 3.2.4](https://github.com/testssl/testssl.sh/releases/tag/v3.2.4),
[GStreamer](https://gstreamer.freedesktop.org/download/),
[Wireshark 4.6.8](https://lists.wireshark.org/archives/wireshark-announce/202608/msg00000.html),
[GDB's Homebrew formula](https://github.com/Homebrew/homebrew-core/blob/main/Formula/g/gdb.rb),
[libmcrypt's MacPorts recipe](https://github.com/macports/macports-ports/blob/6e6c4e936380329061b22afd7b103993c07dd326/devel/libmcrypt/Portfile)
and [Homebrew formula trust](https://docs.brew.sh/Tap-Trust).

## Verification and remaining work

The recorded installer checks cover 94 passing offline tests: 88 macOS tests and
six installation-failure tests. They simulate package managers, startup failures
and interrupted installation paths without downloading or installing security
tools. Bash syntax, Python syntax and whitespace checks passed, and the updated
lockfile passes `uv lock --check --offline`. The frontend is unchanged from the
upstream beta branch. Its `tsc --noEmit` check passes, but ESLint reports 46
existing errors; frontend fixes are outside this contribution.

These checks do not replace a complete installation on Intel/macOS 12. That run
must still verify real downloads, native compilation and tool startup on the
target machine. A successful availability probe also does not establish that all
features work with the machine's hardware, permissions or external services.
