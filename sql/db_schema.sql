-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.attachments (
  attachment_id uuid NOT NULL DEFAULT gen_random_uuid(),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  message_id uuid NOT NULL,
  filename text NOT NULL,
  mime_type text NOT NULL,
  CONSTRAINT attachments_pkey PRIMARY KEY (attachment_id),
  CONSTRAINT message_attachments_message_id_fkey FOREIGN KEY (message_id) REFERENCES public.messages(message_id)
);
CREATE TABLE public.chatrooms (
  chatroom_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  name text NOT NULL CHECK (length(name) >= 2 AND length(name) <= 64),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  creator_id uuid,
  CONSTRAINT chatrooms_pkey PRIMARY KEY (chatroom_id),
  CONSTRAINT chatrooms_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.chats (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  message text,
  username text,
  topic text,
  CONSTRAINT chats_pkey PRIMARY KEY (id)
);
CREATE TABLE public.chunks (
  chunk_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  document_id uuid NOT NULL,
  content text NOT NULL,
  embedding USER-DEFINED NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  chunk_index integer NOT NULL CHECK (chunk_index >= 0),
  content_tsv tsvector DEFAULT to_tsvector('english'::regconfig, content),
  CONSTRAINT chunks_pkey PRIMARY KEY (chunk_id),
  CONSTRAINT chunks_document_id_fkey FOREIGN KEY (document_id) REFERENCES public.documents(document_id)
);
CREATE TABLE public.document_summaries (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  summary text,
  filepath text,
  CONSTRAINT document_summaries_pkey PRIMARY KEY (id)
);
CREATE TABLE public.document_vectors (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  embedding USER-DEFINED,
  text text,
  topic text,
  CONSTRAINT document_vectors_pkey PRIMARY KEY (id)
);
CREATE TABLE public.documents (
  document_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  uploader_id uuid,
  chatroom_id uuid NOT NULL,
  filename text NOT NULL,
  uploaded_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT documents_pkey PRIMARY KEY (document_id),
  CONSTRAINT documents_chatroom_id_fkey FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms(chatroom_id),
  CONSTRAINT documents_uploader_id_fkey FOREIGN KEY (uploader_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.invites (
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  sender_id uuid,
  recipient_id uuid NOT NULL,
  chatroom_id uuid NOT NULL,
  status USER-DEFINED NOT NULL DEFAULT 'PENDING'::invite_status,
  invite_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  CONSTRAINT invites_pkey PRIMARY KEY (invite_id),
  CONSTRAINT invites_chatroom_id_fkey FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms(chatroom_id),
  CONSTRAINT invites_recipient_id_fkey FOREIGN KEY (recipient_id) REFERENCES public.users(user_id),
  CONSTRAINT invites_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.members (
  user_id uuid NOT NULL,
  chatroom_id uuid NOT NULL,
  joined_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT members_pkey PRIMARY KEY (user_id, chatroom_id),
  CONSTRAINT members_chatroom_id_fkey FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms(chatroom_id),
  CONSTRAINT members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.messages (
  message_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  sender_id uuid,
  chatroom_id uuid NOT NULL,
  sent_at timestamp with time zone NOT NULL DEFAULT now(),
  content text NOT NULL,
  has_attachments boolean NOT NULL DEFAULT false CHECK (has_attachments = ANY (ARRAY[true, false])),
  CONSTRAINT messages_pkey PRIMARY KEY (message_id),
  CONSTRAINT messages_chatroom_id_fkey FOREIGN KEY (chatroom_id) REFERENCES public.chatrooms(chatroom_id),
  CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(user_id)
);
CREATE TABLE public.user_topic (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  topic text,
  joined boolean,
  username text,
  CONSTRAINT user_topic_pkey PRIMARY KEY (id)
);
CREATE TABLE public.users (
  user_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
  auth_id uuid DEFAULT auth.uid(),
  username text NOT NULL UNIQUE CHECK (length(username) >= 2 AND length(username) <= 20),
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (user_id),
  CONSTRAINT users_auth_id_fkey FOREIGN KEY (auth_id) REFERENCES auth.users(id)
);
