CREATE EXTENSION IF NOT EXISTS vector;


-- Function to generate a unique key for the 'question_id' column in 'question' table
-- Inspired by youtube video id
CREATE OR REPLACE FUNCTION generateKey()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  length INTEGER := 11;
  chars TEXT := '-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  key TEXT := '';
  randomIndex INTEGER;
  keyExists BOOLEAN;
BEGIN
  LOOP
    -- Generate the first character of the key, excluding "_" and "-" from the first position
    randomIndex := (random() * (length(chars) - 3)) + 2;
    key := substr(chars, randomIndex, 1);

    -- Generate the rest of the characters for the key
    FOR i IN 1..length - 2 LOOP
      randomIndex := random() * length(chars);
      key := key || substr(chars, randomIndex + 1, 1);
    END LOOP;

    -- Generate the last character of the key, excluding "_" and "-" from the last position
    randomIndex := (random() * (length(chars) - 3)) + 2;
    key := key || substr(chars, randomIndex, 1);

    -- Check if the generated key already exists in the 'question' table
    SELECT EXISTS (SELECT 1 FROM question WHERE question_id = key) INTO keyExists;

    EXIT WHEN NOT keyExists;
  END LOOP;

  RETURN key;
END;
$$;

-- Drop the 'question' table and its dependencies if they exist
DROP TABLE IF EXISTS question CASCADE;

-- Create the 'question' table with columns and constraints
-- questions cannot be edited
CREATE TABLE question (
    question_id TEXT DEFAULT generateKey() PRIMARY KEY, -- Primary key generated by the function
    question TEXT NOT NULL, -- the request for advice
    answer TEXT NULL, 
    title TEXT NULL, 
    description TEXT NULL, 
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    modified_at TIMESTAMP WITH TIME ZONE,
    hashtags TEXT[] NULL, -- Array of hashtags (nullable)
    embedding vector(1536) NULL, -- embedding data 
    moderation JSONB NULL, 
    media JSONB NULL, -- list of related books, movies etc
    system_prompt TEXT NULL,
    search_vector tsvector NULL,
    image_url TEXT NULL
);

-- CREATE INDEX idx_question_moderation ON question USING gin(moderation);
CREATE INDEX idx_question_hashtags ON question USING gin (hashtags);
CREATE INDEX idx_question_search_vector ON question USING gin(search_vector);
--CREATE INDEX idx_question_embedding ON question USING gin(embedding);

CREATE INDEX idx_question_added_at ON question (added_at);

CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector(coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector(coalesce(NEW.question, '')), 'B') ||
        setweight(to_tsvector(coalesce(array_to_string(NEW.hashtags, ' '), '')), 'C') ||
        setweight(to_tsvector(coalesce(NEW.answer, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_search_vector
BEFORE INSERT OR UPDATE ON question
FOR EACH ROW
EXECUTE FUNCTION update_search_vector();

-- Create a function to check the length of the question_id and raise an exception if it's not 11 characters
CREATE OR REPLACE FUNCTION check_question_id_length()
RETURNS TRIGGER AS $$
BEGIN
    IF LENGTH(NEW.question_id) <> 11 THEN
        RAISE EXCEPTION 'question_id must be exactly 11 characters';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger that uses the check_question_id_length function before insert
CREATE TRIGGER check_question_id_trigger
BEFORE INSERT ON question
FOR EACH ROW
EXECUTE FUNCTION check_question_id_length();


CREATE OR REPLACE FUNCTION notify_new_question()
RETURNS TRIGGER AS $$
BEGIN
    -- bote.py is listening
    NOTIFY new_question;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER new_question_trigger
AFTER INSERT ON question
FOR EACH ROW
EXECUTE FUNCTION notify_new_question();

CREATE TRIGGER update_modified_at_trigger
BEFORE UPDATE ON question
FOR EACH ROW
EXECUTE FUNCTION update_modified_at();

DROP TABLE IF EXISTS question_vote CASCADE;

-- this table tracks up and down votes.  It is also 
-- referenced in the proximal_question function
CREATE TABLE question_vote (
    question_id TEXT NOT NULL,
    session_id TEXT NOT NULL, 
    up_vote BOOLEAN NOT NULL DEFAULT TRUE,
    vote_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (session_id, vote_at)
);

CREATE INDEX idx_question_id ON question_vote (question_id);
CREATE INDEX idx_vote_at ON question_vote (vote_at);

