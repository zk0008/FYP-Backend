# FYP-Backend

## Local Development

First, update the following environment variables in `.env`:
 
```bash
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
OPENAI_API_KEY
```

Then, install the dependencies:

```bash
pip install -r requirements.txt
```

Then, run the server locally:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
