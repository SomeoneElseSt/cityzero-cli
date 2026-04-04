"""Configuration management for Mapillary client and CLI downloader."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATA_DIR = Path.cwd()

# Normalizes DB and EXIF coords to the same precision so == comparisons work exactly.
# 10^7 = 7 decimal places (~1cm); fits in uint32 for both lat and lon.
GPS_COORD_PRECISION = 10_000_000

# Downloader / API constants
MAX_RESOLUTION = 2048
API_IMAGE_LIMIT = 2000
# Note: 50 and 50 workers were found to be empirically fastest without running into I/O limits
# Feel free to increment until whatever your system can handle
DISCOVERY_WORKERS = 50
DOWNLOAD_WORKERS = 50
DB_COMMIT_BATCH = 50
DISCOVERY_STALENESS_DAYS = 21
GRANULARITY_MIN = 1
GRANULARITY_MAX = 100
GRANULARITY_DEFAULT = 25

BBOX_SLUG_WORDS = [
    "acid","agate","amber","anvil","arch","ark","ash","axe",
    "badge","bark","basalt","bay","beam","birch","blade","bloom",
    "bolt","bone","boulder","brace","braid","branch","brass","brick",
    "bridge","brine","bronze","brook","brush","bulwark","cairn","cape",
    "carbon","cave","cedar","chalk","chart","chest","chrome","cinder",
    "circuit","cliff","cloak","cloud","coal","coast","cobalt","coil",
    "compass","copper","coral","cord","core","crag","crane","crater",
    "creek","crest","crown","crystal","current","dart","dawn","delta",
    "depth","dew","dome","drift","dusk","dust","dye","echo",
    "edge","ember","epoch","fang","fell","fen","fern","field",
    "fig","film","fjord","flare","flint","flood","flow","foam",
    "fold","forge","fork","fort","frost","fuel","gale","gap",
    "gate","gem","gild","glacier","glade","glow","gorge","grain",
    "granite","grove","gulf","haze","heath","helm","hemp","hill",
    "hive","hollow","hook","horizon","hull","ice","inlet","iron",
    "island","jade","jasper","jet","keep","kelp","key","knot",
    "larch","lava","leaf","ledge","lens","lime","link","loch",
    "lode","loop","lumen","magma","mantle","maple","marble","marsh",
    "mast","mesa","mesh","mist","moat","moor","mortar","moss",
    "mount","mud","nacre","needle","node","north","notch","oak",
    "opal","orbit","ore","outcrop","pale","pass","patch","peak",
    "peat","pine","pitch","pivot","plain","plume","pool","port",
    "prism","probe","pulse","quartz","rail","range","rapid","reef",
    "relay","ridge","rift","rim","river","rock","root","rope",
    "ruin","rush","rust","salt","sand","scarp","schist","scree",
    "seal","seam","shelf","shale","shore","silt","sinew","slab",
    "slate","slope","smoke","soil","span","spire","spool","spur",
    "stack","staff","stave","steel","stem","step","stone","storm",
    "strand","stream","strut","summit","surge","swamp","sweep","swift",
    "tarn","thorn","tide","timber","tine","tor","trace","trail",
    "trench","tundra","vale","vault","vein","vent","verge","void",
    "wake","wave","weld","whirl","wind","wire","wood","zinc",
]

CITY_QUIPS = [
    "Somewhere in these pixels is a dog who had a great Tuesday.",
    "A stranger once stood exactly where your images were captured. Wild.",
    "Fun fact: most streets have never had a CLI tool care about them this much.",
    "Pro tip: if you stare at enough street images, you achieve enlightenment. Probably",
    "Pavement. Glorious, unsung, pavement.",
    "Some people travel the world. You're downloading it. Respect.",
    "The grid is a lie. But we're using it anyway.",
    "These streets have seen things. You're about to see them too.",
    "You could've gone outside instead. Bold choice.",
    "This is technically fieldwork.",
    "This data is free. The electricity to process is not. Carry on.",
    "One of these coordinates is someone's commute.",
    "A tree in one of these frames is older than the internet.",
    "Every pixel is a tiny opinion about light.",
    "Somewhere in these pictures is a perfect parking job immortalized.",
    "At least one of the roads you find here leads to Rome.",
    "Not all who wander are lost. Some are just rendering tiles.",
    "There is no such thing as boring. You just don't have enough zoom.",
    "Back to the concrete jungle(s).",
    "You could also go outside and touch grass. Just saying.",
    "You could be riding a bicycle like someone in these pictures.",
    "Fifty shades of gray, but it's just municipal sidewalk planning.",
    "This pixel is gray. The next pixel is gray. The system works.",
    "A celebration of humanity's victory over grass. Sort of.",
    "Your ancestors are watching you terminal-maxxing instead of touching grass. Worth it?",
    "Your ancestors are watching you batch-download intersections instead of continuing the bloodline. Worth it?"
    ]

@dataclass
class MapillaryConfig:
    """Mapillary API configuration."""

    client_token: str


@dataclass
class BoundingBox:
    """Geographic bounding box (west, south, east, north)."""
    
    west: float
    south: float
    east: float
    north: float
    
    @classmethod
    def from_string(cls, bbox_string: str) -> "BoundingBox | None":
        """Parse bounding box from comma-separated string, or None if invalid."""
        parts = bbox_string.split(",")
        if len(parts) != 4:
            return None
        try:
            return cls(west=float(parts[0]), south=float(parts[1]), east=float(parts[2]), north=float(parts[3]))
        except ValueError:
            return None
    
    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Return as tuple (west, south, east, north)."""
        return (self.west, self.south, self.east, self.north)


def get_mapillary_config() -> MapillaryConfig | None:
    """Get Mapillary configuration from environment, or None if token is missing."""
    token = os.getenv("MAPILLARY_CLIENT_TOKEN", "")
    if not token:
        return None
    return MapillaryConfig(client_token=token)


@dataclass
class GridParams:
    """Grid cell sizes derived from a granularity level."""
    grid_cell_size: float


def granularity_to_grid_params(level: int) -> GridParams:
    """Convert a 1–100 granularity level to a grid cell size (log scale)."""
    t = (level - GRANULARITY_MIN) / (GRANULARITY_MAX - GRANULARITY_MIN)
    grid = 0.5 * math.pow(0.0004, t)
    return GridParams(grid_cell_size=round(grid, 6))

# Predefined city bounding boxes (can be extended)
CITY_BBOXES: dict[str, BoundingBox] = {
    "san francisco": BoundingBox(
        west=-122.5147,
        south=37.7034,
        east=-122.3549,
        north=37.8324
    ),
    "new york": BoundingBox(
        west=-74.0479,
        south=40.6829,
        east=-73.9067,
        north=40.8820
    ),
    "los angeles": BoundingBox(
        west=-118.6682,
        south=33.7037,
        east=-118.1553,
        north=34.3373
    ),
    "chicago": BoundingBox(
        west=-87.9401,
        south=41.6444,
        east=-87.5241,
        north=42.0230
    ),
    "miami": BoundingBox(
        west=-80.3203,
        south=25.7090,
        east=-80.1300,
        north=25.8554
    ),
}
