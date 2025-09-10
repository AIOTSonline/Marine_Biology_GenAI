# from flask import Flask, render_template, request, redirect, url_for, jsonify
# import requests
# import os

# # Your backend server (use test_server.py locally, server.py remotely)
# SERVER_URL = "http://127.0.0.1:5000"

# app = Flask(__name__)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         concept = request.form["concept"]
#         method = request.form.get("method", "genai")

#         # Call backend /generate
#         resp = requests.post(f"{SERVER_URL}/generate", json={"concept": concept, "method": method})
#         if resp.status_code != 200:
#             return f"Backend error: {resp.text}", 500

#         backend_data = resp.json()
#         if backend_data.get("status") != "done":
#             return f"Generation failed: {backend_data}", 500

#         # Redirect to results page with glb_files
#         return redirect(url_for("results_page", files=",".join(backend_data["glb_files"])))

#     return render_template("index.html", server_url=SERVER_URL)


# # @app.route("/results")
# # def results_page():
# #     """Show generated .glb files with download/viewer links"""
# #     files = request.args.get("files", "")
# #     file_list = files.split(",") if files else []
# #     file_links = [f"{SERVER_URL}/download/{fname}" for fname in file_list]
# #     return render_template("results.html", files=file_list, file_links=file_links)

# @app.route("/results")
# def results_page():
#     """Show generated .glb files with download/viewer links"""
#     files = request.args.get("files", "")
#     file_list = files.split(",") if files else []
#     file_links = [f"{SERVER_URL}/download/{fname}" for fname in file_list]
#     # Combine into one iterable for template
#     combined = list(zip(file_list, file_links))
#     return render_template("results.html", files_with_links=combined)


# @app.route("/api/generate", methods=["POST"])
# def api_generate():
#     """API endpoint for frontend JS to call backend generate"""
#     data = request.get_json(force=True)
#     concept = data.get("concept")
#     method = data.get("method", "genai")

#     if not concept:
#         return jsonify({"error": "Missing concept"}), 400

#     resp = requests.post(f"{SERVER_URL}/generate", json={"concept": concept, "method": method})
#     return jsonify(resp.json()), resp.status_code


# @app.route("/viewer/<filename>")
# def viewer(filename):
#     """Embed a GLB in a viewer page"""
#     mesh_url = f"{SERVER_URL}/download/{filename}"
#     return render_template("viewer.html", mesh_url=mesh_url)


# if __name__ == "__main__":
#     app.run(debug=True, port=8000)

from flask import Flask, render_template, request, jsonify
import requests
import logging

app = Flask(__name__)
SERVER_URL = "http://127.0.0.1:5000"

logging.basicConfig(level=logging.DEBUG)

@app.route("/")
def index():
    return render_template("index.html", server_url=SERVER_URL)

@app.route("/api/generate", methods=["POST"])
def api_generate():
    data = request.get_json(force=True)
    concept = data.get("concept")
    method = data.get("method", "genai")

    if not concept:
        return jsonify({"error": "Missing concept"}), 400

    try:
        resp = requests.post(f"{SERVER_URL}/generate", json={"concept": concept, "method": method})
        resp.raise_for_status()
        backend_data = resp.json()
        app.logger.debug(f"Backend response: {backend_data}")
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(backend_data), resp.status_code

@app.route("/viewer/<filename>")
def viewer(filename):
    return render_template("viewer.html", mesh_url=f"{SERVER_URL}/download/{filename}")

if __name__ == "__main__":
    app.run(port=8000, debug=True)
