# Smart Medical Records Engine

A doctor asks a question in plain English. The system answers using *that specific
patient's* actual records - and nothing else.

## The problem

A patient's history lives scattered across years of visit notes. When a doctor has eight
minutes and needs to know "has this person ever reacted badly to penicillin?", the answer
is technically in the file - buried somewhere in three years of consultation notes nobody
has time to re-read.

The obvious fix is to let a language model read the notes and answer. The obvious fix is
also where this gets dangerous, because a medical answer that is confidently wrong is worse
than no answer at all, and patient data is the last thing you want leaving the building.

So this is built around three hard rules:

1. **The model may only answer from real notes** - never from memory, never invented
2. **The data never leaves the machine** - the language model runs locally, not in
   somebody's cloud
3. **Every access is logged** - who looked at whose records, and when

## How it answers a question

When a doctor asks *"tell me about this patient's last visit"*:

1. The question is turned into a **vector** - a list of 768 numbers capturing what it
   *means*, not just the words it contains. This is why asking about "penicillin reaction"
   can find a note that says "allergic response to amoxicillin" - similar meaning, different
   words.
2. The database finds the **3 most similar notes** for that patient. Similarity search runs
   *inside* Postgres via pgvector, so the data never has to be shipped somewhere to be
   searched.
3. Those 3 real notes are handed to **Llama 3.1** with instructions to answer using only
   what it was given.
4. The answer, the question, and the exact notes used are all **written to a log** - so
   anyone can later check what the model was told and whether its answer was fair.

Step 4 is the one people skip. It is also the one that makes the system auditable rather
than a black box.

## The safety rail that matters most

Every search is **scoped to a single patient ID**.

This sounds obvious and it is the single most important line in the codebase. Without it,
a similarity search across a shared table will happily surface *another patient's* note
because it happens to be worded similarly. Same illness, same phrasing, wrong human.

The retrieval filters by patient before it ranks by similarity - not after. Cross-patient
leakage is not something you catch in review; it is something you design out.

## Who is allowed in

Doctors log in and receive a **JWT** - a signed token proving who they are, which every
subsequent request must carry. Passwords are stored **bcrypt-hashed**, never in plain text,
so even someone holding the database cannot read them.

Before any note text reaches the language model, it runs through a **PII redaction** step
that strips identifying details. The model gets the clinical substance without the identity
attached.

And every time a doctor opens a patient's record, a row lands in `audit_log`: who, which
patient, what action, when. If somebody ever asks "who accessed this file?", there is an
answer.

## The data model

Notes are stored as **SOAP** - the format clinicians already write in:

- **S**ubjective: what the patient reports
- **O**bjective: what was measured
- **A**ssessment: what the clinician concluded
- **P**lan: what happens next

Structuring it this way means a question about symptoms can be steered toward the parts of
the note where symptoms actually live, instead of treating the whole entry as one
undifferentiated blob.

| Table | Holds |
|---|---|
| `patients` | identity, contact, medical plan |
| `medical_events` | SOAP notes + their 768-dim vector embedding |
| `doctors` | accounts, hashed passwords, roles |
| `query_logs` | every question, the notes retrieved, the answer given |
| `audit_log` | every access, by whom, when |

## Running it

Everything is containerised - the API, the database, the language model, and the data
ingestion all come up together:

```bash
make up          # start everything
make logs        # watch it boot

# create a doctor account
docker exec -it agentic_rag_fastapi-web-1 python /app/scripts/create_doctor.py
```

Then open the API docs, log in as the doctor to get your token, click **Authorize**, and
ask a question at `/ask`.

Because the model runs in its own container alongside the database, **nothing is sent to a
third party**. That is the point: a hospital can run this without any patient data crossing
its own network boundary.

## What is running under the hood

| Piece | What it does |
|---|---|
| **FastAPI** | the web API, with auto-generated interactive docs |
| **PostgreSQL + pgvector** | stores records *and* does the similarity search |
| **Ollama + Llama 3.1** | the language model, running locally |
| **nomic-embed-text** | turns text into the 768-number meaning-vectors |
| **LangChain / LangGraph** | wires the retrieval and generation steps together |
| **Docker Compose** | four services, one command |
| **JWT + bcrypt** | authentication and password hashing |

## Honest limitations

This is a working prototype, not a certified medical device, and nothing here should make
a clinical decision on its own. The redaction is pattern-based rather than a trained model,
so it is a sensible layer of defence rather than a guarantee. The retrieval returns the
3 closest notes - if the relevant history is the 4th, the model will not see it. And a
local model is smaller than a frontier one; the trade is capability for privacy, which for
patient records is the right way round.

---

**Stack:** FastAPI, PostgreSQL, pgvector, Ollama (Llama 3.1), LangChain, LangGraph, Docker
Compose, JWT, bcrypt, pytest
