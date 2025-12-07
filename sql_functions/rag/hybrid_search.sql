DROP FUNCTION IF EXISTS hybrid_search(UUID, VECTOR(1536), TEXT, INT);

CREATE OR REPLACE FUNCTION hybrid_search(
    p_chatroom_id UUID,
    query_embedding VECTOR(1536),
    search_query TEXT,
    match_count INT DEFAULT 5
)
RETURNS TABLE(
    filename TEXT,
    content TEXT,
    rrf_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    -- Get similar chunks using vector search (cosine distance)
    WITH vector_results AS (
        SELECT
            v.chunk_id,
            v.filename,
            v.content,
            ROW_NUMBER() OVER (ORDER BY v.distance ASC) AS rank
        FROM get_similar_embeddings(p_chatroom_id, query_embedding, match_count * 3) v
    ),
    -- Get similar chunks using full-text search (string matching)
    text_results AS (
        SELECT
            t.chunk_id,
            t.filename,
            t.content,
            ROW_NUMBER() OVER (ORDER BY t.rank_score DESC) AS rank
        FROM get_similar_text_chunks(p_chatroom_id, search_query, match_count * 3) t
    ),
    -- Combine results from both searches using reciprocal rank fusion (RRF)
    rrf_combined AS (
        SELECT
            COALESCE(v.chunk_id, t.chunk_id) AS chunk_id,
            COALESCE(v.filename, t.filename) AS filename,
            COALESCE(v.content, t.content) AS content,
            (COALESCE(1.0 / (60 + v.rank), 0) + COALESCE(1.0 / (60 + t.rank), 0))::FLOAT AS rrf_score
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.chunk_id = t.chunk_id
    )
    SELECT 
        rc.filename,
        rc.content,
        rc.rrf_score
    FROM rrf_combined AS rc
    WHERE rc.rrf_score > 0
    ORDER BY rc.rrf_score DESC
    LIMIT match_count;
END;
$$;
