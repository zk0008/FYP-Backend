DROP FUNCTION IF EXISTS get_similar_text_chunks(UUID, TEXT, INT);

CREATE OR REPLACE FUNCTION get_similar_text_chunks(
    p_chatroom_id UUID, 
    search_query TEXT, 
    match_count INT DEFAULT 5
)
RETURNS TABLE(
    chunk_id UUID,
    filename TEXT,
    content TEXT,
    rank_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.chunk_id,
        d.filename, 
        c.content, 
        ts_rank_cd(c.content_tsv, plainto_tsquery('english', search_query))::FLOAT AS rank_score
    FROM chunks AS c
    JOIN documents AS d ON c.document_id = d.document_id
    WHERE d.chatroom_id = p_chatroom_id
      AND c.content_tsv @@ plainto_tsquery('english', search_query)
    ORDER BY rank_score DESC
    LIMIT match_count;
END;
$$;
