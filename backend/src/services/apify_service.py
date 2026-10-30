import os
import asyncio
import re
from typing import List, Optional
from apify_client import ApifyClientAsync
from src.schemas.cv import JobDetail


# LinkedIn datePosted values (shared by valig/linkedin-jobs-scraper)
DATE_POSTED_VALUES = {
    "24h": "r86400",
    "7d": "r604800",
    "30d": "r2592000",
}

# Google postedWithin values (inovaflow/google-jobs-scraper)
GOOGLE_DATE_WITHIN = {
    "24h": "day",
    "7d": "week",
    "30d": "month",
}

# LinkedIn f_WT workplace-type codes, passed to the actor via urlParam
WORKPLACE_TYPE_CODES = {
    "presencial": "1",
    "on-site": "1",
    "remoto": "2",
    "remote": "2",
    "hibrido": "3",
    "hybrid": "3",
}


# All 47 Google editions supported by inovaflow/google-jobs-scraper.
# Country names, English/Spanish variants and common cities. Order matters:
# US before Mexico protects "New Mexico"; UK before Ireland protects
# "Northern Ireland"; Spain before Argentina/Colombia protects ambiguous
# city names such as "Córdoba" and "Cartagena".
COUNTRY_KEYWORDS = (
    (("united states", "usa", "us", "new york", "nyc", "san francisco", "los angeles",
      "chicago", "austin", "seattle", "boston", "miami", "dallas", "houston",
      "atlanta", "denver", "washington", "silicon valley", "indiana",
      "indianapolis", "new mexico"), "us"),
    (("united kingdom", "uk", "britain", "great britain", "england", "scotland",
      "wales", "northern ireland", "london", "edinburgh", "leeds", "bristol"), "gb"),
    (("ireland", "dublin", "cork", "galway"), "ie"),
    (("canada", "canadá", "toronto", "vancouver", "montreal", "montréal", "ottawa",
      "calgary", "edmonton", "quebec", "québec"), "ca"),
    (("australia", "sydney", "melbourne", "brisbane", "perth", "adelaide",
      "canberra"), "au"),
    (("new zealand", "nueva zelanda", "auckland", "wellington", "christchurch"), "nz"),
    (("spain", "españa", "madrid", "barcelona", "valencia", "seville", "sevilla",
      "bilbao", "malaga", "málaga", "zaragoza", "murcia", "canary islands",
      "canarias"), "es"),
    (("mexico", "méxico", "mexico city", "ciudad de méxico", "ciudad de mexico",
      "guadalajara", "monterrey", "puebla", "tijuana", "queretaro",
      "querétaro"), "mx"),
    (("colombia", "bogotá", "bogota", "medellín", "medellin", "cali", "barranquilla",
      "cartagena", "bucaramanga"), "co"),
    (("argentina", "buenos aires", "córdoba", "cordoba", "rosario", "mendoza",
      "la plata", "tucumán", "tucuman"), "ar"),
    (("chile", "santiago de chile", "valparaíso", "valparaiso", "concepción",
      "concepcion", "antofagasta", "la serena"), "cl"),
    (("brazil", "brasil", "são paulo", "sao paulo", "rio de janeiro", "brasília",
      "brasilia", "belo horizonte", "curitiba", "porto alegre", "recife",
      "fortaleza"), "br"),
    (("france", "francia", "paris", "lyon", "marseille", "toulouse", "nice", "nantes",
      "bordeaux", "lille"), "fr"),
    (("germany", "deutschland", "alemania", "berlin", "munich", "münchen", "hamburg",
      "frankfurt", "cologne", "köln", "stuttgart", "düsseldorf", "dusseldorf"), "de"),
    (("netherlands", "países bajos", "paises bajos", "holland", "amsterdam",
      "rotterdam", "the hague", "la haya", "utrecht", "eindhoven"), "nl"),
    (("belgium", "bélgica", "belgica", "brussels", "bruselas", "antwerp", "ghent",
      "bruges"), "be"),
    (("switzerland", "suiza", "zurich", "zúrich", "geneva", "ginebra", "basel",
      "bern", "lausanne"), "ch"),
    (("austria", "vienna", "viena", "salzburg", "graz", "linz"), "at"),
    (("italy", "italia", "rome", "roma", "milan", "milano", "turin", "torino",
      "florence", "firenze", "naples", "napoli", "bologna", "venice", "venezia"), "it"),
    (("portugal", "lisbon", "lisboa", "porto", "braga", "coimbra"), "pt"),
    (("sweden", "suecia", "stockholm", "gothenburg", "göteborg", "malmö", "malmo"),
     "se"),
    (("norway", "noruega", "oslo", "bergen", "trondheim", "stavanger"), "no"),
    (("denmark", "dinamarca", "copenhagen", "copenhague", "københavn", "aarhus",
      "odense"), "dk"),
    (("finland", "finlandia", "helsinki", "espoo", "tampere", "turku"), "fi"),
    (("poland", "polonia", "warsaw", "varsovia", "krakow", "kraków", "wroclaw",
      "wrocław", "gdansk", "gdańsk", "poznan", "poznań"), "pl"),
    (("czech republic", "czechia", "chequia", "república checa", "republica checa",
      "prague", "praga", "brno", "ostrava"), "cz"),
    (("hungary", "hungría", "hungria", "budapest", "debrecen", "szeged"), "hu"),
    (("romania", "rumanía", "rumania", "bucharest", "bucarest", "cluj",
      "cluj-napoca", "timisoara", "timișoara", "iasi", "iași"), "ro"),
    (("greece", "grecia", "athens", "atenas", "thessaloniki", "salonica", "patras"),
     "gr"),
    (("turkey", "turquía", "turquia", "istanbul", "ankara", "izmir", "antalya"), "tr"),
    (("japan", "japón", "japon", "tokyo", "osaka", "kyoto", "yokohama", "nagoya",
      "fukuoka", "sapporo"), "jp"),
    (("south korea", "corea del sur", "seoul", "seúl", "busan", "incheon", "daegu"),
     "kr"),
    (("hong kong", "hongkong"), "hk"),
    (("taiwan", "taiwán", "taipei", "kaohsiung", "taichung"), "tw"),
    (("philippines", "filipinas", "manila", "quezon city", "cebu", "davao"), "ph"),
    (("malaysia", "malasia", "kuala lumpur", "penang", "johor bahru"), "my"),
    (("indonesia", "jakarta", "yakarta", "surabaya", "bandung", "bali", "denpasar"),
     "id"),
    (("thailand", "tailandia", "bangkok", "chiang mai", "phuket", "pattaya"), "th"),
    (("vietnam", "viet nam", "hanoi", "hà nội", "ho chi minh", "hồ chí minh",
      "saigon", "da nang", "haiphong"), "vn"),
    (("israel", "tel aviv", "jerusalem", "haifa", "herzliya"), "il"),
    (("nigeria", "lagos", "abuja", "port harcourt", "ibadan"), "ng"),
    (("kenya", "nairobi", "mombasa", "kisumu"), "ke"),
    (("egypt", "egipto", "cairo", "el cairo", "alexandria", "giza"), "eg"),
    (("india", "bangalore", "bengaluru", "mumbai", "delhi", "new delhi", "hyderabad",
      "pune", "chennai", "kolkata", "gurgaon", "noida"), "in"),
    (("singapore", "singapur"), "sg"),
    (("south africa", "sudáfrica", "sudafrica", "johannesburg", "cape town",
      "durban", "pretoria"), "za"),
    (("united arab emirates", "emiratos árabes", "emiratos arabes", "uae", "dubai",
      "abu dhabi", "sharjah"), "ae"),
)


