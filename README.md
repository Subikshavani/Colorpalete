🎨 Color Palette Generator & Brand Kit (Flask Project)

A full-stack Flask-based Color Palette Generator that extracts color palettes from images, stores them, visualizes history, generates gradients, themes, and provides a Brand Kit preview for UI/UX design inspiration.

✨ Features

📤 Upload image & extract dominant colors

🎨 Automatic color palette generation

🧮 Average color calculation

🖼️ Download palette as PNG & JSON

📜 Palette history with search & filter

🗑️ Delete palettes from history

🌈 Gradient generator page

🧩 Theme preview page

🧱 Brand Kit UI (buttons, cards, navbar preview)

🎯 3D-style modern UI

💾 SQLite database storage

🗂️ Project Structure
color_palate/
│
├── backend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   ├── downloads/
│   │   └── uploads/
│   │
│   ├── templates/
│   │   ├── index.html
│   │   ├── history.html
│   │   ├── gradients.html
│   │   ├── theme.html
│   │   ├── brandkit.html
│   │   └── details.html
│   │
│   ├── app.py
│   ├── palettes.db
│   └── database.db
│
├── venv/
├── requirements.txt
├── README.md
├── palette.png
└── backend.zip

🧠 Tech Stack

Backend: Python, Flask

Frontend: HTML, CSS, JavaScript

Database: SQLite

Image Processing: Pillow, NumPy

Styling: Modern CSS (3D UI, gradients)

⚙️ Installation & Setup
1️⃣ Clone the repository
git clone https://github.com/Subikshavani/Colorpalete.git
cd Colorpalete

2️⃣ Create & activate virtual environment
python -m venv venv
venv\Scripts\activate

3️⃣ Install dependencies
pip install -r requirements.txt


If Pillow error occurs:

pip install pillow numpy

▶️ Run the Application
cd backend
python app.py


Server will start at:

http://127.0.0.1:5000/

🌐 Available Pages
Page	URL
Home	/
History	/history
Gradients	/gradients
Theme	/theme
Brand Kit	/brandkit
