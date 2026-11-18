RAG ANALYZER PRO
================

1. Start Applicatie
-------------------
- Docker Compose starten
- PostgreSQL starten
- Streamlit starten

2. Upload Document
------------------
Ondersteunde bestandstypen:
- PDF
- DOCX
- CSV
- XLSX
- PPTX
- MP3
- WAV
- MP4

3. Verwerking
-------------
ProcessorFactory kiest automatisch de juiste processor.

Voorbeeld:
PDF -> PdfProcessor
CSV -> CsvProcessor
DOCX -> DocxProcessor

4. Chunken
----------
Document wordt opgesplitst in chunks.

Instellingen:
- chunk_size = 1000
- chunk_overlap = 200

5. Embeddings
-------------
Model:
models/gemini-embedding-001

6. ChromaDB
-----------
Chunks worden opgeslagen in:

chroma_db/

7. PostgreSQL
-------------
Documents tabel:

- id
- file_name
- file_size
- chunk_count
- uploaded_at
- embedding_model
- status

Chat_history tabel:

- id
- question
- answer
- created_at

8. Vraag Stellen
----------------
RAG Engine:

Vraag
↓
Retriever
↓
Gemini
↓
Antwoord

9. Export
---------
Beschikbaar:

- JSON
- Excel
- PDF

PDF bevat:

- documentnaam
- bestandsgrootte
- chunk count
- vragen
- antwoorden
- metadata

10. Toekomstige Uitbreidingen
-----------------------------
- Dashboard
- Analytics
- Login systeem
- Django portal
- Klantbeheer
- Metadata filtering