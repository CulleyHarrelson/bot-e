
-- Drop the 'training_data' table and its dependencies if they exist
DROP TABLE IF EXISTS training_data CASCADE;

-- Create the 'training_data' table with columns and constraints
-- training_data cannot be edited
CREATE TABLE training_data (
    training_data_id TEXT DEFAULT generateKey() PRIMARY KEY, -- Primary key generated by the function
    question TEXT NOT NULL, -- The users prompt - their request for advice
    answer TEXT NOT NULL, -- The users prompt - their request for advice
    question_embedding vector(1536) NULL -- embedding data from llm
);
