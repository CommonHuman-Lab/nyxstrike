"""
tests/test_output_cleaning_extended.py

Extended unit tests for the banner-stripping heuristics in
server_core/enhanced_command_executor.py.

Covers all branches of _is_decorative_line() and _is_banner_text_line()
that the original 3-case test_output_cleaning.py does not reach.

No subprocess, no Flask, no server calls.
"""

import pytest

from server_core.enhanced_command_executor import (
    _clean_output,
    _is_decorative_line,
    _is_banner_text_line,
    _strip_leading_banner_block,
)


# ---------------------------------------------------------------------------
# _is_decorative_line
# ---------------------------------------------------------------------------

class TestIsDecorativeLine:
    def test_empty_line_is_decorative(self):
        # The implementation treats empty/blank lines as decorative (returns True)
        assert _is_decorative_line("") is True

    def test_symbols_only_line_is_decorative(self):
        assert _is_decorative_line("========================================") is True

    def test_dashes_only_line_is_decorative(self):
        assert _is_decorative_line("----------------------------------------") is True

    def test_mixed_symbols_line_is_decorative(self):
        assert _is_decorative_line("~*~*~*~*~*~*~*~*~*~*~*~*~") is True

    def test_port_table_header_is_decorative(self):
        # "PORT     STATE SERVICE" — all-caps, low alphanumeric density → decorative
        assert _is_decorative_line("PORT     STATE SERVICE") is True

    def test_nmap_report_line_is_not_decorative(self):
        # Mixed case with IP address — high alphanumeric ratio → not decorative
        assert _is_decorative_line("Nmap 7.98 scan report for 192.168.1.57") is False

    def test_short_all_caps_word_is_not_decorative(self):
        # Only 7 visible chars — does not reach the 10-char threshold for the
        # all-caps rule, and has too high an alphanumeric ratio for the ratio rule
        assert _is_decorative_line("RUSTSCAN") is False

    def test_long_all_caps_banner_is_decorative(self):
        # >10 chars, >85% uppercase letters → decorative
        assert _is_decorative_line("RUSTSCAN BANNER TITLE LINE") is True


# ---------------------------------------------------------------------------
# _is_banner_text_line
# ---------------------------------------------------------------------------

class TestIsBannerTextLine:
    def test_github_url_is_banner(self):
        assert _is_banner_text_line("https://github.com/RustScan/RustScan") is True

    def test_http_url_is_banner(self):
        assert _is_banner_text_line("http://example.com/docs") is True

    def test_normal_result_line_is_not_banner(self):
        assert _is_banner_text_line("Open 192.168.1.57:8096") is False

    def test_nmap_version_line_is_banner(self):
        # Contains "https://" → _is_banner_text_line returns True regardless of context
        assert _is_banner_text_line("Starting Nmap 7.98 ( https://nmap.org )") is True

    def test_marketing_sentence_is_banner(self):
        # "The Modern Day Port Scanner." — title-case tagline
        assert _is_banner_text_line("The Modern Day Port Scanner.") is True

    def test_empty_line_is_not_banner(self):
        assert _is_banner_text_line("") is False


# ---------------------------------------------------------------------------
# _strip_leading_banner_block
# ---------------------------------------------------------------------------

class TestStripLeadingBannerBlock:
    def test_no_leading_decorative_line_is_noop(self):
        text = "Nmap scan report\nHost is up\nPORT STATE SERVICE"
        assert _strip_leading_banner_block(text) == text

    def test_fewer_than_three_consumed_lines_is_noop(self):
        # Only one banner line before real output — too short to strip
        text = "\n".join([
            "========",
            "Nmap 7.98 scan report for 192.168.1.1",
            "Host is up",
        ])
        result = _strip_leading_banner_block(text)
        # Should NOT strip because not enough banner lines were consumed
        assert "Nmap 7.98 scan report for 192.168.1.1" in result

    def test_full_rustscan_banner_is_stripped(self):
        text = "\n".join([
            "ASCII ART LINE",
            "The Modern Day Port Scanner.",
            "https://github.com/RustScan/RustScan",
            "Port scanning: Because every port has a story to tell.",
            "",
            "[~] Automatically increasing ulimit value to 5000.",
            "Open 192.168.1.57:8096",
        ])
        result = _strip_leading_banner_block(text)
        assert "The Modern Day Port Scanner." not in result
        assert "https://github.com/RustScan/RustScan" not in result
        assert "Automatically increasing ulimit value to 5000." in result
        assert "Open 192.168.1.57:8096" in result

    def test_empty_string_returns_empty(self):
        assert _strip_leading_banner_block("") == ""


# ---------------------------------------------------------------------------
# _clean_output — additional edge cases
# ---------------------------------------------------------------------------

class TestCleanOutputEdgeCases:
    def test_empty_string_returns_empty(self):
        assert _clean_output("") == ""

    def test_only_ansi_codes_returns_empty_or_whitespace(self):
        raw = "\x1b[1;34m\x1b[0m"
        cleaned = _clean_output(raw)
        assert "\x1b" not in cleaned

    def test_no_ansi_no_banner_is_unchanged(self):
        raw = "PORT  STATE  SERVICE\n22/tcp open  ssh\n80/tcp open  http"
        assert _clean_output(raw) == raw

    def test_multiline_ansi_stripped_throughout(self):
        raw = "\x1b[32mline one\x1b[0m\n\x1b[31mline two\x1b[0m"
        cleaned = _clean_output(raw)
        assert "\x1b" not in cleaned
        assert "line one" in cleaned
        assert "line two" in cleaned
