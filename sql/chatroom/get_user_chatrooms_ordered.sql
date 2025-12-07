DROP FUNCTION IF EXISTS get_user_chatrooms_ordered(UUID);

CREATE OR REPLACE FUNCTION get_user_chatrooms_ordered(p_user_id UUID)
RETURNS TABLE (
  chatroom_id UUID,
  creator_id UUID,
  name TEXT
)
LANGUAGE sql
AS $$
  SELECT
    c.chatroom_id,
    c.creator_id,
    c.name
  FROM members AS mem
  JOIN chatrooms AS c ON mem.chatroom_id = c.chatroom_id
  WHERE mem.user_id = p_user_id
  ORDER BY mem.joined_at DESC
$$;
