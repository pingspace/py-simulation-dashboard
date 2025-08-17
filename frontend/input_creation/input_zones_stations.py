from __future__ import annotations

import json
from typing import List

import numpy
from core.exception import SimulationFrontendException
from core.parameters import Parameters
from ui_components.grid_designer import GridDesignerUI


class InputZonesAndStations:
    """
    Class to create the zones and stations from the grid designer UI, then to send to SM.

    Parameters
    ----------
    grid_designer_ui : GridDesignerUI
        The grid designer UI.
    """

    def __init__(self, grid_designer_ui: GridDesignerUI):
        self._create_zones(grid_designer_ui=grid_designer_ui)
        self._create_stations(grid_designer_ui=grid_designer_ui)

    def _create_zones(self, grid_designer_ui: GridDesignerUI):
        """
        Create zones from the grid designer UI.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        """
        # Create voids
        sm_and_tc_obstacle_voids = self._create_voids(
            grid_designer_ui=grid_designer_ui, void_type="SM and TC obstacles"
        )
        sm_obstacle_only_voids = self._create_voids(
            grid_designer_ui=grid_designer_ui, void_type="SM obstacles only"
        )
        voids = sm_and_tc_obstacle_voids + sm_obstacle_only_voids

        zone = InputZone(
            max_x=grid_designer_ui.grid_data.shape[1] - 1,
            max_y=grid_designer_ui.grid_data.shape[0] - 1,
            max_z=grid_designer_ui.z_size,
            voids=voids,
        )

        # Assign zones
        self.zones = [zone]

    def _create_voids(
        self, grid_designer_ui: GridDesignerUI, void_type: str
    ) -> List[InputVoid]:
        """
        Create voids from the grid designer UI. The voids are separated by whether they
        are exclusively SM obstacles, or SM and TC obstacles.

        The only way to recognise voids is via the 2D top-down view of the grid, and assume
        that the voids are all the way down throughout the z-axis. This may not be true
        in potential future use cases, e.g. having an empty space at the bottom of the
        grid.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        void_type : str
            The type of void to create, either "SM and TC obstacles" or "SM obstacles
            only".

        Returns
        -------
        List[InputVoid]
            A list of voids.

        Raises
        ------
        SimulationFrontendException
            If the void type is not implemented.
        """
        # If it's both SM and TC obstacles, even z=0 is considered a void. Cells that
        # are not numbers, stations or buffers are all considered voids.
        if void_type == "SM and TC obstacles":
            void_mask = ~(
                grid_designer_ui.grid_data.map(lambda x: str(x).isdigit()).to_numpy()
                | grid_designer_ui.grid_data.map(
                    lambda x: str(x).startswith("P")
                ).to_numpy()
                | grid_designer_ui.grid_data.map(lambda x: str(x) == "B").to_numpy()
            )
            start_z = 0

        # Otherwise if it's SM obstacles only, then skycars can still move at z=0 but
        # no stacks below them can be used. This are marked as buffer cells.
        elif void_type == "SM obstacles only":
            void_mask = grid_designer_ui.grid_data.map(
                lambda x: str(x) == "B"
            ).to_numpy()
            start_z = 1

        else:
            raise SimulationFrontendException(f"Void type {void_type} not implemented")

        # Get void coordinates
        processed = numpy.zeros_like(void_mask, dtype=bool)
        void_positions = numpy.argwhere(numpy.logical_and(void_mask, ~processed))

        # Go through each void cells and expand them to the right and down until they
        # hit a non-void cell. The voids can be overlapping.
        rows, cols = void_mask.shape
        voids = []
        for start_y, start_x in void_positions:
            if processed[start_y, start_x]:
                continue

            # Expand right
            end_x = start_x
            while end_x + 1 < cols and void_mask[start_y, end_x + 1]:
                end_x += 1

            # Expand down
            end_y = start_y
            while end_y + 1 < rows:
                is_valid = True
                for x in range(start_x, end_x + 1):
                    if not void_mask[end_y + 1, x]:
                        is_valid = False
                        break
                if not is_valid:
                    break
                end_y += 1

            # Mark as processed
            processed[start_y : end_y + 1, start_x : end_x + 1] = True

            void = InputVoid(
                from_=Coordinates(x=int(start_x), y=int(start_y), z=start_z),
                to=Coordinates(x=int(end_x), y=int(end_y), z=grid_designer_ui.z_size),
            )
            voids.append(void)

        return voids

    def _create_stations(self, grid_designer_ui: GridDesignerUI):
        """
        Create stations from the grid designer UI.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        """
        # Stations are located at the bottom of the grid with some height offset
        station_height = grid_designer_ui.z_size - Parameters.STATION_HEIGHT_FROM_BOTTOM

        # Get the stations from the grid designer UI. Stations are marked with prefix 'P'.
        # The list is sorted so it's implicitly assume that if a station has different
        # drop and pick points, drop point will be listed first.
        grid_data_array = grid_designer_ui.grid_data.to_numpy()
        grid_stations = sorted(grid_designer_ui.station_cells.copy())

        stations: List[InputStation] = []
        for grid_station in grid_stations:
            y, x = numpy.argwhere(grid_data_array == grid_station)[0].tolist()
            station_number = int("".join(filter(str.isdigit, grid_station)))

            # The second last character should be either D or P to indicate drop or pick
            # point. Otherwise (like the condition below) drop and pick points are the
            # same.
            if grid_station[-2] not in ["D", "P"]:
                drop = InputDropOrPick(
                    coordinates=Coordinates(x=x, y=y, z=station_height), capacity=2
                )
                pick = InputDropOrPick(
                    coordinates=Coordinates(x=x, y=y, z=station_height), capacity=1
                )
                station = InputStation(code=station_number, drop=drop, pick=pick)
                stations.append(station)

            # If the station has both drop and pick points, then process them accordingly.
            # Since we have already sorted the grid station input, drop point will be
            # listed first, then pick point.
            else:
                if grid_station[-2] == "D":
                    drop = InputDropOrPick(
                        coordinates=Coordinates(x=x, y=y, z=station_height), capacity=2
                    )
                else:
                    pick = InputDropOrPick(
                        coordinates=Coordinates(x=x, y=y, z=station_height), capacity=1
                    )
                    station = InputStation(code=station_number, drop=drop, pick=pick)
                    stations.append(station)

        self.stations = stations

    def to_json(
        self, save: bool = False, filename: str = "reset-2.json", type: str = "str"
    ) -> str:
        """
        Convert the input to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the input to a file, by default False.
        filename : str, optional
            The name of the file to save the input to, by default "reset-2.json".
        type : str, optional
            The type of the input; either "str" or "dict", by default "str".

        Returns
        -------
        str
            The JSON string of the input.
        """
        json_str = json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4
        )

        if save:
            with open(filename, "w") as file:
                file.write(json_str)

        if type == "str":
            return json_str
        elif type == "dict":
            return json.loads(json_str)


