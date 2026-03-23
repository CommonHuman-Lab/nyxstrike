from flask import Blueprint, request, jsonify
import logging
import re
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)

api_ctf_cryptography_solver_bp = Blueprint("api_ctf_cryptography_solver", __name__)


@api_ctf_cryptography_solver_bp.route("/api/ctf/cryptography-solver", methods=["POST"])
def ctf_cryptography_solver():
    """Advanced cryptography challenge solver with multiple attack methods"""
    try:
        params = request.json
        cipher_text = params.get("cipher_text", "")
        cipher_type = params.get("cipher_type", "unknown")
        key_hint = params.get("key_hint", "")
        known_plaintext = params.get("known_plaintext", "")
        additional_info = params.get("additional_info", "")

        if not cipher_text:
            return jsonify({"error": "Cipher text is required"}), 400

        results = {
            "cipher_text": cipher_text,
            "cipher_type": cipher_type,
            "analysis_results": [],
            "potential_solutions": [],
            "recommended_tools": [],
            "next_steps": []
        }

        # Cipher type identification
        if cipher_type == "unknown":
            # Basic cipher identification heuristics
            if re.match(r'^[0-9a-fA-F]+$', cipher_text.replace(' ', '')):
                results["analysis_results"].append("Possible hexadecimal encoding")
                results["recommended_tools"].extend(["hex", "xxd"])

            if re.match(r'^[A-Za-z0-9+/]+=*$', cipher_text.replace(' ', '')):
                results["analysis_results"].append("Possible Base64 encoding")
                results["recommended_tools"].append("base64")

            if len(set(cipher_text.upper().replace(' ', ''))) <= 26:
                results["analysis_results"].append("Possible substitution cipher")
                results["recommended_tools"].extend(["frequency-analysis", "substitution-solver"])

        # Hash identification
        hash_patterns = {
            32: "MD5",
            40: "SHA1",
            64: "SHA256",
            128: "SHA512"
        }

        clean_text = cipher_text.replace(' ', '').replace('\n', '')
        if len(clean_text) in hash_patterns and re.match(r'^[0-9a-fA-F]+$', clean_text):
            hash_type = hash_patterns[len(clean_text)]
            results["analysis_results"].append(f"Possible {hash_type} hash")
            results["recommended_tools"].extend(["hashcat", "john", "hashid"])

        # Frequency analysis for substitution ciphers
        if cipher_type in ["substitution", "caesar", "vigenere"] or "substitution" in results["analysis_results"]:
            char_freq: Dict[str, int] = {}
            for char in cipher_text.upper():
                if char.isalpha():
                    char_freq[char] = char_freq.get(char, 0) + 1

            if char_freq:
                most_common = max(char_freq.keys(), key=lambda key: char_freq[key])
                results["analysis_results"].append(f"Most frequent character: {most_common} ({char_freq[most_common]} occurrences)")
                results["next_steps"].append("Try substituting most frequent character with 'E'")

        # ROT/Caesar cipher detection
        if cipher_type == "caesar" or len(set(cipher_text.upper().replace(' ', ''))) <= 26:
            results["recommended_tools"].append("rot13")
            results["next_steps"].append("Try all ROT values (1-25)")

        # RSA-specific analysis
        if cipher_type == "rsa" or "rsa" in additional_info.lower():
            results["recommended_tools"].extend(["rsatool", "factordb", "yafu"])
            results["next_steps"].extend([
                "Check if modulus can be factored",
                "Look for small public exponent attacks",
                "Check for common modulus attacks"
            ])

        # Vigenère cipher analysis
        if cipher_type == "vigenere" or "vigenere" in additional_info.lower():
            results["recommended_tools"].append("vigenere-solver")
            results["next_steps"].extend([
                "Perform Kasiski examination for key length",
                "Use index of coincidence analysis",
                "Try common key words"
            ])

        logger.info(f"🔐 CTF crypto analysis completed | Type: {cipher_type} | Tools: {len(results['recommended_tools'])}")
        return jsonify({
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF crypto solver: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
