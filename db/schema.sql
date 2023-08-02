-- Check if the 'vector' extension exists, and create it if not
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS aws_lambda CASCADE;
CREATE EXTENSION pg_cron;

-- Function to generate a unique key for the 'prompt_id' column in 'user_prompt' table
CREATE OR REPLACE FUNCTION generateBottyKey()
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

    -- Check if the generated key already exists in the 'user_prompt' table
    SELECT EXISTS (SELECT 1 FROM user_prompt WHERE prompt_id = key) INTO keyExists;

    EXIT WHEN NOT keyExists;
  END LOOP;

  RETURN key;
END;
$$;

-- Drop the 'user_prompt' table and its dependencies if they exist
DROP TABLE IF EXISTS user_prompt CASCADE;

-- Create the 'user_prompt' table with columns and constraints
CREATE TABLE user_prompt (
    prompt_id TEXT DEFAULT generateBottyKey() PRIMARY KEY, -- Primary key generated by the function
    prompt TEXT NOT NULL, -- The users prompt - their request for advice
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is updated
    hashtags TEXT[] NULL, -- Array of hashtags (nullable)
    embedding vector(1536) NULL, -- Vector data type with 1536 dimensions (nullable)
    metadata JSONB NULL -- JSONB data type (nullable)
);

-- Create an index on the 'metadata' column of 'user_prompt' table for faster searches
CREATE INDEX idx_user_prompt_metadata ON user_prompt USING gin(metadata);

-- Function to set the 'updated_at' column to the current timestamp after an update on 'user_prompt'
CREATE OR REPLACE FUNCTION update_user_prompt_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := CURRENT_TIMESTAMP; -- Set 'updated_at' column to current timestamp
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop the existing trigger 'update_user_prompt_trigger' if it exists
DROP TRIGGER IF EXISTS update_user_prompt_trigger ON user_prompt;

-- Create a new trigger 'update_user_prompt_trigger' after update on 'user_prompt'
CREATE TRIGGER update_user_prompt_trigger
AFTER UPDATE ON user_prompt
FOR EACH ROW
EXECUTE FUNCTION update_user_prompt_timestamp();

-- Drop the 'response_queue' table and its dependencies if they exist
DROP TABLE IF EXISTS response_queue CASCADE;

-- Create the 'response_queue' table with columns and constraints
CREATE TABLE response (
    id SERIAL PRIMARY KEY, -- Auto-incrementing primary key
    prompt_id TEXT, -- Foreign key referencing 'prompt_id' column in 'user_prompt'
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    is_processed BOOLEAN DEFAULT FALSE, -- Flag indicating whether the record is processed or not
    priority INTEGER DEFAULT 0, -- Priority value (default is 0)
    FOREIGN KEY (prompt_id) REFERENCES user_prompt(prompt_id) ON DELETE CASCADE -- Foreign key constraint
);

-- Create an index on 'response_queue' table to optimize queries involving 'is_processed' and 'priority'
CREATE INDEX idx_user_prompt_queue_priority
ON response_queue (is_processed, priority DESC, added_at ASC);

-- Create an index on 'response_queue' table to optimize queries involving 'prompt_id'
CREATE INDEX idx_user_prompt_queue_prompt
ON response_queue (prompt_id);

-- Function to get the next prompt from the 'response_queue' table
CREATE OR REPLACE FUNCTION get_next_prompt()
RETURNS SETOF user_prompt AS
$$
DECLARE
  next_prompt_id TEXT;
BEGIN
  -- Select the 'prompt_id' from 'response_queue' where 'is_processed' is false,
  -- order by 'priority' descending and 'added_at' ascending, and limit to 1 row
  SELECT prompt_id INTO next_prompt_id 
  FROM response_queue
  WHERE is_processed = FALSE
  ORDER BY priority DESC, added_at ASC
  LIMIT 1;

  -- Return the corresponding row from 'user_prompt' where 'prompt_id' matches 'next_prompt_id'
  RETURN QUERY SELECT * FROM user_prompt WHERE prompt_id = next_prompt_id;
END;
$$
LANGUAGE 'plpgsql';

-- Function to insert a record into the 'response_queue' table after an INSERT on 'user_prompt'
CREATE OR REPLACE FUNCTION insert_into_response_queue()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert a new record into the 'response_queue' table with the new 'prompt_id'
    INSERT INTO response_queue (prompt_id)
    VALUES (NEW.prompt_id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- Drop the existing trigger 'insert_into_response_queue_trigger' on 'user_prompt' if it exists
DROP TRIGGER IF EXISTS insert_into_response_queue_trigger ON user_prompt;

-- Create a new trigger 'insert_into_response_queue_trigger' after insert on 'user_prompt'
CREATE TRIGGER insert_into_response_queue_trigger
AFTER INSERT ON user_prompt
FOR EACH ROW
EXECUTE FUNCTION insert_into_response_queue();


-- Create the 'response_queue' table with columns and constraints
CREATE TABLE response (
    id SERIAL PRIMARY KEY, -- Auto-incrementing primary key
    prompt_id TEXT, -- Foreign key referencing 'prompt_id' column in 'user_prompt'
    added_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Timestamp when the record is added
    analysis JSONB NOT NULL, -- model response to request to analyze text
    message JSONB NOT NULL, -- generated system prompt along with user prompt
    response JSONB, -- model response
    FOREIGN KEY (prompt_id) REFERENCES user_prompt(prompt_id) ON DELETE CASCADE -- Foreign key constraint
);

CREATE INDEX idx_user_response_assistant ON response USING gin(assistant);

