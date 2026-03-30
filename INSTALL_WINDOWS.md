# Cell Counter — Windows Installation Guide

---

## Quick install (recommended)

### Step 1 — Download the app

1. Open your web browser and go to:
   ```
   https://github.com/fruscitti/cells_counting/archive/refs/heads/local-ui.zip
   ```
2. The file **local-ui.zip** will download automatically (check your Downloads folder).
3. Open File Explorer and go to your **Downloads** folder.
4. Right-click **local-ui.zip** → **Extract All…**
5. Choose a destination folder, for example `C:\CellCounter`, then click **Extract**.
6. You will now have a folder called `cells_counting-local-ui` inside your chosen location.

### Step 2 — Run the setup script

1. Open the `cells_counting-local-ui` folder in File Explorer.
2. Double-click **setup.bat**.
3. If Windows shows a blue warning ("Windows protected your PC"), click **More info** → **Run anyway**.
4. A terminal window will open and install everything automatically. This may take a few minutes.
5. When you see **"Setup complete!"**, press any key to close the window.

### Step 3 — Launch the app

Double-click **run.bat** inside the same folder.

> Next time you want to open the app, just double-click **run.bat** — no setup needed again.

---

## Manual install (alternative)

Use this only if the setup script did not work.

### Step 1 — Download the app

Same as above.

### Step 2 — Install Python 3.11

1. Open your web browser and go to:
   ```
   https://www.python.org/downloads/release/python-3119/
   ```
2. Scroll down to **Files** and click **Windows installer (64-bit)**.
3. Run the installer (`python-3.11.9-amd64.exe`).
4. **Important:** On the first screen, check **"Add python.exe to PATH"** before clicking anything else.
5. Click **Install Now** and wait for it to finish, then click **Close**.

### Step 3 — Open a terminal in the app folder

1. Open File Explorer and navigate to the `cells_counting-local-ui` folder.
2. Click on the address bar at the top (it shows the folder path).
3. Type `cmd` and press **Enter**. A terminal window will open in that folder.

### Step 4 — Install dependencies

Type each command below and press **Enter** after each one:

```
python -m venv .venv
.venv\Scripts\activate
pip install PySide6 opencv-python pandas numpy
```

### Step 5 — Run the app

```
python app.py
```

---

## Troubleshooting

**Blue "Windows protected your PC" warning on setup.bat**
Click **More info** → **Run anyway**. This appears because the file was downloaded from the internet.

**"python is not recognized as a command"**
Python was not added to PATH. Uninstall Python and reinstall it, making sure to check **"Add python.exe to PATH"** on the first screen of the installer.

**setup.bat closes immediately without doing anything**
Right-click **setup.bat** → **Run as administrator** and try again.

**"pip install" fails with a network error**
Check your internet connection and try again. If you are on a corporate network, contact your IT department.

**The app opens but shows an error about a missing file**
Make sure `run.bat` and `setup.bat` are inside the `cells_counting-local-ui` folder, not moved elsewhere.

**The window opens but images do not load**
Only `.tif`, `.tiff`, `.png`, and `.jpg` files are supported.
