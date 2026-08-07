import os
from notion_client import Client
from src.schemas.cv import JobDetail

def save_job_to_notion(job: JobDetail) -> bool:
    """Save a matched job opportunity to the specified Notion database."""
    token = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DATABASE_ID")
    
    if not token or not database_id:
        print("Notion integration skipped: NOTION_API_KEY or NOTION_DATABASE_ID is missing in environmental variables")
        return False
        
    try:
        notion = Client(auth=token)
        
        # Build property dict according to requested columns
        properties = {
            "Título": {
                "title": [
                    {
                        "text": {
                            "content": job.title
                        }
                    }
                ]
            },
            "Empresa": {
                "rich_text": [
                    {
                        "text": {
                            "content": job.company
                        }
                    }
                ]
            },
            "Ubicación": {
                "rich_text": [
                    {
                        "text": {
                            "content": job.location
                        }
                    }
                ]
            },
            "Enlace": {
                "url": job.link if job.link else None
            },
            "Match Score": {
                "number": job.match_score if job.match_score is not None else 0
            },
            "Consejo para Aplicar": {
                "rich_text": [
                    {
                        "text": {
                            "content": job.apply_tip if job.apply_tip else ""
                        }
                    }
                ]
            }
        }
        
        notion.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )
        return True
        
    except Exception as e:
        print(f"Failed to save job to Notion: {str(e)}")
        return False

