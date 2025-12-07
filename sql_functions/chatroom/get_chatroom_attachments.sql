DROP FUNCTION IF EXISTS get_chatroom_attachments(UUID);

CREATE OR REPLACE FUNCTION get_chatroom_attachments(p_chatroom_id UUID)
RETURNS TABLE (
  attachment_id UUID
)
LANGUAGE sql
AS $$
  SELECT a.attachment_id
  FROM chatrooms AS c
  JOIN messages AS m ON c.chatroom_id = m.chatroom_id
  JOIN attachments AS a ON m.message_id = a.message_id
  WHERE c.chatroom_id = p_chatroom_id
$$;
