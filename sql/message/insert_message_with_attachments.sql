DROP FUNCTION IF EXISTS insert_message_with_attachments(UUID, UUID, TEXT, JSONB);

CREATE OR REPLACE FUNCTION insert_message_with_attachments(
  p_sender_id UUID,
  p_chatroom_id UUID,
  p_content TEXT,
  p_attachments_data JSONB  -- Should minimally be an empty list if there are no attachments
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
  new_message_id UUID;
  result JSONB;
BEGIN
  -- Insert message record
  INSERT INTO messages (sender_id, chatroom_id, content, has_attachments)
  VALUES (p_sender_id, p_chatroom_id, p_content, JSONB_ARRAY_LENGTH(p_attachments_data) > 0)
  RETURNING message_id INTO new_message_id;

  -- Insert attachment records if any
  IF p_attachments_data IS NOT NULL AND JSONB_ARRAY_LENGTH(p_attachments_data) > 0 THEN
    INSERT INTO attachments (message_id, filename, mime_type)
    SELECT
      new_message_id,
      (att->>'p_filename')::text,
      (att->>'p_mime_type')::text
    FROM JSONB_ARRAY_ELEMENTS(p_attachments_data) AS att;
  END IF;

  -- Return complete message with attachments
  SELECT JSONB_BUILD_OBJECT(
    'message_record', ROW_TO_JSON(m),  -- Needs to be 'message_record' otherwise response has the structure as an error message
    'attachments', COALESCE(ARRAY_AGG(ROW_TO_JSON(a)) FILTER (WHERE a.attachment_id IS NOT NULL), '{}')
  ) INTO result
  FROM messages AS m
  LEFT JOIN attachments AS a ON m.message_id = a.message_id
  WHERE m.message_id = new_message_id
  GROUP BY m.message_id;

  RETURN result;
END;
$$;
