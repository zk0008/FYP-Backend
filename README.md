# FYP-Backend

This repository stores the backend FastAPI server for GroupGPT.

## Contents

1. [Project Overview](#project-overview)

2. [Local Development](#local-development)

3. [Supabase Setup](#supabase-setup)

4. [Deployment](#deployment)

## Project Overview

Chatbots powered by large language models (LLMs) have become valuable tools for individual productivity, but their focus on personal use and tendency to hallucinate hinders their effectiveness in group settings. GroupGPT simplifies knowledge sharing between multiple users by incorporating the chatbot as an additional group member and mitigates hallucinations through retrieval-augmented generation (RAG) and external tool invocations.

- Real-time group messaging functionality is implemented using the Supabase Realtime API, specifically [Postgres Changes](https://supabase.com/docs/guides/realtime/postgres-changes).

    - Client application listens to all insertions and deletions on the `messages` table in the database, filtered by the current chatroom ID.

- RAG functionality is implemented as a [hybrid search](./sql/rag/hybrid_search.sql) that combines [full text](./sql/rag/get_similar_text_chunks.sql) and [vector similarity search](./sql/rag/get_similar_embeddings.sql) rankings using reciprocal rank fusion.

- The tools available to the chatbot are:

    - [arXiv Search](./app/workflows/tools/arxiv.py)

    - [Chunk Retriever](./app/workflows/tools/chunk_retriever.py)

    - [Python REPL](./app/workflows/tools/python_repl.py)

    - [Web Search](./app/workflows/tools/web_search.py)

## Local Development

1. Create a `.env` file as per the `.env.example`. Update the environment variables within using the corrsponding URLs and API keys for the Supabase project and LLM providers.

    > Refer to [Supabase Setup](#supabase-setup) for instructions on setting up the Supabase project.

2. Create a virtual environment for the project and activate it. Use **Python 3.12**.

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # Unix
    .\venv\Scripts\activate.bat  # Windows CMD
    .\venv\Scripts\Activate.ps1  # Windows PowerShell
    ```

3. Install project dependencies.

    ```bash
    pip install -r requirements.txt
    ```

4. Start the local development server

    ```bash
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ```

## Supabase Setup

*TODO*

## Deployment

The backend server was deployed as a Web Service on Render. See [here](https://render.com/docs/your-first-deploy) for the deployment steps.
