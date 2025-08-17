from typing import List, Tuple, Dict

import numpy
import pandas
from matplotlib import axes, figure, patches, pyplot
from matplotlib.animation import FuncAnimation

DROP_ACTION = "LOGC"
PICK_ACTION = "LOGO"


class Colours:
    """
    Class to store the colours for the animation.
    """

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


class ZOrder:
    """
    Class to store the z-order for the animation. Lower z-order means the object is
    plotted on the bottom layer.
    """

    BUFFER = 0.5
    UNAVAILABLE_SECTION = 0.5
    STATION = 1
    PATH = 2
    PATH_HALT = 1.8
    FUTURE_COORD = 3
    FUTURE_COORD_HALT = 1.9
    SKYCAR = 4
    SKYCAR_TEXT = 5
    TIME_TEXT = 6


class Animation:
    """
    Class to contain initialisation and animation methods

    Attributes
    ----------
    summary_data : Dict[int, pandas.DataFrame]
        Dictionary where the key is the skycar index and the value is the summary data
        (data with only main entries "LOG")
    step_data : Dict[int, pandas.DataFrame]
        Dictionary where the key is the skycar index and the value is the step data
        (data with only child entries)
    skycar_indices : List[int]
        The list of skycar indices.
    times : range
        The range of times for the animation.
    delta_time : int
        The time interval between each frame of the animation.
    initial_time : int
        The initial time of the animation.
    simulation_start_time : int
        The actual start time of the simulation from logs.
    lim_x : int
        The maximum x coordinate of the grid.
    lim_y : int
        The maximum y coordinate of the grid.
    station_coordinates : List[Tuple[int, int]]
        The coordinates of the stations in the grid.
    buffer_coordinates : List[Tuple[int, int]]
        The coordinates of the buffers in the grid.
    unavailable_coordinates : List[Tuple[int, int]]
        The coordinates of the unavailable sections in the grid.
    fig : figure.Figure
        The figure object for animation.
    ax : axes.Axes
        The axes object for animation.
    skycars : Dict[int, patches.Rectangle]
        Dictionary where the key is the skycar index and the value is the skycar object
        for animation.
    future_coord_cells : Dict[int, patches.Rectangle]
        Dictionary where the key is the skycar index and the value is the future coordinate
        cell object of the skycar for animation.
    path_lines : Dict[int, patches.Rectangle]
        Dictionary where the key is the skycar index and the value is the path line object
        for animation.
    skycar_texts : Dict[int, pyplot.Text]
        Dictionary where the key is the skycar index and the value is the text object to
        indicate skycar index on top of the skycar object.
    time_text : pyplot.Text
        The time text object for animation.
    stations : List[patches.Rectangle]
        The station objects for animation.
    buffers : List[patches.Rectangle]
        The buffer objects for animation.
    unavailable_sections : List[patches.Rectangle]
        The unavailable section objects for animation.

    Parameters
    ----------
    grid_data : pandas.DataFrame
        The grid data with x coordinates as columns and y coordinates as index.
    movement_data : pandas.DataFrame
        The movement data with skycar_id, action, completed_at, begin_at, prev_x, prev_y, x, y.
    from_time_min : int
        The start time of the simulation in minutes.
    to_time_min : int
        The end time of the simulation in minutes.
    """

    summary_data: Dict[int, pandas.DataFrame]
    step_data: Dict[int, pandas.DataFrame]
    skycar_indices: List[int]
    times: range
    delta_time: int
    initial_time: int
    simulation_start_time: int
    lim_x: int
    lim_y: int
    station_coordinates: List[Tuple[int, int]]
    buffer_coordinates: List[Tuple[int, int]]
    unavailable_coordinates: List[Tuple[int, int]]

    fig: figure.Figure
    ax: axes.Axes
    skycars: Dict[int, patches.Rectangle]
    future_coord_cells: Dict[int, patches.Rectangle]
    path_lines: Dict[int, patches.Rectangle]
    skycar_texts: Dict[int, pyplot.Text]
    time_text: pyplot.Text
    stations: List[patches.Rectangle]
    buffers: List[patches.Rectangle]
    unavailable_sections: List[patches.Rectangle]

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

        # Extract station coordinates (cells starting with 'P')
        station_mask = grid_data.map(
            lambda x: pandas.notna(x) and str(x).startswith("P")
        )
        station_positions = numpy.argwhere(station_mask.values)
        self.station_coordinates = [(x, y) for y, x in station_positions]

        # Extract buffer coordinates (cells with 'B')
        buffer_mask = grid_data.map(lambda x: pandas.notna(x) and str(x) == "B")
        buffer_positions = numpy.argwhere(buffer_mask.values)
        self.buffer_coordinates = [(x, y) for y, x in buffer_positions]

        # Extract unavailable section coordinates (combines "Others" and "Unavailable"
        # from grid_designer). This includes: NaN cells (unavailable) + non-numeric,
        # non-station, non-buffer cells (others)
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
        """
        Read data from movement data and extract the summary and step data for each skycar.

        Parameters
        ----------
        movement_data : pandas.DataFrame
            The movement data with skycar_id, action, completed_at, begin_at, prev_x,
            prev_y, x, y.
        """
        skycar_indices = [int(i) for i in movement_data["skycar_id"].unique()]

        step_data: Dict[int, pandas.DataFrame] = {}
        summary_data: Dict[int, pandas.DataFrame] = {}

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
        Initialise the figure and axes for animation.
        """
        # Ratio to keep the maximum dimension of the grid to 10 units.
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
        """
        Initialise the times for the animation.

        Parameters
        ----------
        from_time_min : int
            The start time of the simulation in minutes.
        to_time_min : int
            The end time of the simulation in minutes.
        """
        # Get the actual start time of the simulation from logs.
        simulation_start_time = min(
            [
                int(self.step_data[skycar_index]["completed_at"].min())
                for skycar_index in self.skycar_indices
            ]
        )

        # Initial time of animation is given by the user + 2 seconds to prevent animation
        # from being broken at the very beginning of simulation start time
        initial_time = simulation_start_time + (from_time_min * 60) + 2

        # Maximum time of animation is either the maximum time of the simulation, or the
        # maximum time intended by the users + 2 seconds (reason stated above)
        max_time = min(
            [
                int(self.step_data[skycar_index]["completed_at"].max())
                for skycar_index in self.skycar_indices
            ]
        )
        max_time = min(max_time, simulation_start_time + (to_time_min * 60) + 2)

        # The duration between each frame of the animation is set to 1 second.
        self.delta_time = 1

        self.times = numpy.arange(initial_time, max_time, self.delta_time)
        self.initial_time = self.times[0]
        self.simulation_start_time = simulation_start_time

        # Create time display at top left corner of the animation
        time_text = pyplot.text(
            0.5,
            0.5,
            f"Time: {(self.initial_time-self.simulation_start_time)/60} mins ",
            ha="left",
            va="top",
            fontsize=10,
            color="black",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
            zorder=ZOrder.TIME_TEXT,
        )
        self.time_text = time_text

    def initialise_sections(self):
        """
        Initialise the different sections (e.g. stations, buffers, unavailable/others) of
        the grid for animation.
        """
        stations = []
        for coord in self.station_coordinates:
            station = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.STATION_COLOUR,
                zorder=ZOrder.STATION,
            )
            stations.append(station)

        buffers = []
        for coord in self.buffer_coordinates:
            buffer = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.BUFFER_COLOUR,
                zorder=ZOrder.BUFFER,
            )
            buffers.append(buffer)

        unavailable_sections = []
        for coord in self.unavailable_coordinates:
            unavailable_section = patches.Rectangle(
                xy=coord,
                width=1,
                height=1,
                color=Colours.UNAVAILABLE_SECTION_COLOUR,
                zorder=ZOrder.UNAVAILABLE_SECTION,
            )
            unavailable_sections.append(unavailable_section)

        self.stations = stations
        self.buffers = buffers
        self.unavailable_sections = unavailable_sections

    def initialise_skycars(self):
        """
        Initialise the skycar objects for animation.
        """
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
                zorder=ZOrder.SKYCAR,
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
                zorder=(
                    ZOrder.FUTURE_COORD if not is_halting else ZOrder.FUTURE_COORD_HALT
                ),
            )

            # Create path line from current position to future position
            current_x, current_y = coords[0], coords[1]
            future_x, future_y = future_coords[0], future_coords[1]

            # Calculate path line dimensions based on direction. If dx > dy, the path line
            # is horizontal, otherwise it is vertical.
            dx = future_x - current_x
            dy = future_y - current_y
            if abs(dx) > abs(dy):
                path_width = abs(dx) + 1
                path_height = 1
                path_x = min(current_x, future_x)
                path_y = future_y
            else:
                path_width = 1
                path_height = abs(dy) + 1
                path_x = future_x
                path_y = min(current_y, future_y)

            path_lines[skycar_index] = patches.Rectangle(
                (path_x, path_y),
                path_width,
                path_height,
                color=Colours.PATH_COLOUR,
                alpha=0.8,
                zorder=ZOrder.PATH if not is_halting else ZOrder.PATH_HALT,
            )

            # Create text label for skycar index. Position at center of skycar rectangle
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
                zorder=ZOrder.SKYCAR_TEXT,
            )

        self.skycars = skycars
        self.future_coord_cells = future_coord_cells
        self.path_lines = path_lines
        self.skycar_texts = skycar_texts

    def get_skycar_info_at_time(
        self, skycar_index: int, time: int
    ) -> Tuple[Tuple[float, float], Tuple[float, float], str]:
        """
        Get skycar information at a given timestamp.

        Parameters
        ----------
        skycar_index : int
            The index of the skycar.
        time : int
            The timestamp of the time.

        Returns
        -------
        (current_x, current_y) : Tuple[float, float]
            The current position of the skycar.
        (future_x, future_y) : Tuple[float, float]
            The future position of the skycar.
        action : str
            The action of the skycar from skycar main movement data (summary data).
        is_halting : bool
            Whether the skycar is halting.
        """
        skycar_step_data = self.step_data[skycar_index]
        step_row = skycar_step_data[skycar_step_data["completed_at"] > time].iloc[0]

        begin_to_completed_time_diff = step_row["completed_at"] - step_row["begin_at"]
        begin_to_current_time_diff = time - step_row["begin_at"]

        # If the skycar has not moved yet, the current position is the previous position.
        if begin_to_current_time_diff <= 0.0:
            current_x = step_row["prev_x"]
            current_y = step_row["prev_y"]
        else:
            # If the skycar has moved, the current position is the previous position +
            # the distance travelled since the beginning of the step.
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

        # If the skycar is expected to not move in the next 2 seconds, we consider it
        # as halting.
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
        """
        Initialise the first frame of the animation.

        Returns
        -------
        List
            The list of all elements to be plotted in the first frame.
        """
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

    def animation_function(self, current_time) -> List:
        """
        Function to animate the skycars.

        Parameters
        ----------
        current_time : int
            The current time of the animation.

        Returns
        -------
        List
            The list of all elements to be plotted in the current frame.
        """
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
            future_cell.set_zorder(
                ZOrder.FUTURE_COORD if not is_halting else ZOrder.FUTURE_COORD_HALT
            )

            # Update path rectangle from current to future position
            current_x, current_y = coords[0], coords[1]
            future_x, future_y = future_coords[0], future_coords[1]

            # Calculate path dimensions based on direction
            dx = future_x - current_x
            dy = future_y - current_y

            # Horizontal path
            if abs(dx) > abs(dy):
                path_width = abs(dx) + 1
                path_height = 1
                path_x = min(current_x, future_x)
                path_y = future_y
            # Vertical path
            else:
                path_width = 1
                path_height = abs(dy) + 1
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
            path_rect.set_zorder(ZOrder.PATH if not is_halting else ZOrder.PATH_HALT)

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
        """
        Main function to animate the skycars.

        Parameters
        ----------
        save_filename : str, optional
            The filename to save the animation to, by default "", which means no file is
            saved.
        """
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
