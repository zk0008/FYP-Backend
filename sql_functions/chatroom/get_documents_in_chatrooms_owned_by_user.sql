DROP FUNCTION IF EXISTS get_documents_in_chatrooms_owned_by_user(UUID);

CREATE OR REPLACE FUNCTION get_documents_in_chatrooms_owned_by_user(p_user_id UUID)
RETURNS TABLE (
  chatroom_id UUID,
  document_id UUID
)
LANGUAGE sql
AS $$
  SELECT c.chatroom_id, d.document_id
  FROM chatrooms AS c
  JOIN documents AS d ON c.chatroom_id = d.chatroom_id
  WHERE c.creator_id = p_user_id
$$;
