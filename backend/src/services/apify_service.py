import os
import asyncio
from typing import List
from apify_client import ApifyClientAsync
from src.schemas.cv import JobDetail

async def scrape_linkedin_jobs(client: ApifyClientAsync, query: str, limit: int = 5) -> List[JobDetail]:
    """Scrape LinkedIn job listings using Apify's public LinkedIn Jobs Scraper."""
    actor_id = os.getenv("LINKEDIN_ACTOR_ID", "apify/linkedin-jobs-scraper")
    run_input = {
        "searchQueries": [query],
        "limitPerQuery": limit
    }
    
    try:
        run = await client.actor(actor_id).call(run_input=run_input, timeout_secs=180)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()
        
        jobs = []
        for item in dataset.items:
            title = item.get("title") or item.get("positionName") or "Posición Desconocida"
            company = item.get("companyName") or item.get("company") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            link = item.get("jobUrl") or item.get("url") or ""
            description = item.get("description") or item.get("descriptionText") or ""
            
            if not link:
                continue
                
            jobs.append(
                JobDetail(
                    title=title,
                    company=company,
                    location=location,
                    link=link,
                    description=description[:800], # Limit length to save context
                    saved_to_notion=False
                )
            )
        return jobs
    except Exception as e:
        print(f"Error scraping LinkedIn Jobs: {str(e)}")
        return []

async def scrape_google_jobs(client: ApifyClientAsync, query: str, limit: int = 5) -> List[JobDetail]:
    """Scrape Google Jobs listings using Apify's public Google Jobs Scraper."""
    actor_id = os.getenv("GOOGLE_JOBS_ACTOR_ID", "apify/google-jobs-scraper")
    run_input = {
        "queries": query,
        "maxResultsPerQuery": limit,
        "maxPagesPerQuery": 1
    }
    
    try:
        run = await client.actor(actor_id).call(run_input=run_input, timeout_secs=180)
        dataset = await client.dataset(run["defaultDatasetId"]).list_items()
        
        jobs = []
        for item in dataset.items:
            title = item.get("title") or "Posición Desconocida"
            company = item.get("companyName") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            link = item.get("applyLink") or item.get("jobLink") or item.get("googleJobsUrl") or item.get("url") or ""
            description = item.get("description") or ""
            
            if not link:
                continue
                
            jobs.append(
                JobDetail(
                    title=title,
                    company=company,
                    location=location,
                    link=link,
                    description=description[:800],
                    saved_to_notion=False
                )
            )
        return jobs
    except Exception as e:
        print(f"Error scraping Google Jobs: {str(e)}")
        return []

async def scrape_jobs_concurrently(query: str, limit: int = 5) -> List[JobDetail]:
    """Scrape LinkedIn and Google Jobs in parallel and return unified list."""
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN environment variable is not configured")
        
    client = ApifyClientAsync(token)
    
    results = await asyncio.gather(
        scrape_linkedin_jobs(client, query, limit),
        scrape_google_jobs(client, query, limit),
        return_exceptions=True
    )
    
    all_jobs = []
    for res in results:
        if isinstance(res, list):
            all_jobs.extend(res)
        else:
            print(f"Parallel scraper execution failed: {str(res)}")
            
    # De-duplicate jobs based on URL/link
    seen_links = set()
    unique_jobs = []
    for job in all_jobs:
        if job.link not in seen_links:
            seen_links.add(job.link)
            unique_jobs.append(job)
            
    return unique_jobs
