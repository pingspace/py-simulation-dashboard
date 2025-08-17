import json

from ui_components.grid_designer import GridDesignerUI


class InputTCObstacles:
    """
    Class to create the TC obstacles from the grid designer UI, then to send to TC.
    TC obstacles are coordinates where skycars cannot access.

    Parameters
    ----------
    grid_designer_ui : GridDesignerUI
        The grid designer UI.
    """
    def __init__(self, grid_designer_ui: GridDesignerUI):
        self.type = "Pillar"
        self.skycar_sid = 0
        self.error_id = 0

        self.two_d = self._find_tc_obstacles(grid_designer_ui=grid_designer_ui)

    def _find_tc_obstacles(self, grid_designer_ui: GridDesignerUI) -> list[str]:
        """
        Find TC obstacles.

        Parameters
        ----------
        grid_designer_ui : GridDesignerUI
            The grid designer UI.

        Returns
        -------
        list[str]
            The list of TC obstacle coordinates.
        """
        # Coordinates that are not free stacks, stations, nor buffers are considered TC 
        # obstacles.
        void_mask = ~(
            grid_designer_ui.grid_data.map(lambda x: str(x).isdigit()).to_numpy()
            | grid_designer_ui.grid_data.map(
                lambda x: str(x).startswith("P")
            ).to_numpy()
            | grid_designer_ui.grid_data.map(lambda x: str(x) == "B").to_numpy()
        )

        rows, cols = void_mask.shape
        return [f"{x},{y}" for y in range(rows) for x in range(cols) if void_mask[y, x]]

    def to_json(
        self, save: bool = False, filename: str = "reset-6.json", type: str = "str"
    ) -> str:
        """
        Convert the TC obstacles to a JSON string.

        Parameters
        ----------
        save : bool, optional
            Whether to save the JSON string to a file, by default False
        filename : str, optional
            The name of the file to save the JSON string to, by default "reset-6.json"
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
