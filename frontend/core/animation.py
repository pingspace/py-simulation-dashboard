from typing import List, Tuple, Dict

import numpy
import pandas
from matplotlib import axes, figure, patches, pyplot
from matplotlib.animation import FuncAnimation

DROP_ACTION = "LOGC"
PICK_ACTION = "LOGO"


class Colours:
    # Purple to indicate drop action, orange to indicate pick action, and blue to
    # indicate an usual action.
    DROP_COLOUR = "#B480B7"
    PICK_COLOUR = "#EF8A45"
    NORMAL_COLOUR = "#64C7F3"

    # Dark green to indicate the future coordinate cell, while light green to indicate
    # the path
    FUTURE_COORD_COLOUR = "#6caa7a"
    PATH_COLOUR = "#85d497"

    # If the skycar halts, the future coordinate cell is dark red, and the path is
    # light red.
    FUTURE_COORD_HALT_COLOUR = "#c44e52"
    PATH_HALT_COLOUR = "#ff9f9b"

    # Brown to indicate the position of stations, and yellow to indicate the buffers.
    # Grey to indicate the unavailable and other sections.
    STATION_COLOUR = "#d4b589"
    BUFFER_COLOUR = "#eceb8a"
    UNAVAILABLE_SECTION_COLOUR = "#bfbbb5"


