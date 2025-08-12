import json
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit
from core.parameters import Parameters


class MosaicRequest:
    """
    Class to handle methods on requests of matrix simulation.
    """

    @staticmethod
    def SM_health_check(SM_base: str) -> bool:
        """
        Health check of the SM server. We take the `isActive` value of the
        GET /v3/settings/OrderDispatcher endpoint as an indicator of the health of the
        SM server.

        Parameters
        ----------
        SM_base : str
            The base URL of the SM server.

        Returns
        -------
        bool
            Whether the SM server is healthy.
        """
        try:
            sm_response = MosaicRequest.send_request(
                url=f"{SM_base}/v3/settings/OrderDispatcher", method="GET", timeout=1
            )
            sm_real_response = json.loads(sm_response.text)
            return sm_real_response["data"]["value"][Parameters.ZONE_NAME]["isActive"]

        except requests.exceptions.RequestException as _:
            return False

    @staticmethod
    def TC_status_check(TC_base: str) -> Tuple[bool, bool | None]:
        """
        Health check of the TC server. We assume that if the connection to the TC server
        is successful, the TC server is healthy.

        The `status` value of the GET /operation/healthcheck endpoint is an indicator of
        whether the TC server is active, i.e. whether there is currently a simulation
        running, or whether there is a completed simulation but not yet formally closed.

        Parameters
        ----------
        TC_base : str
            The base URL of the TC server.

        Returns
        -------
        is_healthy : bool
            Whether the TC server is healthy.
        is_tc_running : bool | None
            Whether the TC server is active. If True, there is a simulation running or a
            simulation has been completed but not yet formally closed. If False, there is
            no simulation running. If None, it means the connection to the TC server is
            unsuccessful.
        """
        try:
            tc_response = MosaicRequest.send_request(
                url=f"{TC_base}/operation/healthcheck", method="GET", timeout=1
            )
            tc_real_response = json.loads(tc_response.text)
            is_healthy = True
            is_tc_running = tc_real_response["model"]["cycle_stop"]["status"]

            return is_healthy, is_tc_running

        except requests.exceptions.RequestException as _:
            is_healthy = False
            is_tc_running = None
            return is_healthy, is_tc_running

    @staticmethod
    def backend_status_check(
        simulation_base: str,
    ) -> Tuple[bool, bool | None, str | None]:
        """
        Health check of the simulation backend server. We assume that if the connection
        to the backend server is successful, the backend server is healthy.

        Parameters
        ----------
        simulation_base : str
            The base URL of the simulation backend server.

        Returns
        -------
        is_healthy : bool
            Whether the backend server is healthy.
        is_simulation_completed : bool | None
            Whether the simulation has been completed. If None, it means the connection
            to the backend server is unsuccessful.
        simulation_name : str | None
            The name of the simulation. If None, it means the connection to the backend
            server is unsuccessful.
        """
        try:
            response = MosaicRequest.send_request(
                url=f"{simulation_base}/status",
                method="GET",
            )
            real_response = json.loads(response.text)
            simulation_name = real_response["simulation_name"]
            is_simulation_completed = (
                True if real_response["stop_time"] is not None else False
            )
            is_healthy = True
            return is_healthy, is_simulation_completed, simulation_name
        except requests.exceptions.RequestException as _:
            is_healthy = False
            is_simulation_completed = None
            simulation_name = None
            return is_healthy, is_simulation_completed, simulation_name

    @staticmethod
    def general_check(
        TC_base: str, SM_base: str, simulation_base: str
    ) -> Tuple[bool, bool | None, bool | None, str | None]:
        """
        General health check of the simulation system that combines the health checks of
        the SM, TC, and backend servers.

        Parameters
        ----------
        TC_base : str
            The base URL of the TC server.
        SM_base : str
            The base URL of the SM server.
        simulation_base : str
            The base URL of the simulation backend server.

        Returns
        -------
        is_healthy : bool
            Whether the simulation system is healthy.
        is_tc_running : bool | None
            Whether the TC server is active. If True, there is a simulation running or a
            simulation has been completed but not yet formally closed. If False, there is
            no simulation running. If None, it means the connection to the TC server is
            unsuccessful.
        is_simulation_completed : bool | None
            Whether the simulation has been completed. If None, it means the connection
            to the backend server is unsuccessful.
        simulation_name : str | None
            The name of the simulation. If None, it means the connection to the backend
            server is unsuccessful.
        """
        is_sm_healthy = MosaicRequest.SM_health_check(SM_base)
        is_tc_healthy, is_tc_running = MosaicRequest.TC_status_check(TC_base)
        is_backend_healthy, is_simulation_completed, simulation_name = (
            MosaicRequest.backend_status_check(simulation_base)
        )

        is_healthy = is_sm_healthy and is_tc_healthy and is_backend_healthy

        return is_healthy, is_tc_running, is_simulation_completed, simulation_name

    @staticmethod
    def tc_stop(TC_base: str) -> requests.Response | None:
        """
        Stop the simulation in TC.

        Parameters
        ----------
        TC_base : str
            The base URL of the TC server.

        Returns
        -------
        requests.Response | None
            The response from the TC server. If None, it means the connection to the TC
            server is unsuccessful.
        """
        try:
            response = MosaicRequest.send_request(
                url=f"{TC_base}/operation/cyclestop",
                data={
                    "status": "Enabled",
                    "reason": "Matrix simulation has stopped the simulation.",
                },
            )
            return response
        except requests.exceptions.RequestException as _:
            streamlit.warning(
                "Failed to stop TC, or there is no job queue to be stopped.",
                icon="⚠️",
            )
            return None

    @staticmethod
    def simulation_stop(simulation_base: str) -> requests.Response | None:
        """
        Stop the simulation in the simulation backend server.

        Parameters
        ----------
        simulation_base : str
            The base URL of the simulation backend server.

        Returns
        -------
        requests.Response | None
            The response from the simulation backend server. If None, it means the
            connection to the simulation backend server is unsuccessful.
        """
        try:
            response = MosaicRequest.send_request(
                url=f"{simulation_base}/jobs/stop",
                method="POST",
            )
            return response
        except requests.exceptions.RequestException as _:
            streamlit.warning(
                "Failed to stop simulation, or there is no job creation to be stopped.",
                icon="⚠️",
            )
            return None

    @staticmethod
    def stop(TC_base: str, simulation_base: str):
        """
        Stop the simulation. To do this, we just need to stop the simulation in TC and
        also in simulation backend server.

        Parameters
        ----------
        TC_base : str
            The base URL of the TC server.
        simulation_base : str
            The base URL of the simulation backend server.

        """
        try:
            _ = MosaicRequest.tc_stop(TC_base)
            _ = MosaicRequest.simulation_stop(simulation_base)
            streamlit.success("Simulation stopped successfully.", icon="✅")
            return None
        except requests.exceptions.RequestException as _:
            return None

    @staticmethod
    def send_request(
        url: str,
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, Any]] = None,
        timeout: int | None = None,
    ) -> requests.Response:
        """
        Send an HTTP request to the specified endpoint.

        Parameters
        ----------
        url : str
            The URL of the endpoint to send the request to.
        method : str, optional
            The HTTP method to use (GET, POST, PUT, DELETE, etc.), by default POST.
        data : Dict[str, Any], optional
            The data to send in the request body, by default None.
        params : Dict[str, Any], optional
            The URL parameters to include, by default None.
        headers : Dict[str, Any], optional
            The headers to include in the request, by default None.
        timeout : int, optional
            The timeout for the request in seconds, by default None.

        Returns
        -------
        requests.Response
            The response from the server.

        Raises
        ------
        requests.exceptions.RequestException
            If the request fails.
        """

        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            raise
