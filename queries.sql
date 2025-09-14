-- name: get_doctor_by_username
SELECT * FROM doctors WHERE username = %s;

-- name: insert_patient
INSERT INTO patients (first_name, last_name, date_of_birth, gender) VALUES %s ON CONFLICT (first_name, last_name, date_of_birth) DO NOTHING;

-- name: find_patient_by_details
SELECT id FROM patients WHERE first_name = %s AND last_name = %s AND date_of_birth = %s;

-- name: get_patient_by_id
SELECT * FROM patients WHERE id = %s;

-- name: insert_medical_event
INSERT INTO medical_events (patient_id, event_date, attending_physician, assessment, subjective, objective, plan, content, embedding)
VALUES %s ON CONFLICT (patient_id, event_date, content) DO NOTHING;

-- name: insert_new_soap_note
INSERT INTO medical_events (patient_id, event_date, attending_physician, subjective, objective, assessment, plan, content, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);

-- name: insert_query_log
INSERT INTO query_logs (patient_id, user_question, retrieved_context, llm_answer) VALUES (%s, %s, %s, %s);

-- name: insert_audit_log
INSERT INTO audit_log (doctor_id, patient_id, action) VALUES (%s, %s, %s);

-- name: find_similar_chunks
SELECT me.content, me.event_date, me.attending_physician
FROM medical_events me
WHERE me.patient_id = %s
ORDER BY me.embedding <=> %s
LIMIT %s;