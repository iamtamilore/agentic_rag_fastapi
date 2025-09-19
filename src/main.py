from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import os
import re
from typing import List, Annotated, Dict, Any

from .db_manager import DatabaseManager
from .auth.security import verify_password, create_access_token, verify_access_token
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama

# --- Security Setup ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI(title="Clinical RAG Co-pilot API", version="1.0.0")

# --- Core Components Initialization ---
db_manager = DatabaseManager(
    host=os.getenv("DB_HOST", "db"),
    port=os.getenv("DB_PORT", "5432"),
    user=os.getenv("DB_USER", "rag_user"),
    password=os.getenv("DB_PASSWORD", "password123"),
    dbname=os.getenv("DB_NAME", "rag_db"),
)
embeddings_model = OllamaEmbeddings(
    model="nomic-embed-text", base_url="http://ollama:11434"
)
llm = Ollama(model="llama3.1", base_url="http://ollama:11434")


# --- PII Redaction Helper ---
def redact_pii(text: str, patient_name: str) -> str:
    if patient_name:
        return re.sub(
            r"\b" + re.escape(patient_name) + r"\b",
            "[PATIENT_NAME]",
            text,
            flags=re.IGNORECASE,
        )
    return text


# --- API Data Models ---
class Token(BaseModel):
    access_token: str
    token_type: str


class Doctor(BaseModel):
    id: int
    username: str
    full_name: str
    role: str


class QueryRequest(BaseModel):
    patient_id: int
    question: str


class QueryResponse(BaseModel):
    answer: str
    retrieved_context: list[str]


class PatientLookupRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str


class PatientLookupResponse(BaseModel):
    patient_id: int
    message: str


class SOAPNoteRequest(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class SOAPNoteResponse(BaseModel):
    success: bool
    message: str


# --- Security Dependency ---
async def get_current_doctor(token: Annotated[str, Depends(oauth2_scheme)]) -> Doctor:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_exception
    doctor_data = db_manager.get_doctor_by_username(payload.get("sub"))
    if doctor_data is None:
        raise credentials_exception
    return Doctor(**doctor_data)


# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the Clinical RAG Co-pilot API"}


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    doctor = db_manager.get_doctor_by_username(form_data.username)
    if not doctor or not verify_password(form_data.password, doctor["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": doctor["username"], "role": doctor["role"]}
    )
    db_manager.log_action(doctor_id=doctor["id"], action="DOCTOR_LOGIN")
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/find-patient", response_model=PatientLookupResponse)
async def find_patient(
    request: PatientLookupRequest,
    current_doctor: Annotated[Doctor, Depends(get_current_doctor)],
):
    patient_id = db_manager.find_patient_by_details(
        request.first_name, request.last_name, request.date_of_birth
    )
    if patient_id is None:
        raise HTTPException(
            status_code=404, detail="Patient not found or details are ambiguous."
        )
    db_manager.log_action(
        doctor_id=current_doctor.id,
        action=f"SEARCHED_FOR_PATIENT",
        patient_id=patient_id,
    )
    return PatientLookupResponse(
        patient_id=patient_id,
        message=f"Patient found by Dr. {current_doctor.full_name}.",
    )


@app.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    current_doctor: Annotated[Doctor, Depends(get_current_doctor)],
):
    question_embedding = embeddings_model.embed_query(request.question)

    # Updated to correctly handle the richer data from db_manager
    retrieved_docs_with_metadata = db_manager.find_similar_chunks(
        request.patient_id, question_embedding, k=3
    )

    retrieved_content = []
    if retrieved_docs_with_metadata:
        for doc in retrieved_docs_with_metadata:
            formatted_doc = f"Date: {doc['event_date'].strftime('%Y-%m-%d')}\nPhysician: {doc['attending_physician']}\nContent: {doc['content']}"
            retrieved_content.append(formatted_doc)

    context_string = (
        "\n\n".join(retrieved_content)
        if retrieved_content
        else "No relevant medical records were found for this patient."
    )

    prompt_template = (
        f"CONTEXT:\n{context_string}\n\nUSER'S QUESTION:\n{request.question}\n\nANSWER:"
    )
    final_answer = llm.invoke(prompt_template)

    patient_info = db_manager.get_patient_by_id(request.patient_id)
    patient_name = (
        f"{patient_info['first_name']} {patient_info['last_name']}"
        if patient_info
        else ""
    )
    db_manager.log_query(
        request.patient_id,
        redact_pii(request.question, patient_name),
        context_string,
        redact_pii(final_answer, patient_name),
    )
    db_manager.log_action(
        doctor_id=current_doctor.id,
        action="ASKED_QUESTION",
        patient_id=request.patient_id,
    )

    # Return the formatted content for the API response
    return QueryResponse(answer=final_answer, retrieved_context=retrieved_content)


@app.post("/patients/{patient_id}/notes", response_model=SOAPNoteResponse)
async def create_soap_note(
    patient_id: int,
    request: SOAPNoteRequest,
    current_doctor: Annotated[Doctor, Depends(get_current_doctor)],
):
    try:
        rag_content = f"Subjective: {request.subjective}\nObjective: {request.objective}\nAssessment: {request.assessment}\nPlan: {request.plan}"
        note_embedding = embeddings_model.embed_query(rag_content)

        db_manager.insert_new_soap_note(
            patient_id=patient_id,
            attending_physician=current_doctor.full_name,
            subjective=request.subjective,
            objective=request.objective,
            assessment=request.assessment,
            plan=request.plan,
            embedding=note_embedding,
        )

        db_manager.log_action(
            doctor_id=current_doctor.id,
            action="CREATED_SOAP_NOTE",
            patient_id=patient_id,
        )
        return SOAPNoteResponse(
            success=True, message="New SOAP note successfully saved."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to save SOAP note: {str(e)}"
        )
