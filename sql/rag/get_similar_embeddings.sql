DROP FUNCTION IF EXISTS get_similar_embeddings(UUID, VECTOR(1536), INT);

CREATE OR REPLACE FUNCTION get_similar_embeddings(
    p_chatroom_id UUID,
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE(
    chunk_id UUID,
    filename TEXT,
    content TEXT,
    distance FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.chunk_id,
        d.filename,
        c.content,
        (c.embedding <=> query_embedding) AS distance
    FROM chunks AS c
    JOIN documents AS d ON c.document_id = d.document_id
    WHERE d.chatroom_id = p_chatroom_id
    ORDER BY distance ASC       
    LIMIT match_count;
END;
$$;
