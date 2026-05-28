# Electric Aircraft Design Example

This repository contains Jupyter notebooks and helper Python modules for the EADG worked examples. Workshop participants will mainly use:

`E_19_Worked_Example.ipynb`

## Requirements

To be able to run the notebook, install:

- Python 3.10 or newer. Python 3.11 is recommended.
- Jupyter Notebook or JupyterLab
- The Python packages listed in `requirements.txt`

The main packages used by the notebook are:

- `numpy`
- `pandas`
- `matplotlib`
- `ipython`
- `jupyterlab`
- `ipykernel`

## Installation Instructions

## Option 1: Recommended Beginner Installation With Anaconda

This is the easiest route if you have never installed Python or Jupyter before.

### Step 1: Download Anaconda

1. Go to the Anaconda download page: <https://www.anaconda.com/download>
2. Download the installer for your operating system: Windows, macOS, or Linux.
3. Run the installer.
4. When asked, accept the default installation options.

On Windows, you do not need to add Anaconda to PATH unless you already know what that means.

### Step 2: Download This Repository

1. Open the GitHub page for this repository.
2. Click the green `Code` button.
3. Click `Download ZIP`.
4. Save the ZIP file somewhere easy to find, such as your Desktop or Downloads folder.
5. Right-click the ZIP file and choose `Extract All...` or `Unzip`.
6. Open the extracted folder.

### Step 3: Open Anaconda Navigator

1. Open `Anaconda Navigator`.
2. Launch `JupyterLab`.
3. JupyterLab will open in your web browser.

### Step 4: Navigate to the Notebook

In JupyterLab:

1. Use the file browser on the left side.
2. Navigate to the extracted repository folder.
3. Open `E-19_Simplified_electric_standard_assumptions_new_W_P_sizing.ipynb`.

### Step 5: Install the Required Packages

In JupyterLab:

1. Click `File` > `New` > `Terminal`.
2. In the terminal, make sure you are in the repository folder. If you opened the terminal from inside the folder, you should already be there.
3. Run:

```bash
pip install -r requirements.txt
```

Wait until the installation finishes. This may take a few minutes.

### Step 6: Run the Notebook

1. Open `E-19_Simplified_electric_standard_assumptions_new_W_P_sizing.ipynb`.
2. In the top menu, click `Run` > `Run All Cells`.
3. If Jupyter asks you to choose a kernel, select the Python kernel from your Anaconda installation.

If the notebook runs without red error messages, the installation is working.

## Option 2: Recommended Installation Without Anaconda

Use this option if you do not want to install Anaconda. This installs regular Python from Python.org, then installs JupyterLab and the required packages using `pip`, Python's package installer.

This option is a good choice if you want a smaller installation than Anaconda.

### Step 1: Install Python

1. Go to <https://www.python.org/downloads/>
2. Download Python 3.11 or newer.
3. Run the installer.
4. On Windows, check the box that says `Add python.exe to PATH`. This checkbox is important.
5. Continue with the default installation options.

After installing, close and reopen your terminal or command prompt.

To check that Python installed correctly, open a terminal or command prompt and run:

```bash
python --version
```

You should see something like:

```text
Python 3.11.x
```

If `python --version` does not work on Windows, try:

```bash
py --version
```

If `py --version` works but `python --version` does not, replace `python` with `py` in the commands below.

### Step 2: Download This Repository

1. Open the GitHub page for this repository.
2. Click the green `Code` button.
3. Click `Download ZIP`.
4. Extract the ZIP file.
5. Open the extracted folder.

### Step 3: Open a Terminal in the Folder

On Windows:

1. Open the extracted repository folder in File Explorer.
2. Click the address bar at the top.
3. Type `cmd` and press Enter.

On macOS:

1. Open the extracted repository folder in Finder.
2. Right-click the folder and choose `New Terminal at Folder`, if available.
3. If that option is not available, open Terminal and use `cd` to move into the folder.

### Step 4: Create a Virtual Environment

This step creates a small, separate Python environment just for this workshop. It helps avoid conflicts with other Python projects on your computer.

Run:

```bash
python -m venv .venv
```

Activate it.

On Windows:

```bash
.venv\Scripts\activate
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

### Step 5: Install the Required Packages

Run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

This installs JupyterLab plus the scientific Python packages needed by the notebook.

### Step 6: Start JupyterLab

Run:

```bash
jupyter lab
```

JupyterLab should open in your web browser. Open:

`E_19_Worked_Example.ipynb.ipynb`

Then click `Run` > `Run All Cells`.

### Optional Simpler No-Anaconda Method

If you are comfortable installing packages directly into your main Python installation, you can skip the virtual environment step and run only:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
jupyter lab
```

The virtual environment method above is still recommended because it keeps the workshop installation separate from other Python work.

## Option 3: Advanced Installation With conda

If you already use conda or Miniconda, create a clean environment:

```bash
conda create -n eadg-workshop python=3.11
conda activate eadg-workshop
pip install -r requirements.txt
jupyter lab
```

Then open:

`E_19_Worked_Example.ipynb.ipynb`

## Option 4: Advanced Installation With venv

If you already have Python installed:

```bash
python -m venv .venv
```

Activate the environment.

Windows:

```bash
.venv\Scripts\activate
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies and start JupyterLab:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
jupyter lab
```

## Quick Test

After installation, open the main notebook and run all cells:

`E_19_Worked_Example.ipynb.ipynb`

The notebook should run using the Python files included in this repository, such as:

- `mission_utils.py`
- `class_1_aero.py`
- `SMP.py`
- `SMP_W_P.py`
- `powertrain_component_sizing.py`
- `special_functions.py`
- `class_1_sizing.py`
- `class_2_airframe_structure.py`
- `systems_simplified.py`
- `class_2_systems.py`
- `class_2_prop_parallel_hybrid.py`
- `class_2_battery_sizing.py`

Keep these `.py` files in the same folder as the notebook.

## Troubleshooting

### `python` is not recognized

Python is either not installed or was not added to PATH.

- If using Anaconda, open `Anaconda Prompt` or launch JupyterLab from `Anaconda Navigator`.
- If using Python.org on Windows, reinstall Python and check `Add python.exe to PATH`.

### `No module named pandas`, `numpy`, or `matplotlib`

The dependencies were not installed in the Python environment being used by Jupyter.

Run this from the repository folder:

```bash
python -m pip install -r requirements.txt
```

Then restart JupyterLab and run the notebook again.

### `No module named mission_utils` or another local module

Jupyter is probably not running from the repository folder, or the notebook was moved away from the helper `.py` files.

Make sure the notebook and all the `.py` files remain together in the extracted repository folder.

### The notebook opens, but it uses the wrong Python kernel

In JupyterLab:

1. Click the kernel name in the upper-right corner of the notebook.
2. Select the Python environment where you installed the requirements.
3. Restart the kernel.
4. Run the notebook again.

## Simple Install Summary

For a workshop, the simplest participant workflow is:

1. Install Anaconda.
2. Download the repository as a ZIP file.
3. Extract the ZIP file.
4. Launch JupyterLab from Anaconda Navigator.
5. Open the extracted repository folder.
6. Run `pip install -r requirements.txt` in a JupyterLab terminal.
7. Open and run `E_19_Worked_Example.ipynb`.
