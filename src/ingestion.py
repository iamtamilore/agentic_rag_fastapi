import os
import csv
import logging
from typing import Dict, Any, List
from langchain_community.embeddings import OllamaEmbeddings
from db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

log = logging.getLogger(__name__)

def ingest_patient_data(
    db_manager: DatabaseManager, 
    embeddings_model: OllamaEmbeddings
):
    """
    Ingests data from a CSV, populating both the patients and medical_events tables.
    """
    log.info("Starting data ingestion from CSV file.")
    try:
        patients_to_insert = []
        all_rows = []
        unique_patients = set()

        with open('patient_data.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                all_rows.append(row)
                patient_tuple = (row['first_name'], row['last_name'], row['date_of_birth'])
                if patient_tuple not in unique_patients:
                    patients_to_insert.append((
                        row['first_name'], row['last_name'],
                        row['date_of_birth'], row.get('gender')
                    ))
                    unique_patients.add(patient_tuple)
        
        log.info(f"Ingesting {len(patients_to_insert)} unique patient records...")
        db_manager.insert_patients(patients_to_insert)
        
        patient_identifiers = list(unique_patients)
        patient_id_map = db_manager.get_patient_ids_by_identifiers(patient_identifiers)
        log.debug("Patient ID Map created.")

        medical_events_to_insert = []
        log.info("Generating embeddings and preparing medical events...")
        
        for row in all_rows:
            identifier_key = (row['first_name'], row['last_name'], row['date_of_birth'])
            patient_db_id = patient_id_map.get(identifier_key)
            
            if not patient_db_id:
                log.warning(f"Skipping event for {row['first_name']}: Patient ID not found.")
                continue

            rag_content = (
                f"Event Date: {row.get('event_date', 'N/A')}\n"
                f"Attending Physician: {row.get('attending_physician', 'N/A')}\n"
                f"Assessment (Diagnosis): {row.get('diagnoses', 'N/A')}\n"
                f"Subjective/Objective (Notes): {row.get('clinical_notes', 'N/A')}\n"
                f"Plan: Prescribed {row.get('medications', 'N/A')}"
            )
            
            record_embedding = embeddings_model.embed_query(rag_content)
            
            medical_events_to_insert.append({
                'patient_id': patient_db_id,
                'event_date': row.get('event_date'),
                'attending_physician': row.get('attending_physician'),
                'diagnosis': row.get('diagnoses'),
                'clinical_notes': row.get('clinical_notes'),
                'content': rag_content,
                'embedding': record_embedding
            })
        
        log.info(f"Ingesting {len(medical_events_to_insert)} medical events...")
        db_manager.insert_medical_events(medical_events_to_insert)
        log.info("Patient data ingestion from CSV complete.")

    except FileNotFoundError:
        log.error("Ingestion failed: 'patient_data.csv' not found.")
        raise
    except Exception as e:
        log.error(f"An unexpected error occurred during ingestion: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    db_manager = DatabaseManager(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "rag_user"),
        password=os.getenv("DB_PASSWORD", "password123"),
        dbname=os.getenv("DB_NAME", "rag_db")
    )
    embeddings_model = OllamaEmbeddings(model="nomic-embed-text", base_url="http://ollama:11434")
    ingest_patient_data(db_manager, embeddings_model)