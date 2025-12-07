DROP FUNCTION IF EXISTS get_user_pending_invites(UUID);

CREATE OR REPLACE FUNCTION get_user_pending_invites(p_user_id UUID)
RETURNS TABLE (
  invite_id UUID,
  sender_username TEXT,
  chatroom_id UUID,
  chatroom_name TEXT,
  status TEXT,
  created_at TIMESTAMPTZ
)
LANGUAGE sql
AS $$
  SELECT
    i.invite_id,
    u.username AS sender_username,
    i.chatroom_id,
    c.name AS chatroom_name,
    i.status,
    i.created_at
  FROM invites AS i
  LEFT JOIN users AS u ON i.sender_id = u.user_id
  JOIN chatrooms AS c ON i.chatroom_id = c.chatroom_id
  WHERE i.recipient_id = p_user_id
    AND i.status = 'PENDING'
  ORDER BY created_at ASC;
$$;
