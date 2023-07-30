CREATE EXTENSION vector;

CREATE OR REPLACE FUNCTION generateBottyKey()
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
  length INTEGER := 11;
  chars TEXT := '-_0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz';
  key TEXT := '';
  randomIndex INTEGER;
BEGIN
  -- Generate the first character
  randomIndex := (random() * (length(chars) - 3)) + 2; -- Exclude "_" and "-" from the first character
  key := key || substr(chars, randomIndex, 1);

  -- Generate the rest of the characters
  FOR i IN 1..length - 2 LOOP
    randomIndex := random() * length(chars);
    key := key || substr(chars, randomIndex + 1, 1);
  END LOOP;

  -- Generate the last character
  randomIndex := (random() * (length(chars) - 3)) + 2; -- Exclude "_" and "-" from the last character
  key := key || substr(chars, randomIndex, 1);

  RETURN key;
END;
$$;

DROP TABLE IF EXISTS user_prompt;
CREATE TABLE user_prompt (
    prompt_id TEXT DEFAULT generateBottyKey() PRIMARY KEY,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_prompt_text TEXT NOT NULL,
    hashtags TEXT[] NULL,
    embedding vector(1536) NULL,
    metadata JSONB NULL
);

CREATE INDEX idx_user_prompt_metadata ON user_prompt USING gin(metadata);

-- Create an AFTER UPDATE trigger to set the 'updated' column
CREATE OR REPLACE FUNCTION update_user_prompt_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_prompt_trigger
AFTER UPDATE ON prompt
FOR EACH ROW
EXECUTE FUNCTION update_prompt_timestamp();

CREATE TABLE user_prompt_queue (
    id SERIAL PRIMARY KEY,
    prompt_id TEXT,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_processed BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 0,
    FOREIGN KEY (prompt_id) REFERENCES user_prompt(prompt_id)
);

CREATE INDEX idx_user_prompt_queue_priority
ON user_prompt_queue (is_processed, priority DESC, added_at ASC);

CREATE OR REPLACE FUNCTION get_next_user_prompt()
RETURNS SETOF user_prompt AS
$$
DECLARE
  next_prompt_id TEXT;
BEGIN
  SELECT prompt_id INTO next_prompt_id 
  FROM user_prompt_queue
  WHERE is_processed = FALSE
  ORDER BY priority DESC, added_at ASC
  LIMIT 1;

  RETURN QUERY SELECT * FROM user_prompt WHERE prompt_id = next_prompt_id;
END;
$$
LANGUAGE 'plpgsql';
