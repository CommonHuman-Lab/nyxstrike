from server_core.enhanced_command_executor import _clean_output


def test_clean_output_strips_ansi_for_any_command():
    raw = "\x1b[1;34m[~]\x1b[0m Starting Nmap"

    cleaned = _clean_output(raw, "nmap -sV 127.0.0.1")

    assert cleaned == "[~] Starting Nmap"


def test_clean_output_strips_leading_banner_but_keeps_results():
    raw = "\n".join([
        "\x1b[1mASCII ART LINE\x1b[0m",
        "The Modern Day Port Scanner.",
        "https://github.com/RustScan/RustScan",
        "Port scanning: Because every port has a story to tell.",
        "",
        "\x1b[1;34m[~]\x1b[0m Automatically increasing ulimit value to 5000.",
        "Open 192.168.1.57:8096",
        "Starting Nmap 7.98",
    ])

    cleaned = _clean_output(raw)

    assert "The Modern Day Port Scanner." not in cleaned
    assert "https://github.com/RustScan/RustScan" not in cleaned
    assert "Automatically increasing ulimit value to 5000." in cleaned
    assert "Open 192.168.1.57:8096" in cleaned
    assert "\x1b" not in cleaned


def test_clean_output_does_not_strip_normal_top_lines():
    raw = "\n".join([
        "Nmap 7.98 scan report for 192.168.1.57",
        "Host is up (0.0053s latency).",
        "PORT     STATE SERVICE",
    ])

    cleaned = _clean_output(raw)

    assert cleaned == raw
