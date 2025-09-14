import os
import time
import logging
import psycopg2
import json
from datetime import datetime
from psycopg2 import sql
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import execute_values, DictCursor
from typing import List, Dict, Any, Tuple

log = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, host: str, port: str, user: str, password: str, dbname: str):
        self.host, self.port, self.user, self.password, self.dbname = host, port, user, password, dbname
        self.pool = self._connect_with_retry()
        self.queries = self._load_sql_queries()
        log.info("DatabaseManager initialized successfully.")

    def _load_sql_queries(self):
        """Loads SQL queries from queries.sql (text file with -- name blocks)."""
        log.info("Loading SQL queries from file...")
        try:
            # Resolve path to queries.sql (root of project, one level up from /app/src)
            base_dir = os.path.dirname(os.path.abspath(__file__))
            queries_path = os.path.join(base_dir, "..", "queries.sql")
            queries_path = os.path.abspath(queries_path)

            if not os.path.exists(queries_path):
                raise FileNotFoundError(f"queries.sql file not found at {queries_path}")

            with open(queries_path, "r") as f:
                raw = f.read()

            # If JSON format, load it, else parse -- name: blocks
            if raw.strip().startswith("{"):
                return json.loads(raw)
            return self._parse_sql_queries(raw)

        except FileNotFoundError as e:
            log.critical(str(e))
            raise
        except json.JSONDecodeError:
            log.critical("Failed to decode JSON from queries.sql. Attempting to parse as text.")
            with open(queries_path, "r") as f:
                raw = f.read()
            return self._parse_sql_queries(raw)

    def _parse_sql_queries(self, raw_queries: str) -> Dict[str, str]:
        """Parses SQL queries from a text file with -- name: markers."""
        queries = {}
        current_name = None
        current_query = []
        for line in raw_queries.splitlines():
            line = line.strip()
            if line.startswith('-- name:'):
                if current_name and current_query:
                    queries[current_name] = ' '.join(current_query).strip()
                current_name = line.replace('-- name:', '').strip()
                current_query = []
            elif line and not line.startswith('--'):
                current_query.append(line)
        if current_name and current_query:
            queries[current_name] = ' '.join(current_query).strip()
        if not queries:
            raise ValueError("No named queries found in queries.sql")
        return queries

    def _connect_with_retry(self):
        retries = 5
        delay = 2
        for i in range(retries):
            try:
                return ThreadedConnectionPool(
                    1, 20,
                    cursor_factory=DictCursor,
                    host=self.host, port=self.port,
                    user=self.user, password=self.password, dbname=self.dbname
                )
            except (psycopg2.OperationalError, psycopg2.errors.Error) as e:
                log.warning(f"Database connection failed: {e}. Retrying.")
                if i < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                else:
                    log.critical("Failed to connect to the database.")
                    raise

    def get_conn(self): return self.pool.getconn()
    def put_conn(self, conn): self.pool.putconn(conn)

    def insert_patients(self, patients_data: List[Tuple]):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                execute_values(cur, sql.SQL(self.queries['insert_patient']), patients_data, page_size=100)
            conn.commit()
            log.info(f"Successfully processed {len(patients_data)} patient records.")
        finally: self.put_conn(conn)
    
    def get_patient_ids_by_identifiers(self, identifiers: List[Tuple[str, str, str]]) -> Dict[Tuple, int]:
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, first_name, last_name, date_of_birth FROM patients WHERE (first_name, last_name, date_of_birth) IN %s;",
                    (tuple(identifiers),)
                )
                return {
                    (row['first_name'], row['last_name'], str(row['date_of_birth'])): row['id']
                    for row in cur.fetchall()
                }
        finally: self.put_conn(conn)
            
    def insert_medical_events(self, medical_events: List[Dict[str, Any]]):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                data_to_insert = [
                    (
                        event['patient_id'], 
                        event['event_date'], 
                        event.get('attending_physician'),
                        event.get('diagnoses'), # map 'diagnoses' → assessment
                        None,  # subjective
                        None,  # objective
                        None,  # plan
                        event.get('clinical_notes'), # map 'clinical_notes' → content
                        event['embedding']
                    )
                    for event in medical_events
                ]
                query = sql.SQL(self.queries['insert_medical_event'])
                execute_values(cur, query, data_to_insert, page_size=100)
            conn.commit()
            log.info(f"Successfully processed {len(medical_events)} medical event records.")
        finally: self.put_conn(conn)

    def insert_new_soap_note(
        self, patient_id: int, attending_physician: str, subjective: str,
        objective: str, assessment: str, plan: str, embedding: List[float]
    ):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                rag_content = (
                    f"Subjective: {subjective}\nObjective: {objective}\n"
                    f"Assessment: {assessment}\nPlan: {plan}"
                )
                event_date = datetime.now().date()
                cur.execute(
                    sql.SQL(self.queries['insert_new_soap_note']),
                    (patient_id, event_date, attending_physician,
                     subjective, objective, assessment, plan, rag_content, embedding)
                )
            conn.commit()
            log.info(f"Successfully inserted new SOAP note for patient_id: {patient_id}")
        except Exception as e:
            log.error(f"Error inserting new SOAP note: {e}")
            conn.rollback()
            raise
        finally: self.put_conn(conn)

    def find_similar_chunks(self, patient_id: int, query_embedding: List[float], k: int = 5) -> List[str]:
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['find_similar_chunks']), (patient_id, str(query_embedding), k))
                return [row['content'] for row in cur.fetchall()]
        finally: self.put_conn(conn)

    def find_patient_by_details(self, first_name: str, last_name: str, dob: str) -> int | None:
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['find_patient_by_details']), (first_name, last_name, dob))
                results = cur.fetchall()
                if len(results) == 1:
                    return results[0]['id']
                else:
                    log.warning(f"Ambiguous or no patient found for {first_name} {last_name}")
                    return None
        finally: self.put_conn(conn)

    def get_patient_by_id(self, patient_id: int) -> Dict | None:
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['get_patient_by_id']), (patient_id,))
                return cur.fetchone()
        finally: self.put_conn(conn)
    
    def get_doctor_by_username(self, username: str) -> dict | None:
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['get_doctor_by_username']), (username,))
                return cur.fetchone()
        finally: self.put_conn(conn)

    def log_query(self, patient_id: int, question: str, context: str, answer: str):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['insert_query_log']), (patient_id, question, context, answer))
            conn.commit()
            log.info(f"Successfully logged query for patient_id: {patient_id}")
        except Exception as e:
            log.error(f"Error logging query: {e}")
            conn.rollback()
        finally: self.put_conn(conn)

    def log_action(self, doctor_id: int, action: str, patient_id: int | None = None):
        conn = self.get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(self.queries['insert_audit_log']), (doctor_id, patient_id, action))
            conn.commit()
            log.info(f"Audit log created for doctor_id {doctor_id}: {action}")
        except Exception as e:
            log.error(f"Error creating audit log: {e}")
            conn.rollback()
        finally: self.put_conn(conn)
