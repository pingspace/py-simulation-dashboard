import json

import numpy
from core.parameters import Parameters
from ui_components.grid_designer import GridDesignerUI


class InputSMObstacles:
    """
    Class to create the SM obstacles from the grid designer UI, then to send to SM. SM
    obstacles are stacks where bins cannot be stored.

    Parameters
    ----------
    grid_designer_ui : GridDesignerUI
        The grid designer UI.
    """

    def __init__(self, grid_designer_ui: GridDesignerUI):
        self._create_stacks(grid_designer_ui=grid_designer_ui)
        self.zoneGroup = Parameters.ZONE_NAME
        self.isSkycarAccessible = False

    def _create_stacks(self, grid_designer_ui: GridDesignerUI):
        """
        Create the stacks as SM obstacles.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.
        """
        # Coordinates that are not free stacks nor stations are considered SM obstacles.
        void_mask = ~(
            grid_designer_ui.grid_data.map(lambda x: str(x).isdigit()).to_numpy()
            | grid_designer_ui.grid_data.map(
                lambda x: str(x).startswith("P")
            ).to_numpy()
        )
        coordinates = numpy.argwhere(void_mask)

        # Create InputStack objects for each coordinate
        self.stacks = [InputStack(x=int(col), y=int(row)) for row, col in coordinates]

    def to_json(
        self, save: bool = False, filename: str = "reset-3.json", type: str = "str"
    ) -> str:
        """
        Convert the SM obstacles to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-3.json"
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


class InputStack:
    """
    Stack information to send to SM.

    Parameters
    ----------
    x : int
        The x coordinate of the stack.
    y : int
        The y coordinate of the stack.
    """

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
