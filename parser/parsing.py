from awpy.parser import DemoParser
from awpy.types import Game


def parse_demo_file(demo_file_name: str) -> Game:
    """
    Given a demo file name, parse it and return the data
    """
    # 128 parse_rate ideally matches with the 128 ticks per second of the demo file to mean player position is polled every second
    p = DemoParser(demofile=demo_file_name, parse_rate=128, parse_frames=True)
    data = p.parse()
    return data
   