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

