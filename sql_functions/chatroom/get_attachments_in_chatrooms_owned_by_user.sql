DROP FUNCTION IF EXISTS get_attachments_in_chatrooms_owned_by_user(UUID);

CREATE OR REPLACE FUNCTION get_attachments_in_chatrooms_owned_by_user(p_user_id UUID)
RETURNS TABLE (
  chatroom_id UUID,
  attachment_id UUID
)
LANGUAGE sql
AS $$
  SELECT c.chatroom_id, a.attachment_id
  FROM chatrooms AS c
  JOIN messages AS m ON c.chatroom_id = m.chatroom_id
  JOIN attachments AS a ON m.message_id = a.message_id
  WHERE c.creator_id = p_user_id
$$;
