DROP FUNCTION IF EXISTS get_chatroom_documents(UUID);

CREATE OR REPLACE FUNCTION get_chatroom_documents(p_chatroom_id UUID)
RETURNS TABLE(
    document_id UUID,
    filename TEXT,
    uploader_username TEXT,
    uploaded_at TIMESTAMPTZ
)
LANGUAGE sql
AS $$
    SELECT 
        d.document_id,
        d.filename,
        u.username as uploader_username,
        d.uploaded_at
    FROM documents d
    LEFT JOIN users u ON d.uploader_id = u.user_id
    WHERE d.chatroom_id = p_chatroom_id
    ORDER BY d.uploaded_at DESC;
$$;
