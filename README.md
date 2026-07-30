<p align="center">
  <img src="assets/logo.png" height=120>
</p>

# Face Registration and Search System

A lightweight face registration and search system designed to support up to approximately 30 people. The application uses SQLite for persistent storage and an in-memory (RAM) cache for fast face search. Only the administrator can register new faces. Once a face is registered, it is immediately added to the RAM cache and becomes searchable without restarting the application. A background scheduler rebuilds the RAM cache from the database every 5 minutes.

## 🔧 Dependencies and Installation

- Python = 3.11 (Recommend to use [Anaconda](https://www.anaconda.com/download/#linux) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html))


### Installation

1. Clone repo

    ```bash
    git clone https://github.com/xinntao/Real-ESRGAN.git
    cd Real-ESRGAN
    ```

1. Install dependent packages

    ```bash
    # Install basicsr - https://github.com/xinntao/BasicSR
    # We use BasicSR for both training and inference
    pip install basicsr
    # facexlib and gfpgan are for face enhancement
    pip install facexlib
    pip install gfpgan
    pip install -r requirements.txt
    python setup.py develop
    ```

---

```powershell
cd face-search-python
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open:

```
http://127.0.0.1:8000
```

## Administrator Credentials

The administrator username and password are stored in the following file:

```
admin_information.json
```

Update the values in this file before running the application.

Example:

```json
{
    "username": "admin",
    "password": "ChangeMe123!"
}
```

## Getting Started

1. Log in as the administrator.
2. Open the **Management** page.
3. Register approximately 10 face images (with the person's consent).
4. Each image should contain exactly one clear, front-facing face.
5. Once a face is registered, it is immediately added to the RAM cache and can be searched without restarting the server.

## Optional Configuration

```powershell
$env:SYNC_MINUTES = "5"       # Interval (in minutes) for rebuilding the RAM cache from SQLite
$env:MATCH_THRESHOLD = "0.50" # Lower values make matching more strict
uvicorn main:app
```

## Notes and Security

- Always obtain the person's consent before registering their face.
- Restrict access to the server and administrator account.
- This project is intended for local or educational use.
- For production deployments, you should enable HTTPS, use secure session management, change the default administrator password, log security events, and implement secure deletion of personal data.
- The `face_recognition` library may require **Visual C++ Build Tools** and **dlib** on some Windows systems. If installation fails, use **Python 3.11**, install the required C++ build tools, or run the project in a Linux/Docker environment.