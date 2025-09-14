TEST
#FIRST RUN
make down, then
make up
CAN CHECK LOGS HERE make logs


#CREATE DOC PROFILE
docker exec -it agentic_rag_fastapi-web-1 python /app/scripts/create_doctor.py

LOGIN USING PROFILE
iyang.thomas
password123

PATIENT IDENTIFIABLE INFORMATION
{
  "first_name": "Kayode",
  "last_name": "Alabi",
  "date_of_birth": "1965-03-15"
}

#SAMPLE QUESTIONS
"Tell me about this patients last visit"?
"Is the patient asthmatic"?
etc

#VERIFY ANSWER IN PATIENT_DATA.CSV