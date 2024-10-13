# csgo-demo-parsing
 
A set of Python scripts you can use to create CSV files (and some GIFs, optionally) through which to examine CSGO game demo files.

## Installation
You should probably make a virtual environment first. See [the Python venv documentation](https://docs.python.org/3/library/venv.html).

But basically (if you're on Windows) navigate to the root directory of the project and open your terminal, typing:

`python -m venv .venv` to create the virtual environment folder, then

`.\venv\Scripts\activate` to activate the virtual environment.

Then, install the requirements:

`pip install -r requirements.txt`

## Usage
You can run the `cli.py` file with a Python interpreter or you can run the `generate-exe.sh` file (after modifying the contents to match your local file system and not mine) to create an executable file that you can port to machines that don't have Python installed.

The `gui.py` file is not up to date with all of the features of the `cli.py` file (and I'm not entirely sure it even works at the moment) but I'm including it for progeny.

The `parsing.ipynb` file was something I used to figure out what I was doing.

The other `.py` files support the `cli.py` and `gui.py` code.