class InputZone:
    """
    The grid information to send to SM.

    Attributes
    ----------
    fromX : int
        The minimum x coordinate of the zone; set to 0.
    toX : int
        The maximum x coordinate of the zone; set to max_x.
    fromY : int
        The minimum y coordinate of the zone; set to 0.
    toY : int
        The maximum y coordinate of the zone; set to max_y.
    fromZ : int
        The minimum z coordinate of the zone; set to 0.
    toZ : int
        The maximum z coordinate of the zone; set to max_z.

    Parameters
    ----------
    max_x : int
        The maximum x coordinate of the grid.
    max_y : int
        The maximum y coordinate of the grid.
    max_z : int
        The maximum z coordinate of the grid.
    voids : List[InputVoid]
        The voids in the grid.
    name : str, optional
        The name of the zone, by default Parameters.ZONE_NAME
    """

    def __init__(
        self,
        max_x: int,
        max_y: int,
        max_z: int,
        voids: List[InputVoid],
        name: str = Parameters.ZONE_NAME,
    ):
        self.name = name
        self.fromX = 0
        self.toX = max_x
        self.fromY = 0
        self.toY = max_y
        self.fromZ = 0
        self.toZ = max_z
        self.voids = voids


class InputVoid:
    def __init__(self, from_: Coordinates, to: Coordinates):
        """
        A void in the grid.

        Parameters
        ----------
        from_ : Coordinates
            The coordinates of the top-left corner of the void.
        to : Coordinates
            The coordinates of the bottom-right corner of the void.
        """
        self.to = to

        # Since from is a reserved keyword in Python, we need to use a different way to
        # set the attribute
        setattr(self, "from", from_)


class InputStation:
    """
    A station in the grid. SM receives the drop point and pick point as lists, but the
    list only contains one element each.

    Parameters
    ----------
    code : int
        The code of the station.
    drop : InputDropOrPick
        Information on drop point.
    pick : InputDropOrPick
        Information on pick point.
    """

    def __init__(self, code: int, drop: InputDropOrPick, pick: InputDropOrPick):
        self.code = code
        self.drop = [drop]
        self.pick = [pick]


class InputDropOrPick:
    """
    Drop or pick point information of a station.

    Parameters
    ----------
    coordinates : Coordinates
        The coordinates of the drop or pick point.
    capacity : int
        The capacity of the drop or pick point. Usually drop point has capacity 2 while
        pick point has capacity 1. It is unknown why this is the case.
    hardware_index : int, optional
        The hardware index of the drop or pick point, by default 1.
    zone_group : str, optional
        The zone group of the drop or pick point, by default Parameters.ZONE_NAME.
    """

    def __init__(
        self,
        coordinates: Coordinates,
        capacity: int,
        hardware_index: int = 1,
        zone_group: str = Parameters.ZONE_NAME,
    ):
        self.capacity = capacity
        self.hardwareIndex = hardware_index
        self.zoneGroup = zone_group
        self.coordinate = coordinates


class Coordinates:
    """
    Coordinates in the grid.

    Parameters
    ----------
    x : int
        The x coordinate.
    y : int
        The y coordinate.
    z : int, optional
        The z coordinate, by default 0.
    """

    def __init__(self, x: int, y: int, z: int = 0):
        self.x = x
        self.y = y
        self.z = z
