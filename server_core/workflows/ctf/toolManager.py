from typing import List

class CTFToolManager:
    """Advanced tool manager for CTF challenges with comprehensive tool arsenal"""

    def __init__(self):
        self.tool_commands = {
            # Web Application Security Tools
            "httpx": "httpx -probe -tech-detect -status-code -title -content-length",
            "katana": "katana -depth 3 -js-crawl -form-extraction -headless",
            "sqlmap": "sqlmap --batch --level 3 --risk 2 --threads 5",
            "dalfox": "dalfox url --mining-dom --mining-dict --deep-domxss",
            "gobuster": "gobuster dir -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt,js",
            "dirsearch": "dirsearch -u {} -e php,html,js,txt,xml,json -t 50",
            "feroxbuster": "feroxbuster -u {} -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,js,txt",
            "arjun": "arjun -u {} --get --post",
            "paramspider": "paramspider -d {}",
            "wpscan": "wpscan --url {} --enumerate ap,at,cb,dbe",
            "nikto": "nikto -h {} -C all",
            "whatweb": "whatweb -v -a 3",

            # Cryptography Challenge Tools
            "hashcat": "hashcat -m 0 -a 0 --potfile-disable --quiet",
            "john": "john --wordlist=/usr/share/wordlists/rockyou.txt --format=Raw-MD5",
            "hashid": "hashid -m",
            "cipher-identifier": "python3 /opt/cipher-identifier/cipher_identifier.py",
            "factordb": "python3 /opt/factordb/factordb.py",
            "rsatool": "python3 /opt/rsatool/rsatool.py",
            "yafu": "yafu",
            "sage": "sage -python",
            "openssl": "openssl",
            "gpg": "gpg --decrypt",
            "steganography": "stegcracker",
            "frequency-analysis": "python3 /opt/frequency-analysis/freq_analysis.py",
            "substitution-solver": "python3 /opt/substitution-solver/solve.py",
            "vigenere-solver": "python3 /opt/vigenere-solver/vigenere.py",
            "base64": "base64 -d",
            "base32": "base32 -d",
            "hex": "xxd -r -p",
            "rot13": "tr 'A-Za-z' 'N-ZA-Mn-za-m'",

            # Binary Exploitation (Pwn) Tools
            "checksec": "checksec --file",
            "pwntools": "python3 -c 'from pwn import *; context.log_level = \"debug\"'",
            "ropper": "ropper --file {} --search",
            "ropgadget": "ROPgadget --binary",
            "one-gadget": "one_gadget",
            "gdb-peda": "gdb -ex 'source /opt/peda/peda.py'",
            "gdb-gef": "gdb -ex 'source /opt/gef/gef.py'",
            "gdb-pwngdb": "gdb -ex 'source /opt/Pwngdb/pwngdb.py'",
            "angr": "python3 -c 'import angr'",
            "radare2": "r2 -A",
            "ghidra": "analyzeHeadless /tmp ghidra_project -import",
            "binary-ninja": "binaryninja",
            "ltrace": "ltrace",
            "strace": "strace -f",
            "objdump": "objdump -d -M intel",
            "readelf": "readelf -a",
            "nm": "nm -D",
            "ldd": "ldd",
            "file": "file",
            "strings": "strings -n 8",
            "hexdump": "hexdump -C",
            "pwninit": "pwninit",
            "libc-database": "python3 /opt/libc-database/find.py",

            # Forensics Investigation Tools
            "binwalk": "binwalk -e --dd='.*'",
            "foremost": "foremost -i {} -o /tmp/foremost_output",
            "photorec": "photorec /log /cmd",
            "testdisk": "testdisk /log",
            "exiftool": "exiftool -all",
            "steghide": "steghide extract -sf {} -p ''",
            "stegsolve": "java -jar /opt/stegsolve/stegsolve.jar",
            "zsteg": "zsteg -a",
            "outguess": "outguess -r",
            "jsteg": "jsteg reveal",
            "volatility": "volatility -f {} imageinfo",
            "volatility3": "python3 /opt/volatility3/vol.py -f",
            "rekall": "rekall -f",
            "wireshark": "tshark -r",
            "tcpdump": "tcpdump -r",
            "networkminer": "mono /opt/NetworkMiner/NetworkMiner.exe",
            "autopsy": "autopsy",
            "sleuthkit": "fls -r",
            "scalpel": "scalpel -c /etc/scalpel/scalpel.conf",
            "bulk-extractor": "bulk_extractor -o /tmp/bulk_output",
            "ddrescue": "ddrescue",
            "dc3dd": "dc3dd",

            # Reverse Engineering Tools
            "ida": "ida64",
            "ida-free": "ida64 -A",
            "retdec": "retdec-decompiler",
            "upx": "upx -d",
            "peid": "peid",
            "detect-it-easy": "die",
            "x64dbg": "x64dbg",
            "ollydbg": "ollydbg",
            "immunity": "immunity",
            "windbg": "windbg",
            "apktool": "apktool d",
            "jadx": "jadx",
            "dex2jar": "dex2jar",
            "jd-gui": "jd-gui",
            "dnspy": "dnspy",
            "ilspy": "ilspy",
            "dotpeek": "dotpeek",

            # OSINT and Reconnaissance Tools
            "sherlock": "sherlock",
            "social-analyzer": "social-analyzer",
            "theHarvester": "theHarvester -d {} -b all",
            "recon-ng": "recon-ng",
            "maltego": "maltego",
            "spiderfoot": "spiderfoot",
            "shodan": "shodan search",
            "censys": "censys search",
            "whois": "whois",
            "dig": "dig",
            "nslookup": "nslookup",
            "host": "host",
            "dnsrecon": "dnsrecon -d",
            "fierce": "fierce -dns",
            "sublist3r": "sublist3r -d",
            "amass": "amass enum -d",
            "assetfinder": "assetfinder",
            "subfinder": "subfinder -d",
            "waybackurls": "waybackurls",
            "gau": "gau",
            "httpx-osint": "httpx -title -tech-detect -status-code",

            # Miscellaneous Challenge Tools
            "qr-decoder": "zbarimg",
            "barcode-decoder": "zbarimg",
            "audio-analysis": "audacity",
            "sonic-visualizer": "sonic-visualizer",
            "spectrum-analyzer": "python3 /opt/spectrum-analyzer/analyze.py",
            "brainfuck": "python3 /opt/brainfuck/bf.py",
            "whitespace": "python3 /opt/whitespace/ws.py",
            "piet": "python3 /opt/piet/piet.py",
            "malbolge": "python3 /opt/malbolge/malbolge.py",
            "ook": "python3 /opt/ook/ook.py",
            "zip": "unzip -P",
            "7zip": "7z x -p",
            "rar": "unrar x -p",
            "tar": "tar -xf",
            "gzip": "gunzip",
            "bzip2": "bunzip2",
            "xz": "unxz",
            "lzma": "unlzma",
            "compress": "uncompress",

            # Modern Web Technologies
            "jwt-tool": "python3 /opt/jwt_tool/jwt_tool.py",
            "jwt-cracker": "jwt-cracker",
            "graphql-voyager": "graphql-voyager",
            "graphql-playground": "graphql-playground",
            "postman": "newman run",
            "burpsuite": "java -jar /opt/burpsuite/burpsuite.jar",
            "owasp-zap": "zap.sh -cmd",
            "websocket-king": "python3 /opt/websocket-king/ws_test.py",

            # Cloud and Container Security
            "docker": "docker",
            "kubectl": "kubectl",
            "aws-cli": "aws",
            "azure-cli": "az",
            "gcloud": "gcloud",
            "terraform": "terraform",
            "ansible": "ansible",

            # Mobile Application Security
            "adb": "adb",
            "frida": "frida",
            "objection": "objection",
            "mobsf": "python3 /opt/mobsf/manage.py",
            "apkleaks": "apkleaks -f",
            "qark": "qark --apk"
        }

        # Tool categories for intelligent selection
        self.tool_categories = {
            "web_recon": ["httpx", "katana", "waybackurls", "gau", "whatweb"],
            "web_vuln": ["sqlmap", "dalfox", "nikto", "wpscan"],
            "web_discovery": ["gobuster", "dirsearch", "feroxbuster"],
            "web_params": ["arjun", "paramspider"],
            "crypto_hash": ["hashcat", "john", "hashid"],
            "crypto_cipher": ["cipher-identifier", "frequency-analysis", "substitution-solver"],
            "crypto_rsa": ["rsatool", "factordb", "yafu"],
            "crypto_modern": ["sage", "openssl", "gpg"],
            "pwn_analysis": ["checksec", "file", "strings", "objdump", "readelf"],
            "pwn_exploit": ["pwntools", "ropper", "ropgadget", "one-gadget"],
            "pwn_debug": ["gdb-peda", "gdb-gef", "ltrace", "strace"],
            "pwn_advanced": ["angr", "ghidra", "radare2"],
            "forensics_file": ["binwalk", "foremost", "photorec", "exiftool"],
            "forensics_image": ["steghide", "stegsolve", "zsteg", "outguess"],
            "forensics_memory": ["volatility", "volatility3", "rekall"],
            "forensics_network": ["wireshark", "tcpdump", "networkminer"],
            "rev_static": ["ghidra", "ida", "radare2", "strings"],
            "rev_dynamic": ["gdb-peda", "ltrace", "strace"],
            "rev_unpack": ["upx", "peid", "detect-it-easy"],
            "osint_social": ["sherlock", "social-analyzer", "theHarvester"],
            "osint_domain": ["whois", "dig", "sublist3r", "amass"],
            "osint_search": ["shodan", "censys", "recon-ng"],
            "misc_encoding": ["base64", "base32", "hex", "rot13"],
            "misc_compression": ["zip", "7zip", "rar", "tar"],
            "misc_esoteric": ["brainfuck", "whitespace", "piet", "malbolge"],
            "db": ["mysql", "postgresql", "sqlite"]
        }

    def get_tool_command(self, tool: str, target: str, additional_args: str = "") -> str:
        """Get optimized command for CTF tool with intelligent parameter selection"""
        base_command = self.tool_commands.get(tool, tool)

        # Add intelligent parameter optimization based on tool type
        if tool in ["hashcat", "john"]:
            # For hash cracking, add common wordlists and rules
            if "wordlist" not in base_command:
                base_command += " --wordlist=/usr/share/wordlists/rockyou.txt"
            if tool == "hashcat" and "--rules" not in base_command:
                base_command += " --rules-file=/usr/share/hashcat/rules/best64.rule"

        elif tool in ["sqlmap"]:
            # For SQL injection, add tamper scripts and optimization
            if "--tamper" not in base_command:
                base_command += " --tamper=space2comment,charencode,randomcase"
            if "--threads" not in base_command:
                base_command += " --threads=5"

        elif tool in ["gobuster", "dirsearch", "feroxbuster"]:
            # For directory brute forcing, optimize threads and extensions
            if tool == "gobuster" and "-t" not in base_command:
                base_command += " -t 50"
            elif tool == "dirsearch" and "-t" not in base_command:
                base_command += " -t 50"
            elif tool == "feroxbuster" and "-t" not in base_command:
                base_command += " -t 50"

        if additional_args:
            return f"{base_command} {additional_args} {target}"
        else:
            return f"{base_command} {target}"

    def get_category_tools(self, category: str) -> List[str]:
        """Get all tools for a specific category"""
        return self.tool_categories.get(category, [])

    def suggest_tools_for_challenge(self, challenge_description: str, category: str) -> List[str]:
        """Suggest optimal tools based on challenge description and category"""
        suggested_tools = []
        description_lower = challenge_description.lower()

        # Category-based tool suggestions
        if category == "web":
            suggested_tools.extend(self.tool_categories["web_recon"][:2])

            if any(keyword in description_lower for keyword in ["sql", "injection", "database", "mysql", "postgres"]):
                suggested_tools.extend(["sqlmap", "hashid"])
            if any(keyword in description_lower for keyword in ["xss", "script", "javascript", "dom"]):
                suggested_tools.extend(["dalfox", "katana"])
            if any(keyword in description_lower for keyword in ["wordpress", "wp", "cms"]):
                suggested_tools.append("wpscan")
            if any(keyword in description_lower for keyword in ["directory", "hidden", "files", "admin"]):
                suggested_tools.extend(["gobuster", "dirsearch"])
            if any(keyword in description_lower for keyword in ["parameter", "param", "get", "post"]):
                suggested_tools.extend(["arjun", "paramspider"])
            if any(keyword in description_lower for keyword in ["jwt", "token", "session"]):
                suggested_tools.append("jwt-tool")
            if any(keyword in description_lower for keyword in ["graphql", "api"]):
                suggested_tools.append("graphql-voyager")

        elif category == "crypto":
            if any(keyword in description_lower for keyword in ["hash", "md5", "sha", "password"]):
                suggested_tools.extend(["hashcat", "john", "hashid"])
            if any(keyword in description_lower for keyword in ["rsa", "public key", "private key", "factorization"]):
                suggested_tools.extend(["rsatool", "factordb", "yafu"])
            if any(keyword in description_lower for keyword in ["cipher", "encrypt", "decrypt", "substitution"]):
                suggested_tools.extend(["cipher-identifier", "frequency-analysis"])
            if any(keyword in description_lower for keyword in ["vigenere", "polyalphabetic"]):
                suggested_tools.append("vigenere-solver")
            if any(keyword in description_lower for keyword in ["base64", "base32", "encoding"]):
                suggested_tools.extend(["base64", "base32"])
            if any(keyword in description_lower for keyword in ["rot", "caesar", "shift"]):
                suggested_tools.append("rot13")
            if any(keyword in description_lower for keyword in ["pgp", "gpg", "signature"]):
                suggested_tools.append("gpg")

        elif category == "pwn":
            suggested_tools.extend(["checksec", "file", "strings"])

            if any(keyword in description_lower for keyword in ["buffer", "overflow", "bof"]):
                suggested_tools.extend(["pwntools", "gdb-peda", "ropper"])
            if any(keyword in description_lower for keyword in ["format", "printf", "string"]):
                suggested_tools.extend(["pwntools", "gdb-peda"])
            if any(keyword in description_lower for keyword in ["heap", "malloc", "free"]):
                suggested_tools.extend(["pwntools", "gdb-gef"])
            if any(keyword in description_lower for keyword in ["rop", "gadget", "chain"]):
                suggested_tools.extend(["ropper", "ropgadget"])
            if any(keyword in description_lower for keyword in ["shellcode", "exploit"]):
                suggested_tools.extend(["pwntools", "one-gadget"])
            if any(keyword in description_lower for keyword in ["canary", "stack", "protection"]):
                suggested_tools.extend(["checksec", "pwntools"])

        elif category == "forensics":
            if any(keyword in description_lower for keyword in ["image", "jpg", "png", "gif", "steganography"]):
                suggested_tools.extend(["exiftool", "steghide", "stegsolve", "zsteg"])
            if any(keyword in description_lower for keyword in ["memory", "dump", "ram"]):
                suggested_tools.extend(["volatility", "volatility3"])
            if any(keyword in description_lower for keyword in ["network", "pcap", "wireshark", "traffic"]):
                suggested_tools.extend(["wireshark", "tcpdump"])
            if any(keyword in description_lower for keyword in ["file", "deleted", "recovery", "carving"]):
                suggested_tools.extend(["binwalk", "foremost", "photorec"])
            if any(keyword in description_lower for keyword in ["disk", "filesystem", "partition"]):
                suggested_tools.extend(["testdisk", "sleuthkit"])
            if any(keyword in description_lower for keyword in ["audio", "wav", "mp3", "sound"]):
                suggested_tools.extend(["audacity", "sonic-visualizer"])

        elif category == "rev":
            suggested_tools.extend(["file", "strings", "objdump"])

            if any(keyword in description_lower for keyword in ["packed", "upx", "packer"]):
                suggested_tools.extend(["upx", "peid", "detect-it-easy"])
            if any(keyword in description_lower for keyword in ["android", "apk", "mobile"]):
                suggested_tools.extend(["apktool", "jadx", "dex2jar"])
            if any(keyword in description_lower for keyword in [".net", "dotnet", "csharp"]):
                suggested_tools.extend(["dnspy", "ilspy"])
            if any(keyword in description_lower for keyword in ["java", "jar", "class"]):
                suggested_tools.extend(["jd-gui", "jadx"])
            if any(keyword in description_lower for keyword in ["windows", "exe", "dll"]):
                suggested_tools.extend(["ghidra", "ida", "x64dbg"])
            if any(keyword in description_lower for keyword in ["linux", "elf", "binary"]):
                suggested_tools.extend(["ghidra", "radare2", "gdb-peda"])

        elif category == "osint":
            if any(keyword in description_lower for keyword in ["username", "social", "media"]):
                suggested_tools.extend(["sherlock", "social-analyzer"])
            if any(keyword in description_lower for keyword in ["domain", "subdomain", "dns"]):
                suggested_tools.extend(["sublist3r", "amass", "dig"])
            if any(keyword in description_lower for keyword in ["email", "harvest", "contact"]):
                suggested_tools.append("theHarvester")
            if any(keyword in description_lower for keyword in ["ip", "port", "service"]):
                suggested_tools.extend(["shodan", "censys"])
            if any(keyword in description_lower for keyword in ["whois", "registration", "owner"]):
                suggested_tools.append("whois")

        elif category == "misc":
            if any(keyword in description_lower for keyword in ["qr", "barcode", "code"]):
                suggested_tools.append("qr-decoder")
            if any(keyword in description_lower for keyword in ["zip", "archive", "compressed"]):
                suggested_tools.extend(["zip", "7zip", "rar"])
            if any(keyword in description_lower for keyword in ["brainfuck", "bf", "esoteric"]):
                suggested_tools.append("brainfuck")
            if any(keyword in description_lower for keyword in ["whitespace", "ws"]):
                suggested_tools.append("whitespace")
            if any(keyword in description_lower for keyword in ["piet", "image", "program"]):
                suggested_tools.append("piet")

        # Remove duplicates while preserving order
        return list(dict.fromkeys(suggested_tools))