class Animation:
    """
    Class to contain initialisation and animation methods
    """

    summary_data: Dict[int, pandas.DataFrame]
    step_data: Dict[int, pandas.DataFrame]
    skycar_indices: List[int]
    fig: figure.Figure
    ax: axes.Axes
    times: range
    skycars: Dict[int, patches.Rectangle]
    future_coord_cells: Dict[int, patches.Rectangle]
    path_lines: Dict[int, patches.Rectangle]
    skycar_texts: Dict[int, pyplot.Text]
    time_text: pyplot.Text
    initial_time: int
    simulation_start_time: int
    lim_x: int
    lim_y: int
    station_coordinates: List[Tuple[int, int]]
    buffer_coordinates: List[Tuple[int, int]]
    unavailable_coordinates: List[Tuple[int, int]]

    def __init__(
        self,
        grid_data: pandas.DataFrame,
        movement_data: pandas.DataFrame,
        from_time_min: int,
        to_time_min: int,
    ):
        self.read_grid_data(grid_data=grid_data)
        self.read_skycar_data(movement_data=movement_data)
        self.initialise_figure()
        self.initialise_times(from_time_min=from_time_min, to_time_min=to_time_min)
        self.initialise_sections()
        self.initialise_skycars()

    def read_grid_data(self, grid_data: pandas.DataFrame):
        """
        Read grid data and extract the limits for x and y coordinates.

        Parameters
        ----------
        grid_data : pandas.DataFrame
            The grid data with x coordinates as columns and y coordinates as index.
        """
        # Get the grid dimensions
        self.lim_x = len(grid_data.columns)
        self.lim_y = len(grid_data.index)

        # Extract station coordinates (cells starting with 'P') using vectorized operations
        station_mask = grid_data.map(
            lambda x: pandas.notna(x) and str(x).startswith("P")
        )
        station_positions = numpy.argwhere(station_mask.values)
        self.station_coordinates = [(x, y) for y, x in station_positions]

        # Extract buffer coordinates (cells with 'B') using vectorized operations
        buffer_mask = grid_data.map(lambda x: pandas.notna(x) and str(x) == "B")
        buffer_positions = numpy.argwhere(buffer_mask.values)
        self.buffer_coordinates = [(x, y) for y, x in buffer_positions]

        # Extract unavailable section coordinates (combines "Others" and "Unavailable" from grid_designer)
        # This includes: NaN cells (unavailable) + non-numeric, non-station, non-buffer cells (others)
        unavailable_mask = grid_data.map(
            lambda x: pandas.isna(x)
            or (
                pandas.notna(x)
                and not str(x).startswith("P")
                and str(x) != "B"
                and not str(x).isdigit()
            )
        )
        unavailable_positions = numpy.argwhere(unavailable_mask.values)
        self.unavailable_coordinates = [(x, y) for y, x in unavailable_positions]

    def read_skycar_data(self, movement_data: pandas.DataFrame):
        skycar_indices = [int(i) for i in movement_data["skycar_id"].unique()]

        step_data: Dict[int, pandas.DataFrame] = {}
        summary_data: Dict[int, pandas.DataFrame] = {}

        # for skycar_index in skycar_indices:
        for skycar_index in skycar_indices:
            summary_mask = movement_data["action"].str.contains("LOG")
            summary_data[skycar_index] = movement_data[
                (summary_mask) & (movement_data["skycar_id"] == skycar_index)
            ]
            step_data[skycar_index] = movement_data[
                (~summary_mask) & (movement_data["skycar_id"] == skycar_index)
            ]

        self.summary_data = summary_data
        self.step_data = step_data
        self.skycar_indices = skycar_indices

    def initialise_figure(self):
        """
        Initialise the figure object
        """
        fig_ratio = 10 / max(self.lim_x, self.lim_y)
        fig, ax = pyplot.subplots(
            1, 1, figsize=(self.lim_x * fig_ratio, self.lim_y * fig_ratio)
        )

        ax.set_xlim(0, self.lim_x)
        ax.set_ylim(0, self.lim_y)
        ax.grid(which="both", color="lightgray", linewidth=0.5, alpha=0.7)
        ax.set_xticks(numpy.arange(0, self.lim_x + 1, 1))
        ax.set_yticks(numpy.arange(0, self.lim_y + 1, 1))
        ax.set_xticklabels([])
        ax.set_yticklabels([])

        ax.set_aspect("equal")
        ax.invert_yaxis()
        self.fig = fig
        self.ax = ax

    def initialise_times(self, from_time_min: int, to_time_min: int):
        simulation_start_time = min(
            [
                int(self.step_data[skycar_index]["completed_at"].min())
                for skycar_index in self.skycar_indices
            ]
        )
        initial_time = simulation_start_time + (from_time_min * 60) + 2

        max_time = min(
            [
                int(self.step_data[skycar_index]["completed_at"].max())
                for skycar_index in self.skycar_indices
            ]
        )
        max_time = min(max_time, simulation_start_time + (to_time_min * 60) + 2)

        self.delta_time = 1
        self.times = numpy.arange(initial_time, max_time, self.delta_time)
        self.initial_time = self.times[0]
        self.simulation_start_time = simulation_start_time

    def initialise_sections(self):
        stations = []
        for coord in self.station_coordinates:
            station = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.STATION_COLOUR,
                zorder=1,
            )
            stations.append(station)

        buffers = []
        for coord in self.buffer_coordinates:
            buffer = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.BUFFER_COLOUR,
                zorder=0.5,
            )
            buffers.append(buffer)

        unavailable_sections = []
        for coord in self.unavailable_coordinates:
            unavailable_section = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.UNAVAILABLE_SECTION_COLOUR,
                zorder=0.5,
            )
            unavailable_sections.append(unavailable_section)

        self.stations = stations
        self.buffers = buffers
        self.unavailable_sections = unavailable_sections

    def initialise_skycars(self):
        skycars = {}
        future_coord_cells = {}
        path_lines = {}
        skycar_texts = {}

        for skycar_index in self.skycar_indices:
            coords, future_coords, action, is_halting = self.get_skycar_info_at_time(
                skycar_index=skycar_index, time=self.initial_time
            )
            if DROP_ACTION in action:
                colour = Colours.DROP_COLOUR
            elif PICK_ACTION in action:
                colour = Colours.PICK_COLOUR
            else:
                colour = Colours.NORMAL_COLOUR

            # Create skycar rectangle with higher z-order to ensure it's above cells
            skycars[skycar_index] = patches.Rectangle(
                xy=coords,
                width=1,
                height=1,
                facecolor=colour,
                edgecolor="black",
                linewidth=1,
                zorder=4,
            )

            # Create future coordinate cell with lower z-order
            future_coord_cells[skycar_index] = patches.Rectangle(
                future_coords,
                1,
                1,
                color=(
                    Colours.FUTURE_COORD_COLOUR
                    if not is_halting
                    else Colours.FUTURE_COORD_HALT_COLOUR
                ),
                alpha=0.6,
                zorder=3 if not is_halting else 1.9,
            )

            # Create path rectangle from current position to future position
            current_x, current_y = coords[0], coords[1]
            future_x, future_y = future_coords[0], future_coords[1]

            # Calculate path dimensions based on direction
            dx = future_x - current_x
            dy = future_y - current_y

            if abs(dx) > abs(dy):  # Horizontal path
                # Width = path length, Height = 1
                path_width = abs(dx) + 1  # +1 to include both current and future cells
                path_height = 1
                # Position at the leftmost point
                path_x = min(current_x, future_x)
                path_y = future_y
            else:  # Vertical path
                # Width = 1, Height = path length
                path_width = 1
                path_height = abs(dy) + 1  # +1 to include both current and future cells
                # Position at the topmost point (with inverted y-axis)
                path_x = future_x
                path_y = min(current_y, future_y)

            path_lines[skycar_index] = patches.Rectangle(
                (path_x, path_y),
                path_width,
                path_height,
                color=Colours.PATH_COLOUR,
                alpha=0.8,
                zorder=2 if not is_halting else 1.8,
            )

            # Create text label for skycar index
            # Position at center of skycar rectangle
            text_x = coords[0] + 0.5
            text_y = coords[1] + 0.5
            skycar_texts[skycar_index] = pyplot.text(
                text_x,
                text_y,
                str(skycar_index),
                ha="center",
                va="center",
                fontsize=8,
                color="black",
                zorder=5,  # Above skycars
            )

        # Create time display at top left corner
        time_text = pyplot.text(
            0.5,  # X position (near left edge)
            0.5,  # Y position (near top with inverted axis)
            f"Time: {(self.initial_time-self.simulation_start_time)/60} mins ",
            ha="left",
            va="top",
            fontsize=10,
            color="black",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            zorder=6,  # Above everything else
        )

        self.skycars = skycars
        self.future_coord_cells = future_coord_cells
        self.path_lines = path_lines
        self.skycar_texts = skycar_texts
        self.time_text = time_text

    def get_skycar_info_at_time(
        self, skycar_index: int, time: int
    ) -> Tuple[Tuple[float, float], Tuple[float, float], str]:
        skycar_step_data = self.step_data[skycar_index]
        step_row = skycar_step_data[skycar_step_data["completed_at"] > time].iloc[0]

        begin_to_completed_time_diff = step_row["completed_at"] - step_row["begin_at"]
        begin_to_current_time_diff = time - step_row["begin_at"]

        if begin_to_current_time_diff <= 0.0:
            current_x = step_row["prev_x"]
            current_y = step_row["prev_y"]
        else:
            current_x = (
                step_row["prev_x"]
                + ((step_row["x"] - step_row["prev_x"]) / begin_to_completed_time_diff)
                * begin_to_current_time_diff
            )
            current_y = (
                step_row["prev_y"]
                + ((step_row["y"] - step_row["prev_y"]) / begin_to_completed_time_diff)
                * begin_to_current_time_diff
            )

        if time - step_row["completed_at"] <= -2:
            is_halting = True
        else:
            is_halting = False

        skycar_summary_data = self.summary_data[skycar_index]
        summary_row = skycar_summary_data[skycar_summary_data["begin_at"] <= time].iloc[
            -1
        ]
        future_x, future_y = summary_row["x"], summary_row["y"]

        action = summary_row["action"]

        return (current_x, current_y), (future_x, future_y), action, is_halting

    def start_frame(self) -> List:

        for buffer in self.buffers:
            self.ax.add_patch(buffer)

        for unavailable_section in self.unavailable_sections:
            self.ax.add_patch(unavailable_section)

        for station in self.stations:
            self.ax.add_patch(station)

        # Add path rectangles first (lowest z-order, bottom layer)
        for path_rect in self.path_lines.values():
            self.ax.add_patch(path_rect)

        # Add future coordinate cells second (middle z-order)
        for future_cell in self.future_coord_cells.values():
            self.ax.add_patch(future_cell)

        # Add skycars third (higher z-order)
        for skycar in self.skycars.values():
            self.ax.add_patch(skycar)

        # Add text labels fourth (highest z-order, on top of everything)
        for text in self.skycar_texts.values():
            self.ax.add_artist(text)

        # Add time text (highest z-order)
        self.ax.add_artist(self.time_text)

        # Return all elements for animation
        return (
            list(self.buffers)
            + list(self.unavailable_sections)
            + list(self.stations)
            + list(self.path_lines.values())
            + list(self.future_coord_cells.values())
            + list(self.skycars.values())
            + list(self.skycar_texts.values())
            + [self.time_text]
        )

    def animation_function(self, current_time):
        for skycar_index in self.skycar_indices:
            coords, future_coords, action, is_halting = self.get_skycar_info_at_time(
                skycar_index=skycar_index, time=current_time
            )

            # Update skycar position and color
            skycar = self.skycars[skycar_index]
            skycar.set_xy(coords)

            if DROP_ACTION in action:
                colour = Colours.DROP_COLOUR
            elif PICK_ACTION in action:
                colour = Colours.PICK_COLOUR
            else:
                colour = Colours.NORMAL_COLOUR
            skycar.set_facecolor(colour)

            # Update future coordinate cell position
            future_cell = self.future_coord_cells[skycar_index]
            future_cell.set_xy(future_coords)
            future_cell.set_color(
                Colours.FUTURE_COORD_COLOUR
                if not is_halting
                else Colours.FUTURE_COORD_HALT_COLOUR
            )
            future_cell.set_zorder(3 if not is_halting else 1.9)

            # Update path rectangle from current to future position
            current_x, current_y = coords[0], coords[1]
            future_x, future_y = future_coords[0], future_coords[1]

            # Calculate path dimensions based on direction
            dx = future_x - current_x
            dy = future_y - current_y

            if abs(dx) > abs(dy):  # Horizontal path
                # Width = path length, Height = 1
                path_width = abs(dx) + 1  # +1 to include both current and future cells
                path_height = 1
                # Position at the leftmost point
                path_x = min(current_x, future_x)
                path_y = future_y
            else:  # Vertical path
                # Width = 1, Height = path length
                path_width = 1
                path_height = abs(dy) + 1  # +1 to include both current and future cells
                # Position at the topmost point (with inverted y-axis)
                path_x = future_x
                path_y = min(current_y, future_y)

            # Update the path rectangle
            path_rect = self.path_lines[skycar_index]
            path_rect.set_xy((path_x, path_y))
            path_rect.set_width(path_width)
            path_rect.set_height(path_height)
            path_rect.set_color(
                Colours.PATH_COLOUR if not is_halting else Colours.PATH_HALT_COLOUR
            )
            path_rect.set_zorder(2 if not is_halting else 1.8)

            # Update text position to center of skycar
            text = self.skycar_texts[skycar_index]
            text.set_position((coords[0] + 0.5, coords[1] + 0.5))

        # Update time display - show elapsed time since initial time
        elapsed_time = current_time - self.simulation_start_time
        self.time_text.set_text(f"Time: {elapsed_time/60:.2f} mins")

        # Return all elements for animation
        return (
            list(self.buffers)
            + list(self.unavailable_sections)
            + list(self.stations)
            + list(self.path_lines.values())
            + list(self.future_coord_cells.values())
            + list(self.skycars.values())
            + list(self.skycar_texts.values())
            + [self.time_text]
        )

    def animate(self, save_filename: str = "") -> FuncAnimation:

        anim = FuncAnimation(
            fig=self.fig,
            func=self.animation_function,
            init_func=self.start_frame,
            frames=self.times,
            interval=100,
            blit=True,
        )
        if save_filename != "":
            anim.save(f"{save_filename}", writer="ffmpeg")