def _map_country(target_location: Optional[str], job_language: Optional[str]) -> str:
    """Map target location or job language to the actor's two-letter Google edition."""
    loc_lower = (target_location or "").lower()

    for keywords, code in COUNTRY_KEYWORDS:
        if any(re.search(rf"\b{re.escape(keyword)}\b", loc_lower) for keyword in keywords):
            return code

    if job_language == "es":
        return "es"

    return "us"


def _build_workplace_params(location_type: Optional[str], workplace_types: Optional[str]) -> List[dict]:
    """Map frontend labels to the LinkedIn f_WT url parameter (1=on-site, 2=remote, 3=hybrid)."""
    if location_type == "remote":
        codes = ["2"]
    else:
        codes = []
        for value in (workplace_types or "").split(","):
            code = WORKPLACE_TYPE_CODES.get(value.strip().lower())
            if code and code not in codes:
                codes.append(code)

    if not codes:
        return []
    return [{"key": "f_WT", "value": ",".join(codes)}]


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


async def _fetch_linkedin_role(
    client: ApifyClientAsync,
    actor_id: str,
    role: str,
    limit: int,
    location: Optional[str],
    date_value: Optional[str],
    workplace_params: List[dict],
) -> List[dict]:
    """Run valig/linkedin-jobs-scraper for a single search role."""
    run_input = {
        "keywords": role,
        "limit": limit,
    }
    if location:
        run_input["location"] = location
    if date_value:
        run_input["datePosted"] = date_value
    if workplace_params:
        run_input["urlParam"] = workplace_params

    print(f"[APIFY_SERVICE] Calling Apify actor '{actor_id}' with run_input: {run_input}", flush=True)
    run = await client.actor(actor_id).call(run_input=run_input)
    print(f"[APIFY_SERVICE] Actor completed. Status: {run.status}. Dataset ID: {run.default_dataset_id}", flush=True)
    dataset = await client.dataset(run.default_dataset_id).list_items()
    print(f"[APIFY_SERVICE] Retrieved {len(dataset.items)} items from dataset.", flush=True)
    return list(dataset.items)


