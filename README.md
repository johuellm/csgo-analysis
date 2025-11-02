# csgo-analysis

Analyze Counter-Strike: Global Offensive demos,
annotate tactics, and run graph neural network predictions.

`stats.py` and `ui\cli.py` are rather outdated.
The most recent version is `gui_app.py`.




## Installation

The suggested python version is `3.12.x`.

It is recommended to [create and activate a virtual environment](https://docs.python.org/3/tutorial/venv.html).

Requires awpy 1.3.1 @ https://github.com/pnxenopoulos/awpy/tree/f0bbee8a2b95d650210f34f70468f6b2457a6e4d

Due to broken dependencies in old awpy, install it in pip via argument `--no-deps`.

```bash
# add deadsnakes because of python3 versions
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev python3.12-tk

git clone https://github.com/johuellm/csgo-analysis
cd csgo-analysis

python3.12 -m venv venv

venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/pip install --no-deps awpy==1.3.1
```



## Usage

Run the GUI.
```bash
# in csgo-analysis root folder
cp ".env.example" ".env"
PYTHONPATH=src/ venv/bin/python src/gui_app.py
```

