import asyncio
import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from src.schemas.cv import CVProfile, JobDetail, CVProcessResponse
from src.services.pdf_service import extract_text_from_pdf
from src.services.gemini_service import parse_cv_with_gemma, evaluate_job_match, generate_chat_response
from src.services.apify_service import scrape_jobs_concurrently
from src.services.notion_service import save_job_to_notion

router = APIRouter()

class ChatRequest(BaseModel):
    question: str
    context: str

@router.post("/api/upload-cv", response_model=CVProcessResponse)
async def upload_cv(
    file: UploadFile = File(...),
    location_type: Optional[str] = Form(None),
    date_posted: Optional[str] = Form(None),
    manual_location: Optional[str] = Form(None),
    workplace_types: Optional[str] = Form(None),
    job_language: Optional[str] = Form(None),
):
    """
    Pipeline completo:
    1. Extraer texto del PDF del CV.
    2. Usar Gemini/Gemma para estructurar el perfil y generar query de búsqueda.
    3. Scrapear ofertas de trabajo de LinkedIn y Google Jobs.
    4. Evaluar afinidad de cada vacante y guardar las > 7 en Notion.
    5. Retornar perfil y listado.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se admiten archivos PDF.")
        
    try:
        print(f"[JOBS_ROUTER] upload_cv: location_type={location_type}, date_posted={date_posted}, manual_location={manual_location}, workplace_types={workplace_types}, job_language={job_language}", flush=True)
        # 1. Leer y extraer texto
        pdf_bytes = await file.read()
        cv_text = extract_text_from_pdf(pdf_bytes)
        
        if not cv_text:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del PDF.")
            
        # 2. Interpretar CV con Gemini
        print("[JOBS_ROUTER] Parsing CV text with Gemini...", flush=True)
        profile = await asyncio.to_thread(parse_cv_with_gemma, cv_text, manual_location)
        print(f"[JOBS_ROUTER] Parsed CV profile: {profile}", flush=True)
        
        # Determine filters with defaults
        effective_date_posted = date_posted if date_posted else "7d"
        effective_location_type = location_type or "both"
        effective_job_language = job_language or "both"
        target_loc = profile.location # Gemini already incorporated manual_location and translated it
        
        # 3. Scrapear ofertas usando la query generada y filtros
        # Limitamos a 15 vacantes para no saturar la API gratuita de Gemini
        print(f"[JOBS_ROUTER] Scraping jobs concurrently for query='{profile.search_query}' location_type='{effective_location_type}' location='{target_loc}' date_posted='{effective_date_posted}'...", flush=True)
        scraped_jobs = await scrape_jobs_concurrently(
            query=profile.search_query,
            limit=15,
            location_type=effective_location_type,
            date_posted=effective_date_posted,
            target_location=target_loc,
            workplace_types=workplace_types,
            resume_skills=profile.skills,
            target_roles=profile.target_roles,
        )
        print(f"[JOBS_ROUTER] Scraped {len(scraped_jobs)} jobs. Commencing matching...", flush=True)
        
        if not scraped_jobs:
            return CVProcessResponse(profile=profile, jobs=[])
            
        # 4. Filtro cognitivo con Gemini en paralelo
        async def evaluate_and_save(job: JobDetail):
            try:
                # Evaluar coincidencia en threadpool
                match_result = await asyncio.to_thread(
                    evaluate_job_match, 
                    profile, 
                    job.title, 
                    job.company, 
                    job.description or "",
                    job_language=effective_job_language
                )
                job.match_score = match_result.match_score
                job.apply_tip = match_result.explanation
                
                # Si supera umbral, guardar en Notion
                if match_result.match_score > 7:
                    saved = await asyncio.to_thread(save_job_to_notion, job)
                    job.saved_to_notion = saved
            except Exception as ex:
                print(f"Error evaluando vacante {job.title}: {str(ex)}")
                job.match_score = 1
                job.apply_tip = "Error al evaluar afinidad."
                
        # Ejecutar evaluaciones de forma concurrente
        await asyncio.gather(*(evaluate_and_save(job) for job in scraped_jobs))
        
        # Ordenar resultados de mayor a menor afinidad
        scraped_jobs.sort(key=lambda x: x.match_score or 0, reverse=True)
        
        return CVProcessResponse(profile=profile, jobs=scraped_jobs)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en pipeline de procesamiento: {str(e)}")

@router.post("/api/chat")
async def chat_with_jobs(req: ChatRequest):
    """
    Chat con el perfil y las vacantes encontradas usando Gemini.
    """
    prompt = f"""
    Eres un asesor de carrera e inteligencia de reclutamiento.
    Se ha procesado el perfil de un candidato y se han obtenido las siguientes vacantes de trabajo:
    
    Contexto actual:
    {req.context}
    
    Pregunta del candidato:
    {req.question}
    
    Responde en español de manera concisa, práctica y útil para el candidato.
    Limita la respuesta a un máximo de 100 palabras a menos que te pida redactar una carta de presentación o mensaje formal.
    """
    
    try:
        answer = await asyncio.to_thread(generate_chat_response, prompt)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en chat: {str(e)}")