def _linkedin_job_from_item(item: dict) -> Optional[JobDetail]:
    """Map valig/linkedin-jobs-scraper output fields to JobDetail."""
    title = item.get("title") or item.get("jobTitle") or "Posición Desconocida"
    company = item.get("companyName") or item.get("company") or "Empresa Desconocida"
    location = item.get("location") or "Remoto / No especificado"
    link = item.get("url") or item.get("jobUrl") or item.get("applyUrl") or ""
    description = item.get("description") or item.get("jobDescription") or ""

    if not link:
        return None

    return JobDetail(
        title=title,
        company=company,
        location=location,
        link=link,
        description=description[:800],
        saved_to_notion=False,
    )


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
    """Scrape LinkedIn jobs with valig/linkedin-jobs-scraper.

    The actor takes a single `keywords` string, so one run is issued per CV role
    (max 3) and the results are merged. Filters are applied post-hoc because the
    actor has no resume-keyword scoring.
    """
    actor_id = os.getenv("LINKEDIN_ACTOR_ID", "valig/linkedin-jobs-scraper")

    roles = _build_keywords(query, target_roles, job_language)[:3]
    date_value = DATE_POSTED_VALUES.get(date_posted)
    workplace_params = _build_workplace_params(location_type, workplace_types)
    location = (target_location or "").strip() or None

    # Buffer per role so post-filters (title/language) still leave enough results
    per_role_limit = min(max(limit, 25), 100)

    try:
        batches = await asyncio.gather(
            *(
                _fetch_linkedin_role(
                    client, actor_id, role, per_role_limit, location, date_value, workplace_params
                )
                for role in roles
            ),
            return_exceptions=True,
        )

        from src.services.gemini_service import is_spanish, is_english

        role_tokens = _role_tokens(target_roles)
        seen_links = set()
        jobs = []

        for batch in batches:
            if isinstance(batch, Exception):
                print(f"LinkedIn role search failed: {str(batch)}", flush=True)
                continue

            for item in batch:
                job = _linkedin_job_from_item(item)
                if not job or job.link in seen_links:
                    continue

                # Data-driven relevance filter: job title must overlap CV role tokens.
                if not _ts_relevant_title(job.title, role_tokens):
                    continue

                text_to_check = f"{job.title} {job.description or ''}"
                if job_language == "es" and not is_spanish(text_to_check):
                    continue
                if job_language == "en" and not is_english(text_to_check):
                    continue

                seen_links.add(job.link)
                jobs.append(job)
                if len(jobs) >= limit:
                    return jobs

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
    """Scrape Google jobs with inovaflow/google-jobs-scraper.

    Date and remote filtering are native actor inputs; only language and
    role-title relevance are filtered locally because the actor has no
    equivalent for them.
    """
    actor_id = os.getenv("GOOGLE_ACTOR_ID", "inovaflow/google-jobs-scraper")

    run_input = {
        "queries": _build_keywords(query, target_roles, job_language)[:3],
        "country": _map_country(target_location, job_language),
        # Buffer because title/language filters drop items after the actor runs
        "maxJobsPerQuery": min(max(limit, 25), 100),
        "language": job_language if job_language in ("es", "en") else "en",
        # One resolved apply link is enough for the UI and keeps the run fast
        "maxApplyOptions": 1,
    }

    posted_within = GOOGLE_DATE_WITHIN.get(date_posted)
    if posted_within:
        run_input["postedWithin"] = posted_within

    if location_type == "remote" or (workplace_types or "").strip().lower() in ("remoto", "remote"):
        run_input["remoteOnly"] = True

    location = (target_location or "").strip()
    if location:
        run_input["locations"] = [location]

    try:
        print(f"[APIFY_SERVICE] Calling Apify actor '{actor_id}' with run_input: {run_input}", flush=True)
        run = await client.actor(actor_id).call(run_input=run_input)
        print(f"[APIFY_SERVICE] Actor completed. Status: {run.status}. Dataset ID: {run.default_dataset_id}", flush=True)
        dataset = await client.dataset(run.default_dataset_id).list_items()
        print(f"[APIFY_SERVICE] Retrieved {len(dataset.items)} items from dataset.", flush=True)

        from src.services.gemini_service import is_spanish, is_english

        role_tokens = _role_tokens(target_roles)
        date_filter_active = date_posted in GOOGLE_DATE_WITHIN
        jobs = []

        for item in dataset.items:
            title = item.get("title") or "Posición Desconocida"
            company = item.get("company") or "Empresa Desconocida"
            job_location = item.get("location") or "Remoto / No especificado"
            description = item.get("description") or ""

            apply_options = item.get("applyOptions") or []
            link = item.get("applyUrl") or ""
            if not link:
                link = next(
                    (opt.get("url") for opt in apply_options if isinstance(opt, dict) and opt.get("url")),
                    "",
                )
            if not link:
                link = item.get("googleUrl") or ""

            if not link:
                continue

            # Data-driven relevance filter: title must overlap CV role tokens.
            if not _ts_relevant_title(title, role_tokens):
                continue

            # Programmatically filter out wrong language jobs early
            text_to_check = f"{title} {description}"
            if job_language == "es" and not is_spanish(text_to_check):
                continue
            if job_language == "en" and not is_english(text_to_check):
                continue

            # The actor keeps jobs without a stated age even when postedWithin is set.
            has_date = item.get("ageDays") is not None or bool(item.get("postedAt") or item.get("postedText"))

            jobs.append(JobDetail(
                title=title,
                company=company,
                location=job_location,
                link=link,
                description=description[:800],
                saved_to_notion=False,
                date_posted_unknown=date_filter_active and not has_date,
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
