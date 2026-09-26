# Architecture

## Agents
1. Language Agent — English/Telugu/Hindi routing and response localization.
2. Intake Agent — structures symptoms, duration, allergies, current medicines and history.
3. Triage Agent — flags emergency indicators.
4. Medical RAG Agent — retrieves approved reference material.
5. Safety Agent — checks allergies/interactions/contraindication flags for clinician review.
6. Supervisor — routes the case through the workflow.
7. Doctor Review — licensed clinician makes the diagnosis and medication decision.
8. Translation Agent — converts the approved response to the patient's selected language.

## Medicine policy
The system must never turn a condition name into an automatic prescription. Medication, dosage, frequency and duration are entered/approved by the doctor.

## Suggested production upgrades
- PostgreSQL + pgvector
- Authentication and RBAC
- Separate patient/doctor accounts
- Audit log
- Consent management
- Encryption at rest/in transit
- Trusted clinical sources
- Human approval gates
- Prescription verification
- Monitoring and evaluation
