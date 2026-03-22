from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any

BROAD_GENRES = {
    "Hip-Hop",
    "R&B",
    "Raggae",
    "Latin",
    "Jazz",
    "Classical",
    "Country",
    "Rock",
    "Electronic Dance Music (EDM)",
    "Indie/Experimental",
    "Pop",
}



@dataclass
class Stage:
    name: str
    max_budget: float
    stage_genres: Optional[Set[str]] = None  # None if it is a Main stage
    performers: List[Dict[str, Any]] = field(default_factory=list)
    total_cost: float = 0.0
    sum_appeal: float = 0.0

    #Checks if Stage is main stage
    def is_main_stage(self) -> bool:
        return self.stage_genres is None

    #Checks whether an artist can perform based on the stage genre
    def can_host(self, artist_broad_genres: Set[str]):
        if self.is_main_stage():
            return True
        return len(artist_broad_genres.intersection(self.stage_genres)) > 0

    #Returns remaining budget
    def remaining_budget(self) -> float:
        return self.max_budget - self.total_cost

    # Adds a new performer to the stage and calculates remaining budget
    def add_performer(self, performer: Dict[str, Any]):
        cost = float(performer.get("cost_of_artist", 0.0))
        appeal = float(performer.get("appeal_score", 0.0))

        bg = performer.get("broad_genres", [])
        if isinstance(bg, list):
            artist_genres = set(bg)

        if not self.can_host(artist_genres):
            raise ValueError(f"Performer genres not allowed on stage")
        if self.total_cost + cost > self.max_budget:
            raise ValueError(f"Budget exceeded")
        self.performers.append(performer)
        self.total_cost += cost
        self.sum_appeal += appeal

    def to_dict(self):
        return {
            "name": self.name,
            "type": "Main" if self.is_main_stage() else "Genre",
            "stage_genres": None if self.is_main_stage() else sorted(self.stage_genres),
            "max_budget": self.max_budget,
            "total_cost": self.total_cost,
            "sum_appeal": self.sum_appeal,
            "n_performers": len(self.performers),
            "performers": self.performers,
        }

def make_main_stage(name: str, max_budget: float):
    return Stage(name=name, max_budget=max_budget, stage_genres=None)

def make_genre_stage(name: str, max_budget: float, genre: str):
    if genre not in BROAD_GENRES:
        raise ValueError("Unknown genre")
    
    return Stage(name=name, max_budget=max_budget, stage_genres={genre})

def make_multi_genre_stage(name: str, max_budget: float, genres: Set[str]):
    return Stage(name=name, max_budget=max_budget, stage_genres=set(genres))