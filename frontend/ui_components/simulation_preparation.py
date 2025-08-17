import streamlit
from input_creation.input_buffer import InputBuffer
from input_creation.input_database import InputDatabase
from input_creation.input_simulation import InputSimulation
from input_creation.input_skycar import InputSkyCarSetup
from input_creation.input_skycar_constraints import InputSkyCarConstraints
from input_creation.input_sm_obstacles import InputSMObstacles
from input_creation.input_tc_obstacles import InputTCObstacles
from input_creation.input_zones_stations import InputZonesAndStations
from ui_components.grid_designer import GridDesignerUI
from ui_components.simulation_input import SimulationInputUI

from frontend.input_creation.input_autostore import InputAutostore


class SimulationPreparationUI:
    """
    Class to prepare the inputs to be sent to relevant servers.

    Parameters
    ----------
    grid_designer_ui : GridDesignerUI
        The UI for grid designer.
    simulation_input_ui : SimulationInputUI
        The UI for simulation input.
    """

    def __init__(
        self, grid_designer_ui: GridDesignerUI, simulation_input_ui: SimulationInputUI
    ):
        self.grid_designer_ui = grid_designer_ui
        self.simulation_input_ui = simulation_input_ui

    def show(self) -> bool:
        """
        Show the simulation preparation UI.

        Returns
        -------
        bool
            True if the simulation preparation UI can be displayed successfully, False
            otherwise.
        """
        streamlit.write("## Simulation Preparation")

        server_number = streamlit.selectbox(
            "Choose a server to run the simulation on.",
            [1, 2],
            index=None,
            placeholder="Select server...",
        )
        if server_number is None:
            return False

        # Create input objects
        input_zones_and_stations = InputZonesAndStations(
            grid_designer_ui=self.grid_designer_ui
        )
        input_sm_obstacles = InputSMObstacles(grid_designer_ui=self.grid_designer_ui)
        input_buffer = InputBuffer(buffer_ratio=self.grid_designer_ui.buffer_ratio)
        input_skycar_setup = InputSkyCarSetup(
            number_of_skycars=self.simulation_input_ui.number_of_skycars,
        )
        input_tc_obstacles = InputTCObstacles(grid_designer_ui=self.grid_designer_ui)
        input_skycar_constraints = InputSkyCarConstraints(
            grid_designer_ui=self.grid_designer_ui
        )
        input_autostore = InputAutostore(
            input_zones_and_stations=input_zones_and_stations,
        )
        input_simulation = InputSimulation(
            simulation_input_ui=self.simulation_input_ui,
            grid_designer_ui=self.grid_designer_ui,
            server_number=server_number,
        )
        input_database = InputDatabase(
            simulation_input_ui=self.simulation_input_ui,
            grid_designer_ui=self.grid_designer_ui,
            input_zones_and_stations=input_zones_and_stations,
            input_simulation=input_simulation,
        )

        # Option to show request files
        is_show_files = streamlit.checkbox("Show request files")
        if is_show_files:
            with streamlit.expander("reset-2.json: Zones and Stations"):
                json_data = input_zones_and_stations.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-2.json"
                )

            with streamlit.expander("reset-3.json: SM Obstacles"):
                json_data = input_sm_obstacles.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-3.json"
                )

            with streamlit.expander("reset-4.json: Buffer"):
                json_data = input_buffer.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-4.json"
                )

            with streamlit.expander("reset-5.json: Skycar Setup"):
                json_data = input_skycar_setup.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-5.json"
                )

            with streamlit.expander("reset-6.json: TC Obstacles"):
                json_data = input_tc_obstacles.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-6.json"
                )

            with streamlit.expander("reset-7.json: Skycar Constraints"):
                json_data = input_skycar_constraints.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-7.json"
                )

            with streamlit.expander("reset-autostore.json: Autostore"):
                json_data = input_autostore.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-autostore.json"
                )

            with streamlit.expander("reset-simulation.json: Simulation"):
                json_data = input_simulation.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-simulation.json"
                )

            with streamlit.expander("reset-database.json: Database"):
                json_data = input_database.to_json()
                self._show_individual_json_file(
                    json_data=json_data, file_name="reset-database.json"
                )

        self.input_zones_and_stations = input_zones_and_stations
        self.input_sm_obstacles = input_sm_obstacles
        self.input_buffer = input_buffer
        self.input_skycar_setup = input_skycar_setup
        self.input_tc_obstacles = input_tc_obstacles
        self.input_skycar_constraints = input_skycar_constraints
        self.input_autostore = input_autostore
        self.input_simulation = input_simulation
        self.input_database = input_database
        self.server_number = server_number

        return True

    def _show_individual_json_file(self, json_data: str, file_name: str):
        """
        Helper method to show individual JSON files and allow download.

        Parameters
        ----------
        json_data : str
            The JSON data to be shown.
        file_name : str
            The name of the file to be downloaded.
        """
        streamlit.download_button(
            label="Download",
            data=json_data,
            file_name=file_name,
            mime="application/json",
            type="primary",
        )
        streamlit.json(json_data)
