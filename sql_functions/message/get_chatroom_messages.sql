DROP FUNCTION IF EXISTS get_chatroom_messages(UUID);

CREATE OR REPLACE FUNCTION get_chatroom_messages(p_chatroom_id UUID)
RETURNS TABLE (
  message_id UUID,
  username TEXT,
  content TEXT,
  sent_at TIMESTAMPTZ,
  attachments JSONB
)
LANGUAGE sql
AS $$
  SELECT
    m.message_id,
    u.username,
    m.content,
    m.sent_at,
    COALESCE(
      JSONB_AGG(
        JSONB_BUILD_OBJECT(
          'attachment_id', a.attachment_id,
          'mime_type', a.mime_type,
          'filename', a.filename
        ) ORDER BY a.filename
      ) FILTER (WHERE a.attachment_id IS NOT NULL),
      '[]'::JSONB
    ) as attachments
  FROM messages AS m
  LEFT JOIN users AS u ON m.sender_id = u.user_id
  LEFT JOIN attachments AS a ON m.message_id = a.message_id
  WHERE m.chatroom_id = p_chatroom_id
    AND m.sent_at < CURRENT_TIMESTAMP
  GROUP BY m.message_id, u.username, m.content, m.sent_at
  ORDER BY sent_at ASC;
$$;
