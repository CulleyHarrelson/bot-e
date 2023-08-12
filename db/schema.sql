-- Check if the 'vector' extension exists, and create it if not
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;
--CREATE EXTENSION pg_cron;

DROP TYPE ask_status CASCADE;
CREATE TYPE ask_status AS ENUM ('new', 'noncompliant', 'complete', 'deleted');

-- Function to generate a unique key for the 'ask_id' column in 'ask' table
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

    -- Check if the generated key already exists in the 'ask' table
    SELECT EXISTS (SELECT 1 FROM ask WHERE ask_id = key) INTO keyExists;

    EXIT WHEN NOT keyExists;
  END LOOP;

  RETURN key;
END;
$$;



-- Drop the 'ask' table and its dependencies if they exist
DROP TABLE IF EXISTS ask CASCADE;

-- Create the 'ask' table with columns and constraints
-- Asks cannot be edited
CREATE TABLE ask (
    ask_id TEXT DEFAULT generateKey() PRIMARY KEY, -- Primary key generated by the function
    prompt TEXT NOT NULL, -- The users prompt - their request for advice
    title TEXT NULL, 
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    ask_status ask_status NOT NULL DEFAULT 'new',
    hashtags TEXT[] NULL, -- Array of hashtags (nullable)
    embedding vector(1536) NULL, -- embedding data from llm
    moderation JSONB NULL, -- response to request for meta analysis on question
    analysis JSONB NULL, -- response to request for meta analysis on question
    system_prompt TEXT NULL, -- response to request for meta analysis on question
    response TEXT NULL, -- response to request for meta analysis on question
    search_vector tsvector NULL
);

CREATE INDEX idx_ask_moderation ON ask USING gin(moderation);
CREATE INDEX idx_ask_analysis ON ask USING gin(analysis);
CREATE INDEX idx_ask_hashtags ON ask USING gin (hashtags);
CREATE INDEX idx_search_vector ON ask USING gin(search_vector);
--CREATE INDEX idx_ask_embedding ON ask USING gin(embedding);

-- Create an index on ask.added_at
CREATE INDEX idx_ask_added_at ON ask (added_at);

CREATE OR REPLACE FUNCTION update_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := 
        setweight(to_tsvector(coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector(coalesce(NEW.prompt, '')), 'B') ||
        setweight(to_tsvector(coalesce(array_to_string(NEW.hashtags, ' '), '')), 'C') ||
        setweight(to_tsvector(coalesce(NEW.response, '')), 'D');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_search_vector
BEFORE INSERT OR UPDATE ON ask
FOR EACH ROW
EXECUTE FUNCTION update_search_vector();

