from flask import Blueprint, request, jsonify
from server_core.singletons import wordlist_store

api_wordlist_store_bp = Blueprint("wordlist_store", __name__)

@api_wordlist_store_bp.route("/api/wordlists/<wordlist_id>", methods=["GET"])
def get_wordlist(wordlist_id):
    """
    Retrieve a specific wordlist entry by its ID.

    Args:
        wordlist_id (str): The unique identifier of the wordlist.

    Returns:
        JSON object containing the wordlist information if found, or an error message with a 404 status if not found.
    """
    wordlist = wordlist_store.load(wordlist_id)
    if wordlist is None:
        return jsonify({"error": "Wordlist not found"}), 404
    return jsonify(wordlist)

@api_wordlist_store_bp.route("/api/wordlists", methods=["GET"])
def get_all_wordlists():
    """
    Retrieve all wordlist entries.

    Returns:
        JSON array containing all wordlist entries.
    """
    wordlists = wordlist_store.load_all()
    return jsonify(wordlists)

@api_wordlist_store_bp.route("/api/wordlists/<wordlist_id>/path", methods=["GET"])
def get_wordlist_path(wordlist_id):
    """
    Retrieve the file path for a specific wordlist by its ID.

    Args:
        wordlist_id (str): The unique identifier of the wordlist.

    Returns:
        JSON object containing the file path if found, or an error message with a 404 status if not found or missing path.
    """
    path = wordlist_store.getPath(wordlist_id)
    if path is None:
        return jsonify({"error": "Wordlist not found or missing path"}), 404
    return jsonify(path)

@api_wordlist_store_bp.route("/api/wordlists/bestmatch", methods=["POST"])
def find_best_wordlist():
    """
    Find the best matching wordlist based on provided criteria.

    Request Body:
        JSON object containing search criteria for the wordlist.

    Example Criteria:
    {
        "type": "password",
        "recommended_for": ["brute-force", "credential-stuffing"],
        "speed": "fast"
    }

    Returns:
        JSON object containing the best matching wordlist, or an error message with a 404 status if no match is found.
    """
    criteria = request.get_json()
    if not criteria:
        return jsonify({"error": "Missing criteria"}), 400
    best_match = wordlist_store.find_best_match(criteria)
    if best_match is None:
        return jsonify({"error": "No matching wordlist found"}), 404
    return jsonify(best_match)

@api_wordlist_store_bp.route("/api/wordlists/<wordlist_id>", methods=["POST"])
def save_wordlist(wordlist_id):
    """
    Save or update a wordlist entry in the wordlists.json file in the correct format.

    The wordlist_info dict must follow the scheme as defined in config.py:
        {
            "path": <str>,           # Absolute path to the wordlist file
            "type": <str>,           # 'password' or 'directory' etc.
            "description": <str>,    # Description of the wordlist
            "recommended_for": <list>, # List of recommended use cases
            "size": <int>,           # Size of the wordlist (number of entries)
            "tool": <list>,          # Tools that use this wordlist
            "speed": <str>,          # Speed category ('fast', 'medium', 'slow')
            "language": <str>,       # Language of the wordlist
            "coverage": <str>,       # Coverage type ('broad', 'focused' etc.)
            "format": <str>,         # File format (e.g., 'txt', 'lst')
        }
    At minimum, 'path' and 'type' are required.
    """
    wordlist_info = request.get_json()
    if not wordlist_info:
        return jsonify({"error": "Missing wordlist info"}), 400
    success = wordlist_store.save(wordlist_id, wordlist_info)
    if not success:
        return jsonify({"error": "Failed to save wordlist"}), 500
    return jsonify({"status": "success"})

@api_wordlist_store_bp.route("/api/wordlists/<wordlist_id>", methods=["DELETE"])
def delete_wordlist(wordlist_id):
    """
    Delete a specific wordlist entry by its ID.

    Args:
        wordlist_id (str): The unique identifier of the wordlist.

    Returns:
        JSON object indicating success, or an error message with a 500 status if deletion fails.
    """
    success = wordlist_store.delete(wordlist_id)
    if not success:
        return jsonify({"error": "Failed to delete wordlist"}), 500
    return jsonify({"status": "success"})   