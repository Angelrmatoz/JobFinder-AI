import os
import asyncio
import re
from typing import List, Optional
from apify_client import ApifyClientAsync
from src.schemas.cv import JobDetail


# LinkedIn publishedAt values
DATE_POSTED_VALUES = {
    "24h": "r86400",
    "7d": "r604800",
    "30d": "r2592000",
}

# Actor workType values (as documented in actor input schema)
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
    """Map frontend labels to Actor workType array values."""
    if location_type == "remote":
        return ["remote"]

    values = []
    for value in (workplace_types or "").split(","):
        work_type = WORKPLACE_TYPE_VALUES.get(value.strip().lower())
        if work_type and work_type not in values:
            values.append(work_type)
    return values


ROLE_TRANSLATIONS_TO_ES = {
    "full-stack developer": "Desarrollador Full Stack",
    "full stack developer": "Desarrollador Full Stack",
    "fullstack developer": "Desarrollador Full Stack",
    "frontend developer": "Desarrollador Frontend",
    "front-end developer": "Desarrollador Frontend",
    "front end developer": "Desarrollador Frontend",
    "backend developer": "Desarrollador Backend",
    "back-end developer": "Desarrollador Backend",
    "back end developer": "Desarrollador Backend",
    "web developer": "Desarrollador Web",
    "software engineer": "Desarrollador de Software",
    "software developer": "Desarrollador de Software",
    "mobile developer": "Desarrollador Móvil",
    "react developer": "Desarrollador React",
    "node developer": "Desarrollador Node",
    "java developer": "Desarrollador Java",
    "python developer": "Desarrollador Python",
}


def _translate_role_to_es(role: str) -> str:
    role_lower = role.strip().lower()
    if role_lower in ROLE_TRANSLATIONS_TO_ES:
        return ROLE_TRANSLATIONS_TO_ES[role_lower]

    translated = role
    translated = re.sub(r"\b(full-stack|fullstack|full stack)\s+developer\b", "Desarrollador Full Stack", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\b(front-end|frontend|front end)\s+developer\b", "Desarrollador Frontend", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\b(back-end|backend|back end)\s+developer\b", "Desarrollador Backend", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bdeveloper\b", "Desarrollador", translated, flags=re.IGNORECASE)
    translated = re.sub(r"\bengineer\b", "Ingeniero", translated, flags=re.IGNORECASE)
    return translated.strip()


def _build_keywords(query: str, target_roles: Optional[List[str]], job_language: Optional[str] = None) -> List[str]:
    """Use role titles from CV for recall; strip work-mode words from query.

    Translates roles to Spanish if job_language is 'es' to improve Spanish job retrieval.
    """
    roles = []
    seen = set()
    for role in target_roles or []:
        normalized = role.strip()
        if job_language == "es":
            normalized = _translate_role_to_es(normalized)
        if normalized and normalized.casefold() not in seen:
            seen.add(normalized.casefold())
            roles.append(normalized)

    if roles:
        return roles[:3]

    cleaned = re.sub(
        r"\b(remote|remoto|hybrid|hibrido|presencial|on-site)\b",
        "",
        query,
        flags=re.IGNORECASE,
    )
    cleaned_query = re.sub(r"\s+", " ", cleaned).strip() or query
    if job_language == "es":
        cleaned_query = _translate_role_to_es(cleaned_query)
    return [cleaned_query]


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
    job_language: Optional[str] = None,
) -> List[JobDetail]:
    """Scrape LinkedIn jobs using Actor native input parameters.

    Uses keyword, locations, workType, publishedAt, resumeKeywords
    as documented in the actor's input schema for maximum precision.
    """
    actor_id = os.getenv("LINKEDIN_ACTOR_ID", "cheap_scraper/linkedin-job-scraper")

    run_input = {
        "keyword": _build_keywords(query, target_roles, job_language),
        "enrichCompanyData": False,
        "excludeRecruitingAgencies": False,
        "filterEasyApply": False,
        "filterUnder10Applicants": False,
        "saveOnlyUniqueItems": True,
        "maxItems": max(limit, 150),
    }

    # Date posted (publishedAt) - "any" means no filter
    published_at = DATE_POSTED_VALUES.get(date_posted)
    if published_at:
        run_input["publishedAt"] = published_at

    # Location (must be in English for LinkedIn to resolve geoId correctly)
    if target_location and target_location.strip():
        run_input["locations"] = [target_location.strip()]
    else:
        run_input["locations"] = ["Worldwide"]

    # Workplace type filter
    work_types = _build_work_types(location_type, workplace_types)
    if work_types:
        run_input["workType"] = work_types

    # Resume keywords for scoring
    resume_keywords = _build_resume_keywords(resume_skills)
    if resume_keywords:
        run_input["resumeKeywords"] = resume_keywords

    try:
        print(f"[APIFY_SERVICE] Calling Apify actor '{actor_id}' with run_input: {run_input}", flush=True)
        run = await client.actor(actor_id).call(run_input=run_input)
        print(f"[APIFY_SERVICE] Actor completed. Status: {run.status}. Dataset ID: {run.default_dataset_id}", flush=True)
        dataset = await client.dataset(run.default_dataset_id).list_items()
        print(f"[APIFY_SERVICE] Retrieved {len(dataset.items)} items from dataset.", flush=True)

        from src.services.gemini_service import is_spanish, is_english

        jobs = []
        for item in dataset.items:
            title = item.get("jobTitle") or item.get("title") or item.get("positionName") or "Posición Desconocida"
            company = item.get("companyName") or item.get("company") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            link = item.get("jobUrl") or item.get("url") or ""
            description = item.get("jobDescription") or item.get("description") or item.get("descriptionText") or ""
            if not link:
                continue

            # Programmatically filter out wrong language jobs early to avoid filling the limit slots with them
            text_to_check = f"{title} {description}"
            if job_language == "es" and not is_spanish(text_to_check):
                continue
            if job_language == "en" and not is_english(text_to_check):
                continue

            jobs.append(JobDetail(title=title, company=company, location=location, link=link, description=description[:800], saved_to_notion=False))
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        print(f"Error scraping LinkedIn Jobs: {str(e)}", flush=True)
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
    job_language: Optional[str] = None,
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
            job_language=job_language,
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
