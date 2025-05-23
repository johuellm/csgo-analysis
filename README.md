# csgo-demo-visualizer

Visualizing CS:GO demos for analysis purposes. A rework of this [csgo-analysis](https://github.com/samihan-m/csgo-analysis) [fork](https://github.com/johuellm/csgo-analysis) by [@johuellm](https://github.com/johuellm).

Suggest python version is `3.12.x`.

## Installation

Make sure the versions of Python mentioned above are installed.

It is recommended to [create and activate a virtual environment](https://docs.python.org/3/tutorial/venv.html).

Requires awpy 1.3.1 @ https://github.com/pnxenopoulos/awpy/tree/f0bbee8a2b95d650210f34f70468f6b2457a6e4d

`pip install -r requirements.txt`

## Usage

🚧🚧 Still under construction. 🚧🚧

A limited glimpse of functionality can be seen by running the `cli.py` file. For example, if your current working directory is the root of the project:

`python src/cli.py`

The Tkinter application (very much under construction) can be run via the `gui.py` file. For example, if your current working directory is the root of the project:

`python src/gui.py`

Click the File button at the top, then Open. Select a demo file and the application will visualize the first frame of round 1. Click Play to watch the demo unfold, click on a round number to jump to that round, or scrub the timeline for finer control.

## Updating dependencies

I used `pip-tools` to produce a `requirements.txt` file with exact versions of all dependencies pinned and hashed. This is to better ensure that a `pip install` to reproduce the environment doesn't fetch a different version of a dependency without our express intent.

To that end, any updates to `requirements.txt` should probably also involve `pip-tools` (see the `pip-tools` docs for the command I used [here](https://github.com/jazzband/pip-tools?tab=readme-ov-file#using-hashes)).

