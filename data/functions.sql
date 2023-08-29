-- This is the data api

CREATE OR REPLACE FUNCTION next_question()
RETURNS SETOF question AS
$$
DECLARE
  next_question_id TEXT;
BEGIN
  SELECT question_id INTO next_question_id 
  FROM question
  WHERE answer IS NULL
  ORDER BY added_at ASC
  LIMIT 1;

  -- Return the corresponding row from 'question' where 'question_id' matches 'next_question_id'
  RETURN QUERY SELECT * FROM question WHERE question_id = next_question_id;
END;
$$ LANGUAGE plpgsql;

/*
get_proximal_question() notes:
The first subquery inside the UNION selects the row with the greatest distance
from the exclude_ids array, just as in the previous version of the function.
The second subquery selects the row with the greatest proximity to the
include_ids array.

By using UNION, the function will return a single row, which is either the row
with the greatest distance from the exclude_ids array or the row with the
greatest proximity to the include_ids array, depending on which one has the
higher value according to the <-> operator.
*/

-- unclear if this works?
CREATE OR REPLACE FUNCTION get_proximal_question(
    exclude_ids TEXT[],
    include_ids TEXT[]
) RETURNS SETOF question AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM question
    WHERE question_id = (
        SELECT question_id
        FROM question
        ORDER BY embedding <-> (SELECT embedding FROM question WHERE question_id = ANY(exclude_ids))
        LIMIT 1
    )
    UNION
    SELECT *
    FROM question
    WHERE question_id = (
        SELECT question_id
        FROM question
        ORDER BY embedding <-> (SELECT embedding FROM question WHERE question_id = ANY(include_ids))
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get the next question that does not have a embedding value.
-- this works as a queue for the embeddings api
CREATE OR REPLACE FUNCTION next_embedding()
RETURNS SETOF question AS
$$
DECLARE
  next_question_id TEXT;
BEGIN
  SELECT question_id INTO next_question_id 
  FROM question
  WHERE embedding IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'question' where 'question_id' matches 'next_question_id'
  RETURN QUERY SELECT * FROM question WHERE question_id = next_question_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get the next question that does not have a moderation value.
-- this works as a queue for the moderation api
CREATE OR REPLACE FUNCTION next_moderation()
RETURNS SETOF question AS
$$
DECLARE
  next_question_id TEXT;
BEGIN
  SELECT question_id INTO next_question_id 
  FROM question
  WHERE moderation IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'question' where 'question_id' matches 'next_question_id'
  RETURN QUERY SELECT * FROM question WHERE question_id = next_question_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION new_question(prompt_value TEXT)
RETURNS question AS $$
DECLARE
    inserted_question question;
BEGIN
     IF LENGTH(TRIM(prompt_value)) = 0 THEN
        RAISE EXCEPTION 'question.question cannot be a zero-length string';
    END IF;
    -- Insert the record into the 'question' table
    INSERT INTO question (question) VALUES (prompt_value) RETURNING * INTO inserted_question;

    RETURN inserted_question;
END;
$$ LANGUAGE plpgsql;

-- Function to get the next question that does not have an analysis value.
-- this works as a queue for the conversation api to get the analysis dictionary
CREATE OR REPLACE FUNCTION next_analysis()
RETURNS SETOF question AS
$$
DECLARE
  next_question_id TEXT;
BEGIN
  SELECT question_id INTO next_question_id 
  FROM question
  WHERE analysis IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'question' where 'question_id' matches 'next_question_id'
  RETURN QUERY SELECT * FROM question WHERE question_id = next_question_id;
END;
$$ LANGUAGE plpgsql;

 --select question_id from find_similar('Y7HXnornSAh')

-- return similar questions 
CREATE OR REPLACE FUNCTION similar(question_id_in TEXT, row_limit INT DEFAULT 10)
RETURNS SETOF question
AS $$
DECLARE
    target_embedding vector(1536);
BEGIN
    -- Get the target embedding for the given question_id
    SELECT embedding INTO target_embedding
    FROM question
    WHERE question_id = question_id_in;

    IF target_embedding IS NULL THEN
        RAISE EXCEPTION 'No record found for the given question_id';
    END IF;

    -- Perform the proximity search using pg_similarity extension
    RETURN QUERY
    SELECT a.*
    FROM question a
    WHERE a.question_id <> question_id_in  -- Exclude the same question_id
    ORDER BY a.embedding <-> target_embedding  -- Order by proximity to the target embedding
    LIMIT row_limit;  -- Limit the results to the specified row limit
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION search(search_term TEXT, limit_rows INT DEFAULT 10)
RETURNS SETOF question AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM question
    WHERE search_vector @@ plainto_tsquery(search_term)
    LIMIT limit_rows;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_similar(aid TEXT) RETURNS TABLE(question TEXT, answer TEXT) AS $$
DECLARE
    question_embedding vector(1536);
    similarity_threshold FLOAT := 0.9; -- Adjust the threshold as needed
BEGIN
    -- Fetch the question's embedding
    SELECT embedding INTO question_embedding FROM question WHERE question_id = aid;

    -- Ensure the question's embedding is not null
    IF question_embedding IS NULL THEN
        RAISE EXCEPTION 'Embedding for the given question_id is NULL';
    END IF;

    -- Find similar training_data entries using pgvector's knn cosine similarity
    RETURN QUERY
    SELECT T.question, T.answer
    FROM training_data AS T
    WHERE T.question_embedding <-> question_embedding < similarity_threshold
    ORDER BY T.question_embedding <-> question_embedding
    LIMIT 1;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN;
END;
$$ LANGUAGE plpgsql;

-- returns bot-e version to tag each question row
CREATE OR REPLACE FUNCTION getVersion() RETURNS text AS $$
BEGIN
    RETURN '0.1';
END;
$$ LANGUAGE plpgsql;

