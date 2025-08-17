"""
Main file for simulation backend via FastAPI.
"""

import time
from datetime import datetime
from typing import Dict

from fastapi import BackgroundTasks, Body, FastAPI
from job_service import JobsCreationRequest, JobService

app = FastAPI()

# Add this at the top level of the file
job_creation_status = {
    "start_time": None,
    "stop_requested": False,
    "stop_time": None,
    "simulation_name": None,
}


@app.get("/time")
async def get_current_time() -> Dict:
    """
    Get current time in YYYY-MM-DD HH:MM:SS format. Mainly to test for response.

    Returns
    -------
    Dict
        JSON response with current time.
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"current_time": current_time}


@app.get("/status")
async def get_status() -> Dict:
    """
    Get the status of the job creation process.

    Returns
    -------
    Dict
        JSON response with the status of the job creation process.
    """
    return job_creation_status


@app.post("/jobs/stop")
async def stop_jobs():
    """
    Stop the job creation process.

    Returns
    -------
    Dict
        JSON response with the message indicating the job creation process has been
        stopped.
    """
    job_creation_status["stop_requested"] = True
    return {"message": "Job creation process has been stopped"}


@app.post("/jobs/create")
async def create_jobs(
    background_tasks: BackgroundTasks,
    jobs_creation_request: JobsCreationRequest = Body(...),
) -> Dict:
    """
    The main job creation endpoint.

    Parameters
    ----------
    background_tasks : BackgroundTasks
        The background tasks to run the job creation process.
    jobs_creation_request : JobsCreationRequest
        The request body containing the jobs creation request.

    Returns
    -------
    Dict
        JSON response with the message indicating the job creation process has been
        started.
    """
    # Reset the status before starting new job creation
    job_creation_status["start_time"] = None
    job_creation_status["stop_requested"] = False
    job_creation_status["stop_time"] = None
    job_creation_status["simulation_name"] = jobs_creation_request.configuration.name

    job_service = JobService(
        jobs_creation_request=jobs_creation_request,
        job_creation_status=job_creation_status,
    )

    def create_jobs_and_update_status():
        """
        Background task to create jobs and update the status.
        """
        job_creation_status["start_time"] = time.time()
        job_service.create_jobs()

    background_tasks.add_task(create_jobs_and_update_status)

    return {"message": "Job creation process has been started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
