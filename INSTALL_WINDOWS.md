# Cell Counter — Windows Installation Guide

Follow these steps in order. Each step includes screenshots descriptions so you know what to expect.

---

## Step 1 — Download the app

1. Open your web browser and go to:
   ```
   https://github.com/fruscitti/cells_counting/archive/refs/heads/local-ui.zip
   ```
2. The file **local-ui.zip** will download automatically (check your Downloads folder).
3. Open File Explorer and go to your **Downloads** folder.
4. Right-click **local-ui.zip** → **Extract All…**
5. Choose a destination folder, for example `C:\CellCounter`, then click **Extract**.
6. You should now have a folder called `cells_counting-local-ui` inside your chosen location.

---

## Step 2 — Install Python 3.11

1. Open your web browser and go to:
   ```
   https://www.python.org/downloads/release/python-3119/
   ```
2. Scroll down to **Files** and click **Windows installer (64-bit)** to download it.
3. Run the installer (`python-3.11.9-amd64.exe`).
4. **Important:** On the first screen, check the box **"Add python.exe to PATH"** at the bottom before clicking anything else.
5. Click **Install Now** and wait for it to finish.
6. Click **Close** when done.

---

## Step 3 — Open a terminal in the app folder

1. Open **File Explorer** and navigate to the folder you extracted in Step 1
   (e.g. `C:\CellCounter\cells_counting-local-ui`).
2. Click on the address bar at the top of File Explorer (it shows the folder path).
3. Type `cmd` and press **Enter**. A black terminal window will open in that folder.

---

## Step 4 — Install dependencies

Copy and paste each command below into the terminal, pressing **Enter** after each one.

**Create a virtual environment:**
```
python -m venv .venv
```

**Activate the virtual environment:**
```
.venv\Scripts\activate
```

You should see `(.venv)` appear at the start of the line — this means it is active.

**Install required packages:**
```
pip install PySide6 opencv-python pandas numpy
```

This will download and install everything needed. It may take a few minutes depending on your internet connection.

---

## Step 5 — Run the app

In the same terminal window (with `(.venv)` still visible), type:

```
python app.py
```

The Cell Counter window will open.

---

## Running the app again later

You do not need to repeat Steps 1–4. Next time:

1. Open **File Explorer**, navigate to the app folder.
2. Click the address bar, type `cmd`, press **Enter**.
3. In the terminal, run:
   ```
   .venv\Scripts\activate
   python app.py
   ```

---

## Troubleshooting

**"python is not recognized as a command"**
Python was not added to PATH. Uninstall Python and reinstall it, making sure to check **"Add python.exe to PATH"** on the first screen.

**"pip install" fails with a network error**
Check your internet connection and try again. If you are behind a corporate proxy, contact your IT department.

**The app opens but shows an error about a missing file**
Make sure you are running `python app.py` from inside the `cells_counting-local-ui` folder (Step 3).

**The window opens but images do not load**
Only `.tif`, `.tiff`, `.png`, and `.jpg` files are supported. Make sure your images are in one of these formats.
