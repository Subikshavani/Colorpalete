'''from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import sqlite3
import json
from datetime import datetime
from PIL import Image
import numpy as np

app = Flask(__name__)

# Database Path
DB_PATH = "palettes.db"

# Ensure download folder exists
DOWNLOAD_DIR = "static/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ---------------------------------------------------
# DB INITIALIZATION
# ---------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            created_at TEXT,
            palette_json TEXT,
            average_rgb TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------------------------------------------
# UTILITY: HEX <-> RGB
# ---------------------------------------------------
def hex_to_rgb(hexcode):
    hexcode = hexcode.lstrip('#')
    if len(hexcode) == 3:
        hexcode = ''.join([v * 2 for v in hexcode])
    return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ---------------------------------------------------
# UTILITY: COLOR DISTANCE
# ---------------------------------------------------
def color_distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


# ---------------------------------------------------
# EXTRACT PALETTE USING K-MEANS-LIKE APPROACH
# ---------------------------------------------------
def extract_palette(image_path, n_colors=5):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((200, 200))
    pixels = np.array(img).reshape(-1, 3)

    # Simple centroid clustering
    rng = np.random.default_rng()
    centroids = pixels[rng.choice(len(pixels), n_colors, replace=False)]

    for _ in range(8):
        distances = np.sqrt(((pixels[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2))
        labels = np.argmin(distances, axis=1)
        for i in range(n_colors):
            group = pixels[labels == i]
            if len(group) > 0:
                centroids[i] = group.mean(axis=0)

    palette = [{"rgb": tuple(map(int, c)), "hex": rgb_to_hex(tuple(map(int, c)))} for c in centroids]

    average_color = tuple(map(int, pixels.mean(axis=0)))
    return palette, average_color


# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gradients")
def gradients():
    return render_template("gradients.html")


@app.route("/theme")
def theme():
    return render_template("theme.html")


@app.route("/history")
def history():
    return render_template("history.html")


# ---------------------------------------------------
# API: UPLOAD + EXTRACT PALETTE
# ---------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file name"}), 400

    filepath = os.path.join("static/uploads", file.filename)
    os.makedirs("static/uploads", exist_ok=True)
    file.save(filepath)

    palette, avg_color = extract_palette(filepath)

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO palettes (filename, created_at, palette_json, average_rgb)
        VALUES (?, ?, ?, ?)
    """, (
        file.filename,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json.dumps(palette),
        json.dumps(avg_color)
    ))
    conn.commit()
    pid = c.lastrowid
    conn.close()

    # Create downloadable JSON + PNG
    json_path = f"{DOWNLOAD_DIR}/palette_{pid}.json"
    png_path = f"{DOWNLOAD_DIR}/palette_{pid}.png"

    # Save JSON
    with open(json_path, "w") as f:
        json.dump({"palette": palette, "average": avg_color}, f, indent=4)

    # Create PNG preview
    block = Image.new("RGB", (500, 100))
    w = 500 // len(palette)

    for i, col in enumerate(palette):
        part = Image.new("RGB", (w, 100), tuple(col["rgb"]))
        block.paste(part, (i * w, 0))

    block.save(png_path)

    return jsonify({
        "success": True,
        "id": pid,
        "filename": file.filename,
        "palette": palette,
        "average": avg_color,
        "json_url": url_for('static', filename=f"downloads/palette_{pid}.json"),
        "png_url": url_for('static', filename=f"downloads/palette_{pid}.png")
    })


# ---------------------------------------------------
# API: GET PALETTES (SEARCH + FILTER)  **FIXED**
# ---------------------------------------------------
@app.route("/api/palettes")
def api_palettes():
    search = request.args.get("search", "").lower()
    color_filter = request.args.get("color")
    color_filter_rgb = hex_to_rgb(color_filter) if color_filter else None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, created_at, palette_json, average_rgb FROM palettes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    items = []
    for r in rows:
        pid, fname, created_at, palette_json, avg_rgb = r

        # search filter
        if search and search not in fname.lower():
            continue

        try:
            palette = json.loads(palette_json)
        except:
            palette = []

        # color filter (IGNORE default black)
        if color_filter_rgb and color_filter.lower() != "#000000":
            found = any(color_distance(color_filter_rgb, tuple(p['rgb'])) < 50 for p in palette)
            if not found:
                continue

        try:
            avg = json.loads(avg_rgb)
        except:
            avg = None

        items.append({
            "id": pid,
            "filename": fname,
            "created_at": created_at,
            "average": {"rgb": avg, "hex": rgb_to_hex(tuple(avg))} if avg else None,
            "json_url": url_for('static', filename=f"downloads/palette_{pid}.json"),
            "png_url": url_for('static', filename=f"downloads/palette_{pid}.png")
        })

    return jsonify({"palettes": items})


# ---------------------------------------------------
# API: DELETE ENTRY
# ---------------------------------------------------
@app.route("/api/delete/<int:pid>", methods=["DELETE"])
def api_delete(pid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM palettes WHERE id=?", (pid,))
    conn.commit()
    conn.close()

    # delete files
    try:
        os.remove(f"{DOWNLOAD_DIR}/palette_{pid}.json")
        os.remove(f"{DOWNLOAD_DIR}/palette_{pid}.png")
    except:
        pass

    return jsonify({"success": True})


# ---------------------------------------------------
# RUN SERVER
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

'''
from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
import sqlite3
import json
from datetime import datetime
from PIL import Image
import numpy as np

