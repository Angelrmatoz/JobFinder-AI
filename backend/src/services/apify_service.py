import os
import asyncio
import re
from typing import List, Optional
from apify_client import ApifyClientAsync
from src.schemas.cv import JobDetail


DATE_POSTED_VALUES = {
    "24h": "r86400",
    "7d": "r604800",
    "30d": "r2592000",
}

WORKPLACE_TYPE_VALUES = {
    "presencial": "on-site",
    "on-site": "on-site",
    "remoto": "remote",
    "remote": "remote",
    "hibrido": "hybrid",
    "hybrid": "hybrid",
}


def _build_resume_keywords(skills: Optional[List[str]]) -> List[dict]:
    """Convert CV skills into Actor resumeKeywords input."""
    seen = set()
    keywords = []
    for skill in skills or []:
        normalized = skill.strip()
        key = normalized.casefold()
        if normalized and key not in seen:
            seen.add(key)
            keywords.append({"keyword": normalized})
    return keywords


def _build_work_types(location_type: Optional[str], workplace_types: Optional[str]) -> List[str]:
    """Map frontend labels to documented Actor workType values."""
    if location_type == "remote":
        return ["remote"]

    values = []
    for value in (workplace_types or "").split(","):
        work_type = WORKPLACE_TYPE_VALUES.get(value.strip().lower())
        if work_type and work_type not in values:
            values.append(work_type)
    return values

def _build_keywords(query: str, target_roles: Optional[List[str]]) -> List[str]:
    """Use role titles for recall; work mode belongs in workType, not query text."""
    roles = []
    for role in target_roles or []:
        normalized = role.strip()
        if normalized and normalized.casefold() not in {value.casefold() for value in roles}:
            roles.append(normalized)

    if roles:
        return roles[:3]

    cleaned_query = re.sub(
        r"\b(remote|remoto|hybrid|hibrido|presencial|on-site)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )
    return [re.sub(r"\s+", " ", cleaned_query).strip() or query]

async def scrape_linkedin_jobs(
    client: ApifyClientAsync,
    query: str,
    limit: int = 5,
    location_type: Optional[str] = None,
    date_posted: Optional[str] = None,
    target_location: Optional[str] = None,
    workplace_types: Optional[str] = None,
    resume_skills: Optional[List[str]] = None,
    target_roles: Optional[List[str]] = None,
) -> List[JobDetail]:
    """Scrape LinkedIn jobs through Actor native keyword search filters."""
    actor_id = os.getenv("LINKEDIN_ACTOR_ID", "cheap_scraper/linkedin-job-scraper")
    run_input = {
        "keyword": _build_keywords(query, target_roles),
        "enrichCompanyData": False,
        "excludeRecruitingAgencies": False,
        "filterEasyApply": False,
        "filterUnder10Applicants": False,
        "saveOnlyUniqueItems": True,
        "maxItems": max(limit, 150),
    }
    published_at = DATE_POSTED_VALUES.get(date_posted)
    if published_at:
        run_input["publishedAt"] = published_at
    if target_location and target_location.strip():
        run_input["locations"] = [target_location.strip()]

    work_types = _build_work_types(location_type, workplace_types)
    if work_types:
        run_input["workType"] = work_types

    resume_keywords = _build_resume_keywords(resume_skills)
    if resume_keywords:
        run_input["resumeKeywords"] = resume_keywords

    try:
        print(f"[APIFY_SERVICE] Calling Apify actor '{actor_id}' with run_input: {run_input}", flush=True)
        run = await client.actor(actor_id).call(run_input=run_input)
        print(f"[APIFY_SERVICE] Actor completed. Status: {run.status}. Dataset ID: {run.default_dataset_id}", flush=True)
        dataset = await client.dataset(run.default_dataset_id).list_items()
        print(f"[APIFY_SERVICE] Retrieved {len(dataset.items)} items from dataset.", flush=True)

        jobs = []
        for item in dataset.items:
            title = item.get("jobTitle") or item.get("title") or item.get("positionName") or "Posición Desconocida"
            company = item.get("companyName") or item.get("company") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            link = item.get("jobUrl") or item.get("url") or ""
            description = item.get("jobDescription") or item.get("description") or item.get("descriptionText") or ""
            if not link:
                continue
            jobs.append(JobDetail(title=title, company=company, location=location, link=link, description=description[:800], saved_to_notion=False))
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        print(f"Error scraping LinkedIn Jobs: {str(e)}", flush=True)
        return []

async def scrape_google_jobs(client: ApifyClientAsync, query: str, limit: int = 5) -> List[JobDetail]:
    """Scrape Google Jobs listings using Apify's public Google Jobs Scraper."""
    actor_id = os.getenv("GOOGLE_JOBS_ACTOR_ID", "orgupdate/google-jobs-scraper")
    run_input = {
        "includeKeyword": query,
        "pagesToFetch": 1,
    }
    
    try:
        run = await client.actor(actor_id).call(run_input=run_input)
        dataset = await client.dataset(run.default_dataset_id).list_items()
        
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
            
            if len(jobs) >= limit:
                break
                
        return jobs
    except Exception as e:
        print(f"Error scraping Google Jobs: {str(e)}")
        return []

async def scrape_jobs_concurrently(
    query: str,
    limit: int = 5,
    location_type: Optional[str] = None,
    date_posted: Optional[str] = None,
    target_location: Optional[str] = None,
    workplace_types: Optional[str] = None,
    resume_skills: Optional[List[str]] = None,
    target_roles: Optional[List[str]] = None,
) -> List[JobDetail]:
    """Scrape LinkedIn jobs and return unified list."""
    token = os.getenv("APIFY_TOKEN")
    if not token:
        raise ValueError("APIFY_TOKEN environment variable is not configured")
        
    client = ApifyClientAsync(token)
    
    results = await asyncio.gather(
        scrape_linkedin_jobs(
            client=client,
            query=query,
            limit=limit,
            location_type=location_type,
            date_posted=date_posted,
            target_location=target_location,
            workplace_types=workplace_types,
            resume_skills=resume_skills,
            target_roles=target_roles,
        ),
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
