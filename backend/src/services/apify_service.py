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


def _map_country_and_domain(target_location: Optional[str], job_language: Optional[str]) -> tuple[str, str]:
    """Map target location or job language to country code and google domain."""
    country = "us"
    domain = "google.com"

    loc_lower = (target_location or "").lower()

    if any(k in loc_lower for k in ["spain", "españa", "madrid", "barcelona"]):
        country = "None"
        domain = "google.es"
    elif any(k in loc_lower for k in ["mexico", "méxico"]):
        country = "mx"
        domain = "google.com.mx"
    elif "colombia" in loc_lower:
        country = "None"
        domain = "google.com.co"
    elif "argentina" in loc_lower:
        country = "None"
        domain = "google.com.ar"
    elif "chile" in loc_lower:
        country = "None"
        domain = "google.cl"
    elif any(k in loc_lower for k in ["peru", "perú"]):
        country = "None"
        domain = "google.com.pe"
    elif any(k in loc_lower for k in ["uk", "united kingdom", "london"]):
        country = "uk"
        domain = "google.co.uk"
    elif any(k in loc_lower for k in ["canada", "toronto"]):
        country = "ca"
        domain = "google.ca"
    elif any(k in loc_lower for k in ["brazil", "brasil"]):
        country = "br"
        domain = "google.com.br"
    elif any(k in loc_lower for k in ["france", "paris"]):
        country = "fr"
        domain = "google.fr"
    elif any(k in loc_lower for k in ["germany", "deutschland", "berlin"]):
        country = "de"
        domain = "google.de"
    elif job_language == "es":
        country = "None"
        domain = "google.es"

    # Ensure final country code matches the strict allowed list
    allowed_countries = {"None", "us", "ca", "uk", "de", "fr", "au", "jp", "in", "br", "mx"}
    if country not in allowed_countries:
        country = "None"

    return country, domain


_DATE_RE = re.compile(
    r"\d+\s*(?:hours?|horas?|days?|días?|weeks?|semanas?|months?|mes(?:es)?|years?|años?)",
    re.IGNORECASE,
)


def _looks_like_date(text: str) -> bool:
    """True if the string looks like a relative posting date, not a salary or other noise."""
    lowered = text.lower()
    if "ago" in lowered or "hace" in lowered:
        return True
    return _DATE_RE.search(lowered) is not None


def _extract_posted_at(item: dict) -> Optional[str]:
    """Extract age string from item fields. Ignores non-date noise (e.g. salary strings)."""
    for source in (
        item.get("posted_at"),
        (item.get("detected_extensions") or {}).get("posted_at"),
    ):
        if isinstance(source, str) and _looks_like_date(source):
            return source

    extensions = item.get("extensions") or []
    if isinstance(extensions, list):
        for ext in extensions:
            if isinstance(ext, str) and _looks_like_date(ext):
                return ext
    return None


def _is_within_date_range(posted_text: Optional[str], date_posted: Optional[str]) -> bool:
    """Check if the job age string is within the requested limit (24h, 7d, 30d)."""
    if not date_posted or date_posted == "any":
        return True
    if not posted_text:
        return True

    text = posted_text.lower()

    if date_posted == "24h":
        if any(w in text for w in ["week", "semana", "month", "mes", "year", "año"]):
            return False
        day_match = re.search(r'(\d+)\s*(?:day|día)', text)
        if day_match:
            days = int(day_match.group(1))
            return days <= 1
        return True

    if date_posted == "7d":
        if any(w in text for w in ["month", "mes", "year", "año"]):
            return False
        week_match = re.search(r'(\d+)\s*(?:week|semana)', text)
        if week_match:
            weeks = int(week_match.group(1))
            return weeks <= 1
        day_match = re.search(r'(\d+)\s*(?:day|día)', text)
        if day_match:
            days = int(day_match.group(1))
            return days <= 7
        return True

    if date_posted == "30d":
        if any(w in text for w in ["year", "año"]):
            return False
        month_match = re.search(r'(\d+)\s*(?:month|mes)', text)
        if month_match:
            months = int(month_match.group(1))
            return months <= 1
        week_match = re.search(r'(\d+)\s*(?:week|semana)', text)
        if week_match:
            weeks = int(week_match.group(1))
            return weeks <= 4
        day_match = re.search(r'(\d+)\s*(?:day|día)', text)
        if day_match:
            days = int(day_match.group(1))
            return days <= 30
        return True

    return True


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


def _role_tokens(target_roles: Optional[List[str]]) -> set:
    """Derive role tokens from CV target roles (data-driven, never hardcoded).

    Includes both the original role and its Spanish translation so titles in
    either language overlap. Empty/filtered to single-word noise.
    """
    tokens = set()
    for role in target_roles or []:
        for form in (role, _translate_role_to_es(role)):
            for token in re.split(r"[\W_]+", form.casefold()):
                if len(token) > 2:
                    tokens.add(token)
    return tokens