app = Flask(__name__)

# Database Path
DB_PATH = "palettes.db"

# Ensure download folder exists
DOWNLOAD_DIR = "static/downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# ---------------------------------------------------
# DB INITIALIZATION
# ---------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS palettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            created_at TEXT,
            palette_json TEXT,
            average_rgb TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


# ---------------------------------------------------
# UTILITY: HEX <-> RGB
# ---------------------------------------------------
def hex_to_rgb(hexcode):
    hexcode = hexcode.lstrip('#')
    if len(hexcode) == 3:
        hexcode = ''.join([v * 2 for v in hexcode])
    return tuple(int(hexcode[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)


# ---------------------------------------------------
# UTILITY: COLOR DISTANCE
# ---------------------------------------------------
def color_distance(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


# ---------------------------------------------------
# EXTRACT PALETTE USING K-MEANS-LIKE APPROACH
# ---------------------------------------------------
def extract_palette(image_path, n_colors=5):
    img = Image.open(image_path).convert("RGB")
    img = img.resize((200, 200))
    pixels = np.array(img).reshape(-1, 3)

    rng = np.random.default_rng()
    centroids = pixels[rng.choice(len(pixels), n_colors, replace=False)]

    for _ in range(8):
        distances = np.sqrt(((pixels[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2))
        labels = np.argmin(distances, axis=1)
        for i in range(n_colors):
            group = pixels[labels == i]
            if len(group) > 0:
                centroids[i] = group.mean(axis=0)

    palette = [{"rgb": tuple(map(int, c)), "hex": rgb_to_hex(tuple(map(int, c)))} for c in centroids]
    average_color = tuple(map(int, pixels.mean(axis=0)))
    return palette, average_color


# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/gradients")
def gradients():
    return render_template("gradients.html")


@app.route("/theme")
def theme():
    return render_template("theme.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/brandkit")
def brandkit():
    # Example brand colors
    brand = {
        "background": "#1e293b",
        "text": "#ffffff",
        "primary": "#ff416c",
        "accent": "#ff4b2b",
        "secondary": "#00c6ff"
    }
    return render_template("brandkit.html", brand=brand)


# ---------------------------------------------------
# API: UPLOAD + EXTRACT PALETTE
# ---------------------------------------------------
@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file name"}), 400

    filepath = os.path.join("static/uploads", file.filename)
    os.makedirs("static/uploads", exist_ok=True)
    file.save(filepath)

    palette, avg_color = extract_palette(filepath)

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO palettes (filename, created_at, palette_json, average_rgb)
        VALUES (?, ?, ?, ?)
    """, (
        file.filename,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        json.dumps(palette),
        json.dumps(avg_color)
    ))
    conn.commit()
    pid = c.lastrowid
    conn.close()

    # Create downloadable JSON + PNG
    json_path = f"{DOWNLOAD_DIR}/palette_{pid}.json"
    png_path = f"{DOWNLOAD_DIR}/palette_{pid}.png"

    with open(json_path, "w") as f:
        json.dump({"palette": palette, "average": avg_color}, f, indent=4)

    block = Image.new("RGB", (500, 100))
    w = 500 // len(palette)

    for i, col in enumerate(palette):
        part = Image.new("RGB", (w, 100), tuple(col["rgb"]))
        block.paste(part, (i * w, 0))

    block.save(png_path)

    return jsonify({
        "success": True,
        "id": pid,
        "filename": file.filename,
        "palette": palette,
        "average": avg_color,
        "json_url": url_for('static', filename=f"downloads/palette_{pid}.json"),
        "png_url": url_for('static', filename=f"downloads/palette_{pid}.png")
    })


# ---------------------------------------------------
# API: GET PALETTES
# ---------------------------------------------------
@app.route("/api/palettes")
def api_palettes():
    search = request.args.get("search", "").lower()
    color_filter = request.args.get("color")
    color_filter_rgb = hex_to_rgb(color_filter) if color_filter else None

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, created_at, palette_json, average_rgb FROM palettes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    items = []
    for r in rows:
        pid, fname, created_at, palette_json, avg_rgb = r

        if search and search not in fname.lower():
            continue

        try:
            palette = json.loads(palette_json)
        except:
            palette = []

        if color_filter_rgb and color_filter.lower() != "#000000":
            found = any(color_distance(color_filter_rgb, tuple(p['rgb'])) < 50 for p in palette)
            if not found:
                continue

        try:
            avg = json.loads(avg_rgb)
        except:
            avg = None

        items.append({
            "id": pid,
            "filename": fname,
            "created_at": created_at,
            "average": {"rgb": avg, "hex": rgb_to_hex(tuple(avg))} if avg else None,
            "json_url": url_for('static', filename=f"downloads/palette_{pid}.json"),
            "png_url": url_for('static', filename=f"downloads/palette_{pid}.png")
        })

    return jsonify({"palettes": items})


# ---------------------------------------------------
# API: DELETE ENTRY
# ---------------------------------------------------
@app.route("/api/delete/<int:pid>", methods=["DELETE"])
def api_delete(pid):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM palettes WHERE id=?", (pid,))
    conn.commit()
    conn.close()

    try:
        os.remove(f"{DOWNLOAD_DIR}/palette_{pid}.json")
        os.remove(f"{DOWNLOAD_DIR}/palette_{pid}.png")
    except:
        pass

    return jsonify({"success": True})


# ---------------------------------------------------
# RUN SERVER
# ---------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
