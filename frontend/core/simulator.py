import requests
import streamlit
from core.config import (
    SIMULATION_BASE_1,
    SIMULATION_BASE_2,
    SM_BASE_1,
    SM_BASE_2,
    TC_BASE_1,
    TC_BASE_2,
)
from core.simulation_database import SimulationDatabase
from core.simulation_requests import MosaicRequest
from ui_components.simulation_preparation import SimulationPreparationUI


class Simulator:
    """
    The main class to process the steps and send the relevant requests to relevant
    servers to start a simulation.

    Parameters
    ----------
    simulation_preparation_ui : SimulationPreparationUI
        The UI component to handle the simulation preparation.
    """

    def __init__(self, simulation_preparation_ui: SimulationPreparationUI):
        self.simulation_preparation_ui = simulation_preparation_ui
        self._set_server()

    def run(self, simulation_name: str):
        """
        The main method to go through the steps and send the relevant requests to relevant
        servers to start a simulation.

        Parameters
        ----------
        simulation_name : str
            The name of the simulation.
        """
        # Check if the server is healthy. Only proceed if the server is healthy or no 
        # simulation is running in the server.
        is_healthy, is_simulation_running, _, previous_simulation_name = (
            MosaicRequest.general_check(
                TC_base=self.TC_BASE,
                SM_base=self.SM_BASE,
                simulation_base=self.SIMULATION_BASE,
            )
        )
        if not is_healthy:
            streamlit.warning(
                "Server is unavailable. Please choose other server.", icon="⚠️"
            )
            return

        if is_simulation_running:
            streamlit.warning(
                f"Simulation {previous_simulation_name} is running. Please stop it before "
                + "running another one by pressing the stop button at the top of the page.",
                icon="⚠️",
            )
            return

        # Steps to send the requests to the relevant servers to start a simulation.
        steps = [
            ("Reset Layout in SM", self._reset_layout),
            ("Initialise Setup in SM", self._initialise_setup),
            ("Configure SM Obstacles", self._configure_SM_obstacles),
            ("Configure Storage Layout in SM", self._configure_layout),
            ("Configure TC Obstacles", self._configure_TC_obstacles),
            ("Configure Skycar Setup in TC", self._configure_skycar_setup),
            ("Configure Skycar Constraints in TC", self._configure_skycar_constraints),
            ("Start Cube in TC", self._start_cube),
            ("Disable Autostore in SM", self._disable_autostore),
            ("Start Simulation in Backend", self._start_simulation),
            ("Save Simulation Parameters", self._save_simulation_parameters),
        ]

        progress_bar = streamlit.progress(0)
        status_text = streamlit.empty()
        for i, (step_name, step_func) in enumerate(steps):
            status_text.text(f"Running: {step_name}")
            _ = step_func()
            progress_bar.progress((i + 1) / len(steps))

        status_text.text(f"Simulation {simulation_name} started successfully!")

    def _set_server(self):
        """
        Set the right base URL for the server.
        """
        if self.simulation_preparation_ui.server_number == 1:
            self.SM_BASE = SM_BASE_1
            self.TC_BASE = TC_BASE_1
            self.SIMULATION_BASE = SIMULATION_BASE_1
        elif self.simulation_preparation_ui.server_number == 2:
            self.SM_BASE = SM_BASE_2
            self.TC_BASE = TC_BASE_2
            self.SIMULATION_BASE = SIMULATION_BASE_2

    def _reset_layout(self) -> requests.Response:
        """
        Reset SM layout.

        Returns
        -------
        requests.Response
            The response from SM.
        """
        response = MosaicRequest.send_request(
            url=f"{self.SM_BASE}/v3/initialize/reset",
        )
        return response

    def _initialise_setup(self) -> requests.Response:
        """
        Initialise SM setup with zones and stations.

        Returns
        -------
        requests.Response
            The response from SM.
        """
        response = MosaicRequest.send_request(
            url=f"{self.SM_BASE}/v3/initialize",
            data=self.simulation_preparation_ui.input_zones_and_stations.to_json(
                type="dict"
            ),
        )
        return response

    def _configure_SM_obstacles(self) -> requests.Response:
        """
        Configure SM obstacles.

        Returns
        -------
        requests.Response
            The response from SM.
        """
        response = MosaicRequest.send_request(
            url=f"{self.SM_BASE}/v3/obstacles",
            data=self.simulation_preparation_ui.input_sm_obstacles.to_json(type="dict"),
        )
        return response

    def _configure_layout(self) -> requests.Response:
        """
        Configure SM layout.

        Returns
        -------
        requests.Response
            The response from SM.
        """
        response = MosaicRequest.send_request(
            url=f"{self.SM_BASE}/v3/initialize/storage",
            data=self.simulation_preparation_ui.input_buffer.to_json(type="dict"),
        )
        return response

    def _configure_skycar_setup(self) -> requests.Response:
        """
        Configure TC skycar setup.

        Returns
        -------
        requests.Response
            The response from TC.
        """
        response = MosaicRequest.send_request(
            url=f"{self.TC_BASE}/simulation/seed-skycars",
            data=self.simulation_preparation_ui.input_skycar_setup.to_json(type="dict"),
        )
        return response

    def _configure_TC_obstacles(self) -> requests.Response:
        """
        Configure TC obstacles.

        Returns
        -------
        requests.Response
            The response from TC.
        """
        response = MosaicRequest.send_request(
            url=f"{self.TC_BASE}/wcs/obstacle",
            data=self.simulation_preparation_ui.input_tc_obstacles.to_json(type="dict"),
        )
        return response

    def _configure_skycar_constraints(self) -> requests.Response:
        """
        Configure TC skycar constraints.

        Returns
        -------
        requests.Response
            The response from TC.
        """
        response = MosaicRequest.send_request(
            url=f"{self.TC_BASE}/operation/cube/constraints",
            data=self.simulation_preparation_ui.input_skycar_constraints.to_json(
                type="dict"
            ),
            method="PATCH",
        )
        return response

    def _start_cube(self) -> requests.Response:
        """
        Start TC cube.

        Returns
        -------
        requests.Response
            The response from TC.
        """
        response = MosaicRequest.send_request(
            url=f"{self.TC_BASE}/operation/cube?start=true&bypass=true",
        )
        return response

    def _disable_autostore(self) -> requests.Response:
        """
        Disable autostore in SM.

        Returns
        -------
        requests.Response
            The response from SM.
        """
        response = MosaicRequest.send_request(
            url=f"{self.SM_BASE}/v3/settings/auto-store",
            method="PUT",
            data=self.simulation_preparation_ui.input_autostore.to_json(type="dict"),
        )
        return response

    def _start_simulation(self) -> requests.Response:
        """
        Start simulation in simulation backend.

        Returns
        -------
        requests.Response
            The response from simulation backend.
        """
        simulation_database = SimulationDatabase()
        simulation_run_id = simulation_database.add_simulation_run(
            name=self.simulation_preparation_ui.input_simulation.configuration.name,
            server_number=self.simulation_preparation_ui.server_number,
        )
        simulation_database.close_connection()

        self.simulation_preparation_ui.input_simulation.update_simulation_run_id(
            simulation_run_id=simulation_run_id
        )

        response = MosaicRequest.send_request(
            url=f"{self.SIMULATION_BASE}/jobs/create",
            method="POST",
            data=self.simulation_preparation_ui.input_simulation.to_json(type="dict"),
        )
        return response

    def _save_simulation_parameters(self):
        """
        Save simulation parameters to the database.
        """
        simulation_database = SimulationDatabase()
        simulation_run_id = (
            self.simulation_preparation_ui.input_simulation.configuration.id
        )
        simulation_database.add_simulation_parameters(
            simulation_run_id=simulation_run_id,
            parameters=self.simulation_preparation_ui.input_database.to_json(
                type="dict"
            ),
        )
        simulation_database.close_connection()
