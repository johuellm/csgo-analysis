# csgo-demo-visualizer
 Visualizing CS:GO demos for analysis purposes. A rework of this [csgo-analysis](https://github.com/samihan-m/csgo-analysis) [fork](https://github.com/johuellm/csgo-analysis) by [@johuellm](https://github.com/johuellm).

 Developed in Python `3.11.9` and Go `1.22.2`.

## Installation

Make sure the versions of Python and Go mentioned above are installed.

`pip install -r requirements.txt`

## Usage

🚧🚧 Still under construction. 🚧🚧

A limited glimpse of functionality can be seen by running the `cli.py` file. For example, if your current working directory is the root of the project:

`python src/cli.py`

## Updating dependencies

I used `pip-tools` to produce a `requirements.txt` file with exact versions of all dependencies pinned and hashed. This is to better ensure that a `pip install` to reproduce the environment doesn't fetch a different version of a dependency without our express intent.

To that end, any updates to `requirements.txt` should probably also involve `pip-tools` (see the `pip-tools` docs for the command I used [here](https://github.com/jazzband/pip-tools?tab=readme-ov-file#using-hashes)).