def _ts_relevant_title(title: str, tokens: set) -> bool:
    """Title overlaps CV role tokens. No tokens => keep (filter disabled)."""
    if not tokens or not title:
        return True
    title_tokens = set(t for t in re.split(r"[\W_]+", title.casefold()) if len(t) > 1)
    return bool(tokens & title_tokens)


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

        role_tokens = _role_tokens(target_roles)

        jobs = []
        for item in dataset.items:
            title = item.get("jobTitle") or item.get("title") or item.get("positionName") or "Posición Desconocida"
            company = item.get("companyName") or item.get("company") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            link = item.get("jobUrl") or item.get("url") or ""
            description = item.get("jobDescription") or item.get("description") or item.get("descriptionText") or ""
            if not link:
                continue

            # Data-driven relevance filter: job title must overlap CV role tokens.
            # Drops unrelated feed jobs (e.g. stacked feed) without hardcoding a profession.
            if not _ts_relevant_title(title, role_tokens):
                continue

            # Programmatically filter to match language jobs to avoid filling the limit slots with them
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


async def scrape_google_jobs(
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
    """Scrape Google jobs using johnvc/google-jobs-scraper actor.

    Maps common advanced filters to maintain parity with LinkedIn scraper.
    """
    actor_id = os.getenv("GOOGLE_ACTOR_ID", "johnvc/google-jobs-scraper")

    # Map country and domain
    country, domain = _map_country_and_domain(target_location, job_language)

    # Build query keywords
    kws = _build_keywords(query, target_roles, job_language)
    query_str = " OR ".join(f'"{kw}"' for kw in kws) if kws else query

    # If location is remote, or workplace types only includes remote
    google_location = ""
    if location_type == "remote" or (workplace_types == "remoto" or workplace_types == "remote"):
        google_location = "Remote"
    elif target_location and target_location.strip():
        google_location = target_location.strip()

    run_input = {
        "query": query_str,
        "country": country,
        "google_domain": domain,
        "include_lrad": False,
        "language": job_language if job_language in ["es", "en"] else "es",
        "lrad_value": "5",
        "max_delay": 1,
        "max_pagination": 1,
        "num_results": 100,
        "output_file": "google_jobs_results.json",
    }

    if google_location:
        run_input["location"] = google_location

    try:
        print(f"[APIFY_SERVICE] Calling Apify actor '{actor_id}' with run_input: {run_input}", flush=True)
        run = await client.actor(actor_id).call(run_input=run_input)
        print(f"[APIFY_SERVICE] Actor completed. Status: {run.status}. Dataset ID: {run.default_dataset_id}", flush=True)
        dataset = await client.dataset(run.default_dataset_id).list_items()
        print(f"[APIFY_SERVICE] Retrieved {len(dataset.items)} items from dataset.", flush=True)

        from src.services.gemini_service import is_spanish, is_english

        role_tokens = _role_tokens(target_roles)

        jobs = []
        for item in dataset.items:
            title = item.get("title") or item.get("jobTitle") or item.get("positionName") or "Posición Desconocida"
            company = item.get("company_name") or item.get("companyName") or item.get("company") or "Empresa Desconocida"
            location = item.get("location") or "Remoto / No especificado"
            description = item.get("description") or item.get("jobDescription") or item.get("descriptionText") or ""

            # Extract link from apply_options list or fallback to top-level link/url
            apply_options = item.get("apply_options") or []
            link = ""
            if apply_options and isinstance(apply_options, list):
                for option in apply_options:
                    if isinstance(option, dict) and option.get("link"):
                        link = option.get("link")
                        break
            if not link:
                link = item.get("link") or item.get("url") or ""

            if not link:
                continue

            # Data-driven relevance filter: title must overlap CV role tokens.
            if not _ts_relevant_title(title, role_tokens):
                continue

            # Programmatically filter out jobs by age/date range early
            # Google Jobs actor does NOT support datePosted natively, so we must filter here
            posted_text = _extract_posted_at(item)
            print(f"[APIFY_SERVICE] Google Job '{title}' posted_at='{posted_text}' (filter={date_posted})", flush=True)
            date_posted_unknown = False
            if date_posted and date_posted != "any":
                if not posted_text:
                    # Age unknown: keep the job. Absence of date != outside range,
                    # and skipping everything the scraper can't date makes Google Jobs useless.
                    print(f"[APIFY_SERVICE] '{title}': no posted_at data, keeping job (age unknown)", flush=True)
                    date_posted_unknown = True
                elif not _is_within_date_range(posted_text, date_posted):
                    print(f"[APIFY_SERVICE] Skipping '{title}': posted_at '{posted_text}' outside {date_posted} range", flush=True)
                    continue

            # Programmatically filter out wrong language jobs early
            text_to_check = f"{title} {description}"
            if job_language == "es" and not is_spanish(text_to_check):
                continue
            if job_language == "en" and not is_english(text_to_check):
                continue

            jobs.append(JobDetail(
                title=title,
                company=company,
                location=location,
                link=link,
                description=description[:800],
                saved_to_notion=False,
                date_posted_unknown=date_posted_unknown
            ))
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        print(f"Error scraping Google Jobs: {str(e)}", flush=True)
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
    """Scrape LinkedIn and Google jobs concurrently and return unified list."""
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
        scrape_google_jobs(
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
