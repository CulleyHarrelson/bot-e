-- This is the data api

-- Function to get the next ask from the 'response_queue' table
CREATE OR REPLACE FUNCTION next_ask()
RETURNS SETOF ask AS
$$
DECLARE
  next_ask_id TEXT;
BEGIN
  -- Select the 'ask_id' from 'response_queue' where 'is_processed' is false,
  -- order by 'priority' descending and 'added_at' ascending, and limit to 1 row
  SELECT ask_id INTO next_ask_id 
  FROM response_queue
  WHERE is_processed = FALSE
  ORDER BY priority DESC, added_at ASC
  LIMIT 1;

  -- Return the corresponding row from 'ask' where 'ask_id' matches 'next_ask_id'
  RETURN QUERY SELECT * FROM ask WHERE ask_id = next_ask_id;
END;
$$ LANGUAGE plpgsql;

/*
get_proximal_ask() notes:
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
CREATE OR REPLACE FUNCTION get_proximal_ask(
    exclude_ids TEXT[],
    include_ids TEXT[]
) RETURNS SETOF ask AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM ask
    WHERE ask_id = (
        SELECT ask_id
        FROM ask
        ORDER BY embedding <-> (SELECT embedding FROM ask WHERE ask_id = ANY(exclude_ids))
        LIMIT 1
    )
    UNION
    SELECT *
    FROM ask
    WHERE ask_id = (
        SELECT ask_id
        FROM ask
        ORDER BY embedding <-> (SELECT embedding FROM ask WHERE ask_id = ANY(include_ids))
        LIMIT 1
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get the next ask that does not have a embedding value.
-- this works as a queue for the embeddings api
CREATE OR REPLACE FUNCTION next_embedding()
RETURNS SETOF ask AS
$$
DECLARE
  next_ask_id TEXT;
BEGIN
  -- Select the 'ask_id' from 'response_queue' where 'is_processed' is false,
  -- order by 'priority' descending and 'added_at' ascending, and limit to 1 row
  SELECT ask_id INTO next_ask_id 
  FROM ask
  WHERE embedding IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'ask' where 'ask_id' matches 'next_ask_id'
  RETURN QUERY SELECT * FROM ask WHERE ask_id = next_ask_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get the next ask that does not have a moderation value.
-- this works as a queue for the moderation api
CREATE OR REPLACE FUNCTION next_moderation()
RETURNS SETOF ask AS
$$
DECLARE
  next_ask_id TEXT;
BEGIN
  -- Select the 'ask_id' from 'response_queue' where 'is_processed' is false,
  -- order by 'priority' descending and 'added_at' ascending, and limit to 1 row
  SELECT ask_id INTO next_ask_id 
  FROM ask
  WHERE moderation IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'ask' where 'ask_id' matches 'next_ask_id'
  RETURN QUERY SELECT * FROM ask WHERE ask_id = next_ask_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION new_ask(prompt_value TEXT)
RETURNS ask AS $$
DECLARE
    inserted_ask ask;
BEGIN
     IF LENGTH(TRIM(prompt_value)) = 0 THEN
        RAISE EXCEPTION 'ask.prompt cannot be a zero-length string';
    END IF;
    -- Insert the record into the 'ask' table
    INSERT INTO ask (prompt) VALUES (prompt_value) RETURNING * INTO inserted_ask;

    RETURN inserted_ask;
END;
$$ LANGUAGE plpgsql;

-- Function to get the next ask that does not have an analysis value.
-- this works as a queue for the conversation api to get the analysis dictionary
CREATE OR REPLACE FUNCTION next_analysis()
RETURNS SETOF ask AS
$$
DECLARE
  next_ask_id TEXT;
BEGIN
  SELECT ask_id INTO next_ask_id 
  FROM ask
  WHERE analysis IS NULL
  ORDER BY added_at
  LIMIT 1;

  -- Return the corresponding row from 'ask' where 'ask_id' matches 'next_ask_id'
  RETURN QUERY SELECT * FROM ask WHERE ask_id = next_ask_id;
END;
$$ LANGUAGE plpgsql;

 --select ask_id from find_similar('Y7HXnornSAh')

-- return similar questions 
CREATE OR REPLACE FUNCTION similar(ask_id_in TEXT, row_limit INT DEFAULT 10)
RETURNS SETOF ask
AS $$
DECLARE
    target_embedding vector(1536);
BEGIN
    -- Get the target embedding for the given ask_id
    SELECT embedding INTO target_embedding
    FROM ask
    WHERE ask_id = ask_id_in;

    IF target_embedding IS NULL THEN
        RAISE EXCEPTION 'No record found for the given ask_id';
    END IF;

    -- Perform the proximity search using pg_similarity extension
    RETURN QUERY
    SELECT a.*
    FROM ask a
    WHERE a.ask_id <> ask_id_in  -- Exclude the same ask_id
    ORDER BY a.embedding <-> target_embedding  -- Order by proximity to the target embedding
    LIMIT row_limit;  -- Limit the results to the specified row limit
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION search(search_term TEXT, limit_rows INT DEFAULT 10)
RETURNS SETOF ask AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM ask
    WHERE search_vector @@ plainto_tsquery(search_term)
    LIMIT limit_rows;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_similar(aid TEXT) RETURNS TABLE(question TEXT, answer TEXT) AS $$
DECLARE
    ask_embedding vector(1536);
    similarity_threshold FLOAT := 0.9; -- Adjust the threshold as needed
BEGIN
    -- Fetch the ask's embedding
    SELECT embedding INTO ask_embedding FROM ask WHERE ask_id = aid;

    -- Ensure the ask's embedding is not null
    IF ask_embedding IS NULL THEN
        RAISE EXCEPTION 'Embedding for the given ask_id is NULL';
    END IF;

    -- Find similar training_data entries using pgvector's knn cosine similarity
    RETURN QUERY
    SELECT T.question, T.answer
    FROM training_data AS T
    WHERE T.question_embedding <-> ask_embedding < similarity_threshold
    ORDER BY T.question_embedding <-> ask_embedding
    LIMIT 1;

EXCEPTION
    WHEN NO_DATA_FOUND THEN
        RETURN;
END;
$$ LANGUAGE plpgsql;

-- returns bot-e version to tag each ask row
CREATE OR REPLACE FUNCTION getVersion() RETURNS text AS $$
BEGIN
    RETURN '0.1';
END;
$$ LANGUAGE plpgsql;

