<p align="center">
  <img src="assets/logo.png" height="120">
</p>

<h1 align="center">Face Registration and Search System</h1>

<p align="center">
A lightweight face registration and search system built with <b>FastAPI</b>, <b>SQLite</b>, and the <b>face_recognition</b> library.
Designed for small-scale deployments where fast face lookup and simple administration are required.
</p>

---

## 📖 Overview

This project provides a lightweight facial recognition system capable of registering and searching faces in real time.

The system is optimized for datasets containing approximately **30 registered individuals**. Face embeddings are permanently stored in **SQLite**, while an in-memory cache is maintained for extremely fast searches.

Only authenticated administrators are allowed to register new faces.

Whenever a new face is registered:

* The image is encoded immediately.
* The embedding is saved into SQLite.
* The RAM cache is updated instantly.
* The new person becomes searchable without restarting the application.

Additionally, a background scheduler synchronizes the RAM cache with the database every **5 minutes**.

---

# ✨ Features

* 🔐 Administrator-only face registration
* 👤 Real-time face search
* ⚡ RAM-based face embedding cache
* 💾 SQLite persistent storage
* 🔄 Automatic cache synchronization
* 🚀 FastAPI backend
* 📁 Lightweight architecture
* 🖥️ Suitable for local deployment

---

# 📂 Project Structure

```text
face-search-python/
│
├── assets/                    # Project images and logo
│   └── logo.png
│
├── data/
│   ├── faces.db               # SQLite database
│   └── uploads/               # Registered face images
│
├── admin_information.json     # Administrator credentials
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
└── README.md
```

---

# 🔧 Requirements

* Python 3.11
* Windows / Linux
* SQLite

It is recommended to use a virtual environment.

---

# 📦 Installation

Clone the repository

```bash
git clone https://github.com/monashahriari/face-search-python.git

cd face-search-python
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Windows

```powershell
.venv\Scripts\activate
```

Linux

```bash
source .venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# 🚀 Run the Application

Start the FastAPI server

```bash
uvicorn main:app --reload
```

Open your browser

```
http://127.0.0.1:8000
```

---

# 🔑 Administrator Account

Administrator credentials are stored inside

```
admin_information.json
```

Example

```json
{
    "username": "admin",
    "password": "ChangeMe123!"
}
```

For security reasons, change the default password before using the application.

---

# ⚙️ Optional Configuration

Environment variables

```powershell
$env:SYNC_MINUTES="5"
$env:MATCH_THRESHOLD="0.50"

uvicorn main:app
```

| Variable        | Description                           |
| --------------- | ------------------------------------- |
| SYNC_MINUTES    | Interval for rebuilding the RAM cache |
| MATCH_THRESHOLD | Face matching threshold               |

---

# 🚀 Usage

1. Login as Administrator.
2. Open the **Management** page.
3. Register face images.
4. Each image should contain exactly one clear frontal face.
5. Once registered, the face becomes immediately searchable.

---

# 🔒 Security Notes

* Register faces only with the person's consent.
* Protect administrator credentials.
* Restrict server access.
* Enable HTTPS in production.
* Use secure session management.
* Regularly back up the SQLite database.

---

# 📌 Limitations

* Intended for approximately 30 registered individuals.
* Designed for local or educational deployments.
* Uses the `face_recognition` library for feature extraction.
* Large-scale deployments should consider dedicated vector databases such as FAISS or Milvus.

---

# 📜 License

This project is intended for educational and research purposes.
