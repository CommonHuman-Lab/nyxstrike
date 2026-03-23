from flask import Blueprint, request, jsonify
import logging
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

api_ctf_forensics_analyzer_bp = Blueprint("api_ctf_forensics_analyzer", __name__)


@api_ctf_forensics_analyzer_bp.route("/api/ctf/forensics-analyzer", methods=["POST"])
def ctf_forensics_analyzer():
    """Advanced forensics challenge analyzer with multiple investigation techniques"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        analysis_type = params.get("analysis_type", "comprehensive")
        extract_hidden = params.get("extract_hidden", True)
        check_steganography = params.get("check_steganography", True)

        if not file_path:
            return jsonify({"error": "File path is required"}), 400

        results = {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "file_info": {},
            "metadata": {},
            "hidden_data": [],
            "steganography_results": [],
            "recommended_tools": [],
            "next_steps": []
        }

        # Basic file analysis
        try:
            file_result = subprocess.run(['file', file_path], capture_output=True, text=True, timeout=30)
            if file_result.returncode == 0:
                results["file_info"]["type"] = file_result.stdout.strip()

                # Determine file category and suggest tools
                file_type = file_result.stdout.lower()
                if "image" in file_type:
                    results["recommended_tools"].extend(["exiftool", "steghide", "stegsolve", "zsteg"])
                    results["next_steps"].extend([
                        "Extract EXIF metadata",
                        "Check for steganographic content",
                        "Analyze color channels separately"
                    ])
                elif "audio" in file_type:
                    results["recommended_tools"].extend(["audacity", "sonic-visualizer", "spectrum-analyzer"])
                    results["next_steps"].extend([
                        "Analyze audio spectrum",
                        "Check for hidden data in audio channels",
                        "Look for DTMF tones or morse code"
                    ])
                elif "pdf" in file_type:
                    results["recommended_tools"].extend(["pdfinfo", "pdftotext", "binwalk"])
                    results["next_steps"].extend([
                        "Extract text and metadata",
                        "Check for embedded files",
                        "Analyze PDF structure"
                    ])
                elif "zip" in file_type or "archive" in file_type:
                    results["recommended_tools"].extend(["unzip", "7zip", "binwalk"])
                    results["next_steps"].extend([
                        "Extract archive contents",
                        "Check for password protection",
                        "Look for hidden files"
                    ])
        except Exception as e:
            results["file_info"]["error"] = str(e)

        # Metadata extraction
        try:
            exif_result = subprocess.run(['exiftool', file_path], capture_output=True, text=True, timeout=30)
            if exif_result.returncode == 0:
                results["metadata"]["exif"] = exif_result.stdout
        except Exception as e:
            results["metadata"]["exif_error"] = str(e)

        # Binwalk analysis for hidden files
        if extract_hidden:
            try:
                binwalk_result = subprocess.run(['binwalk', '-e', file_path], capture_output=True, text=True, timeout=60)
                if binwalk_result.returncode == 0:
                    results["hidden_data"].append({
                        "tool": "binwalk",
                        "output": binwalk_result.stdout
                    })
            except Exception as e:
                results["hidden_data"].append({
                    "tool": "binwalk",
                    "error": str(e)
                })

        # Steganography checks
        if check_steganography:
            steg_tools = ["steghide", "zsteg", "outguess"]
            for tool in steg_tools:
                try:
                    steg_result = None
                    if tool == "steghide":
                        steg_result = subprocess.run([tool, 'info', file_path], capture_output=True, text=True, timeout=30)
                    elif tool == "zsteg":
                        steg_result = subprocess.run([tool, '-a', file_path], capture_output=True, text=True, timeout=30)
                    elif tool == "outguess":
                        steg_result = subprocess.run([tool, '-r', file_path, '/tmp/outguess_output'], capture_output=True, text=True, timeout=30)

                    if steg_result and steg_result.returncode == 0 and steg_result.stdout.strip():
                        results["steganography_results"].append({
                            "tool": tool,
                            "output": steg_result.stdout
                        })
                except Exception as e:
                    results["steganography_results"].append({
                        "tool": tool,
                        "error": str(e)
                    })

        # Strings analysis
        try:
            strings_result = subprocess.run(['strings', file_path], capture_output=True, text=True, timeout=30)
            if strings_result.returncode == 0:
                interesting_strings = []
                for line in strings_result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['flag', 'password', 'key', 'secret', 'http', 'ftp']):
                        interesting_strings.append(line.strip())

                if interesting_strings:
                    results["hidden_data"].append({
                        "tool": "strings",
                        "interesting_strings": interesting_strings[:20]
                    })
        except Exception as e:
            results["hidden_data"].append({
                "tool": "strings",
                "error": str(e)
            })

        logger.info(f"🔍 CTF forensics analysis completed | File: {file_path} | Tools used: {len(results['recommended_tools'])}")
        return jsonify({
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF forensics analyzer: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
