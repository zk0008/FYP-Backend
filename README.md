# FYP-Backend

This repository contains the backend FastAPI server for GroupGPT. See [here](https://github.com/nicholasbay/FYP-Frontend) for the frontend client.

## Contents

1. [Project Overview](#project-overview)

2. [Functionality Deep Dive](#functionality-deep-dive)

2. [Local Development](#local-development)

3. [Supabase Setup](#supabase-setup)

4. [Deployment](#deployment)

## Project Overview

Chatbots powered by large language models have become valuable tools for individual productivity, but their focus on personal use and tendency to hallucinate hinders their effectiveness in group settings. GroupGPT simplifies knowledge sharing between multiple users by incorporating the chatbot as an additional group member and mitigates hallucinations through retrieval-augmented generation (RAG) and external tool invocations.

## Functionality Deep Dive

### Real-Time Group Messaging

The real-time group messaging functionality is implemented using the Supabase Realtime API, specifically [Postgres Changes](https://supabase.com/docs/guides/realtime/postgres-changes).

The client application listens to all insertions and deletions on the `messages` table in the database, filtered by the current chatroom ID. See the [frontend's custom hook](https://github.com/nicholasbay/FYP-Frontend/blob/main/hooks/messages/use-realtime-messages.ts) for the implementation details.

### Retrieval-Augmented Generation

#### File Indexing

GroupGPT accepts PDFs and images as inputs to its knowledge base, with separate indexing pipelines for each.

![PDF Indexing Pipeline](./assets/pdf-indexing-pipeline.png)

See [`pdf_pipeline.py`](./app/pipelines/pdf_pipeline.py) for the implementation details.

![Image Indexing Pipeline](./assets/image-indexing-pipeline.png)

See [`image_pipeline.py`](./app/pipelines/image_pipeline.py) for the implementation details.

#### Chunk Retrieval

Chunk retrieval is implemented as a hybrid of both full text and vector similarity searches. The rankings from both searches are combined into a single ordered list using reciprocal rank fusion.

![Chunk Retrieval Pipeline](./assets/chunk_retrieval_pipeline.png)

See [`hybrid_search.sql`](./sql_functions/rag/hybrid_search.sql), [`get_similar_text_chunks.sql`](./sql_functions/rag/get_similar_text_chunks.sql), and [`get_similar_embeddings.sql`](./sql_functions/rag/get_similar_embeddings.sql) for the implementation details.

### Chatbot Tools

The following tools are available to the chatbot.

| Tool | Description |
|------|-------------|
| [arXiv Search](./app/workflows/tools/arxiv.py) | Searches the arXiv database for relevant published research |
| [Chunk Retriever](./app/workflows/tools/chunk_retriever.py) | Searches the knowledge base for specific information related to the user's context |
| [Python REPL](./app/workflows/tools/python_repl.py) | Executes Python code and returns the printed result; useful for accurate calculations |
| [Web Search](./app/workflows/tools/web_search.py) | Searches the web for up-to-date information |

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

> All of the following steps can be done through the Supabase online dashboard.

### Create Supabase Project

1. Create a Supabase project and update the Supabase variables within the `.env` file.

### Set Up PostgreSQL Database

1. Create the enumerated types required for the `invite` table.

    | Schema | Name | Values |
    | --- | --- | --- |
    | `public` | `invite_status` | `PENDING`, `ACCEPTED`, `REJECTED` |

2. Activate the following extensions for the database.

    - `pgsodium`

    - `vector`

    - `pgjwt`

3. Create the database tables according to the ER diagram below.

    ![ER Diagram](./assets/er_diagram.png)

4. Create the SQL functions for each of the `.sql` files within [`sql_functions`](./sql_functions/). These functions will be remotely invoked for various GroupGPT functionalities.

5. Turn on database publications in `supabase_realtime` for the following tables:

    - `chatrooms`

    - `documents`

    - `invites`

    - `messages`

6. Create Row Level Security policies for each of the database tables.

### Set Up Object Store

1. Create the following buckets in the object store.

    | Name | File Size Limit | Allowed MIME Types |
    | --- | --- | --- |
    | `attachments` | 5 MB | `image/jpeg`, `image/png`, `application/pdf`, `text/*` |
    | `knowledge-bases` | 5 MB | `image/jpeg`, `image/png`, `application/pdf`, `text/*` |

2. Create access control policies for both buckets. **4** policies should be created, one for each of `SELECT`, `INSERT`, `UPDATE`, and `DELETE` operations.

    - For `SELECT`, set **USING expression** as `(bucket_id = '<bucket_name>'::text)`.

    - For `INSERT`, set **WITH CHECK expression** as `(bucket_id = '<bucket_name'::text)`.

    - For `UPDATE`, set **USING expression** as `(bucket_id = '<bucket_name>'::text)` and leave **WITH CHECK expression** empty.

    - For `DELETE`, set **USING expression** as `(bucket_id = '<bucket_name>'::text)`.

### Email Services

The email service used for sending emails to GroupGPT users is [Resend](https://resend.com/home). See [here](https://supabase.com/docs/guides/auth/auth-smtp) for the steps to link Resend's SMTP server to the Supabase project.

The HTML template used for the confirmation email can be found [here](./confirmation-email.html).

## Deployment

The backend server was deployed as a Web Service on Render. See [here](https://render.com/docs/your-first-deploy) for the deployment steps.
