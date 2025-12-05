"""Biography endpoints."""

from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter()


BIOGRAPHY_FILE = Path("data/biography.html")


@router.get("/biography")
async def get_biography() -> dict:
    """Get the artist biography HTML content."""
    try:
        if not BIOGRAPHY_FILE.exists():
            # Return placeholder content if file doesn't exist yet
            return {
                "content": """
                    <h1>Dan Brown</h1>
                    <p class="dates">1949 - 2022</p>
                    <p><em>Biography content will be added here.</em></p>
                    <p>Please provide the biography content to display on this page.</p>
                """
            }

        # Read the biography HTML file
        content = BIOGRAPHY_FILE.read_text(encoding='utf-8')
        return {"content": content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading biography: {str(e)}")
