"""Module for Computing Aggregates of the Converted DataFrame of demo File."""

import os

import pandas as pd

from demolyzer.demo_utils import demo_to_dataframe


class DemoAnalyzer:
    def __init__(self, demo_in_path: str, persist: bool = True):
        """Initialize an instance of a DemoAnalyzer.

        Args:
            demo_in_path: Path to demo file.
            persist: Persist converted demo as a csv as to not re-convert. Defaults to True.
        """
        csv_name = f"{os.path.splitext(demo_in_path)[0]}.csv"
        if persist and os.path.exists(csv_name):
            self.df = pd.read_csv(csv_name)
        else:
            self.df = demo_to_dataframe(demo_in_path)
            if persist:
                self.df.to_csv(csv_name, index=False)

        self.demo_file = demo_in_path

    @property
    def players(self) -> dict[str, str]:
        """Get the players in this file.

        Returns:
            dict of {steam_id: player_name}
        """
        unique_ids_df = self.df.drop_duplicates(subset="players_info.steamId")

        players = dict(zip(unique_ids_df["players_info.steamId"], unique_ids_df["players_info.name"]))

        return players

    @property
    def num_players(self) -> int:
        """Get the number of players in this demo file.

        Returns:
            number of players
        """
        return len(self.df["players_info.steamId"].unique())

    @property
    def duration(self) -> float:
        pass

    def death_stats(self) -> dict[str, dict[str, float | int]]:
        """Get the number of alive and death ticks for all players in a given demo.

        Returns:
            dict of {steam_id: {alive_ticks: int, death_ticks: int}}
        """
        stats = {}
        for steam_id, name in self.players.items():
            if pd.isna(steam_id):
                continue
            player_df = self.df[self.df["players_info.steamId"] == steam_id]
            tick_stats = player_df["players_state"].value_counts().to_dict()
            stats[steam_id] = {
                "alive_ticks": tick_stats.get("Alive", None),
                "death_ticks": tick_stats.get("Death", None),
            }

        return stats

    def __str__(self) -> str:
        return f"{self.demo_file} with {self.num_players} players and duration of {self.duration}"
