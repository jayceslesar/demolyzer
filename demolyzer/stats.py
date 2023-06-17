"""Module for Computing Aggregates of the Converted DataFrame of demo File."""

import os
import random
from math import atan2, degrees

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from demolyzer.demo_utils import demo_to_dataframe


def _normalize_angle(angle: int | float) -> float:
    return (angle + 180) % 360 - 180


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

    def delta_mouse_movement(self) -> None:
        """Sum delta pitch angle and delta view angle to visualize change in aim over ticks."""
        players = self.players.items()
        num_of_players = len(players)

        fig = make_subplots(rows=num_of_players, cols=1, shared_xaxes=True)

        for i, (steam_id, name) in enumerate(players, start=1):
            player_df = self.df[self.df["players_info.steamId"] == steam_id]
            delta_pitch = player_df["players_pitch_angle"].diff()[1:]
            delta_view = player_df["players_view_angle"].diff()[1:]
            delta_sum = delta_pitch + delta_view
            ticks = player_df["tick"]

            fig.add_trace(go.Scatter(x=ticks, y=delta_sum, name=steam_id), row=i, col=1)

        fig.update_layout(title="Delta Mouse Movement Over Time for Each Player")
        fig.show()

    def viewangle_delta_plot(self) -> None:
        players = self.players.items()

        colors = [
            f"rgb({random.randint(0, 255)}, {random.randint(0, 255)}, {random.randint(0, 255)})"
            for _ in range(len(players))
        ]

        fig = make_subplots(
            rows=len(players),
            cols=3,
            subplot_titles=("View Angle Delta", "Pitch Angle Delta", "Angle of Movement"),
            shared_xaxes=True,
        )

        for i, (steam_id, name) in enumerate(players, start=1):
            showlegend = i == 1
            player_df = self.df[self.df["players_info.steamId"] == steam_id]

            delta_view_angle = (player_df["players_view_angle"].diff()[1:]).apply(_normalize_angle)
            fig.add_trace(
                go.Scatter(x=player_df["tick"][1:], y=delta_view_angle, name=steam_id, marker_color=colors[i - 1]),
                row=i,
                col=1,
            )

            delta_pitch_angle = player_df["players_pitch_angle"].diff()[1:]
            fig.add_trace(
                go.Scatter(
                    x=player_df["tick"][1:],
                    y=delta_pitch_angle,
                    name=steam_id,
                    marker_color=colors[i - 1],
                    showlegend=False,
                ),
                row=i,
                col=2,
            )

            delta_x = player_df["players_position.x"].diff()[1:]
            delta_y = player_df["players_position.y"].diff()[1:]
            angle_of_movement = [degrees(atan2(dy, dx)) for dx, dy in zip(delta_x, delta_y)]
            fig.add_trace(
                go.Scatter(
                    x=player_df["tick"][1:],
                    y=angle_of_movement,
                    name=steam_id,
                    marker_color=colors[i - 1],
                    showlegend=False,
                ),
                row=i,
                col=3,
            )

        fig.update_layout(title="View Angle Delta, Pitch Angle Delta and Angle of Movement over Time for Each Player")
        fig.update_xaxes(title="Time", row=len(players))
        fig.show()

    def __str__(self) -> str:
        return f"{self.demo_file} with {self.num_players} players and duration of {self.duration}"
