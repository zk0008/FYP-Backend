DROP FUNCTION IF EXISTS get_similar_embeddings_legacy(VECTOR(1536), TEXT, INT);
 
CREATE OR REPLACE FUNCTION get_similar_embeddings_legacy(query_embedding VECTOR(1536), query_topic TEXT, match_count INT DEFAULT 5)
RETURNS TABLE(id INT, text TEXT, similarity FLOAT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT e.id::INTEGER, e.text, (e.embedding <=> query_embedding) AS similarity
  FROM document_vectors AS e
  WHERE e.topic = query_topic
  ORDER BY e.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
