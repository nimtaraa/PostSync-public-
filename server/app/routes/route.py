from fastapi import APIRouter, HTTPException,Header
from app.models.agent import AgentState
from app.services.mongodb_service import get_job_summary_from_summary_collection
from app.utils.logger import get_logger
from app.services.agent_graph import app

logger = get_logger(__name__)
router = APIRouter(prefix="/agent", tags=["Agent Workflow"])

LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"

@router.post("/start")
def run_agent_workflow(niche: str,
                    access_token: str = Header(..., description="LinkedIn access token"),
                    person_urn: str = Header(..., description="LinkedIn person URN (e.g. urn:li:person:abcd123)")
):
    """
    🚀 Run the AI agent workflow for a given niche.
    """
    try:
        # ✅ Optional: Verify that access token is valid
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(LINKEDIN_ME_URL, headers=headers)

        if me_response.status_code != 200:
            logger.error("❌ Invalid or expired LinkedIn access token: %s", me_response.text)
            raise HTTPException(status_code=401, detail="Invalid or expired LinkedIn access token")

        linkedin_user = me_response.json()
        logger.info("✅ LinkedIn user verified: %s", linkedin_user.get("id"))

        state = AgentState(
            niche=niche,
            topic=None,
            post_draft=None,
            final_post=None,
            image_asset_urn=None,
            is_approved=False,
            iteration_count=0,
            linkedin_person_urn=person_urn,
            linkedin_access_token=access_token
        )

        logger.info("🚀 Starting workflow for niche: %s", niche)

        final_state = None
        for s in app.stream(state):
            node_name = list(s.keys())[0]
            logger.info("➡ Node executed: %s", node_name)
            final_state = s

        logger.info("🎯 Workflow finished successfully for niche: %s", niche)
        return {"status": "success", "message": "Workflow completed", "final_state": final_state}

    except Exception as e:
        logger.exception("❌ Workflow execution failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.get("/summary")
def get_jobs_summary():
    """
    ✅ Returns total completed and failed jobs.
    """
    try:
        job_summary =get_job_summary_from_summary_collection()  
        logger.info("Job summary fetched: completed=%d, failed=%d", job_summary["total_completed"], job_summary["total_failed"])
        
        return {
            "total_completed": job_summary["total_completed"],
            "total_failed": job_summary["total_failed"]
        }

    except Exception as e:
        logger.exception("Failed to fetch job summary: %s", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch job summary: {str(e)}")
