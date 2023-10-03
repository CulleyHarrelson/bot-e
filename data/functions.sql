
CREATE OR REPLACE FUNCTION proximal_question(question_id_in TEXT, session_id_in TEXT, similar_in BOOLEAN DEFAULT true)
RETURNS SETOF question
AS $$
DECLARE
    target_embedding vector(1536);
    vote_count INT;
BEGIN
    SELECT embedding INTO target_embedding
    FROM question
    WHERE question_id = question_id_in;

    IF target_embedding IS NULL THEN
        RAISE EXCEPTION 'No record found for the given question_id';
    END IF;

    -- Check if the combination already exists in question_vote
    SELECT COUNT(*) INTO vote_count
    FROM question_vote
    WHERE question_id = question_id_in
      AND session_id = session_id_in
      AND up_vote = similar_in;

    IF vote_count = 0 THEN
        -- Insert the combination if it doesn't exist
        INSERT INTO question_vote (question_id, session_id, up_vote) VALUES (question_id_in, session_id_in, similar_in);
    END IF;

    RETURN QUERY
    SELECT a.*
    FROM question a
    WHERE a.question_id <> question_id_in 
      -- this is a problematic where clauses when there is very little data
      AND a.question_id NOT IN (SELECT question_id FROM question_vote WHERE session_id = session_id_in)
    ORDER BY 
      CASE WHEN similar_in THEN a.embedding <-> target_embedding ELSE target_embedding <-> a.embedding END, 
      a.question_id 
    LIMIT 1;  
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION search(query TEXT, limit_rows INT DEFAULT 10)
RETURNS TABLE (
    question_id TEXT,
    question TEXT,
    answer TEXT,
    image_url TEXT,
    media JSONB,
    added_at TIMESTAMP WITH TIME ZONE,
    title TEXT,
    description TEXT,
    search_vector TSVECTOR,
    rank DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        q.question_id,
        q.question, 
        q.answer, 
        q.image_url, 
        q.media, 
        q.added_at,
        q.title,
        q.description,
        q.search_vector,
        ts_rank(q.search_vector, websearch_to_tsquery('english', query))::DOUBLE PRECISION AS rank
    FROM question AS q
    WHERE q.search_vector @@ websearch_to_tsquery('english', query)
    ORDER BY rank DESC
    LIMIT limit_rows;
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

CREATE OR REPLACE FUNCTION get_top_upvotes(start_date DATE, row_limit INT DEFAULT 50)
RETURNS TABLE (
    question_id TEXT,
    question TEXT,
    answer TEXT,
    image_url TEXT,
    media JSONB,
    added_at TIMESTAMP WITH TIME ZONE,
    title TEXT,
    description TEXT,
    up_votes BIGINT,
    down_votes BIGINT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT
        q.question_id,
        q.question,
        q.answer,
        q.image_url,
        q.media,
        q.added_at,
        q.title,
        q.description,
        COUNT(CASE WHEN qv.up_vote THEN 1 ELSE NULL END) AS up_votes,
        COUNT(CASE WHEN NOT qv.up_vote THEN 1 ELSE NULL END) AS down_votes
    FROM
        question_vote qv
    JOIN
        question q
    ON
        qv.question_id = q.question_id
    WHERE
        qv.vote_at >= start_date
        AND qv.vote_at <= current_date + INTERVAL '30 day'
    GROUP BY
        q.question_id,
        q.question,
        q.answer,
        q.image_url,
        q.media,
        q.added_at,
        q.title,
        q.description
    ORDER BY
        up_votes DESC
    LIMIT row_limit;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION insert_question_comment(
  in_question_id TEXT,
  in_session_id TEXT,
  in_comment TEXT
) RETURNS question_comment AS $$
DECLARE
  comment_count INTEGER;
  new_comment question_comment;
BEGIN
  -- Count the number of comments by session_id in the last hour
  SELECT COUNT(*)
  INTO comment_count
  FROM question_comment
  WHERE session_id = in_session_id
    AND added_at >= NOW() - INTERVAL '1 hour';

  -- Check if the comment_count is 10 or more, and raise an error if true
  IF comment_count >= 10 THEN
    RAISE EXCEPTION 'Error: Too many comments in the last hour for this session. Please try again soon.';
  ELSE
    -- Insert the new comment and return the inserted row
    INSERT INTO question_comment (question_id, session_id, comment)
    VALUES (in_question_id, in_session_id, in_comment)
    RETURNING * INTO new_comment;
    
    RETURN new_comment;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION full_image_url(image_url TEXT)
RETURNS TEXT AS $$
DECLARE
    pg_version TEXT;
BEGIN
    -- Get the PostgreSQL version
    SELECT version() INTO pg_version;

    -- Check if the PostgreSQL version contains "Homebrew"
    IF position('Homebrew' IN pg_version) > 0 THEN
        -- If "Homebrew" is found, prepend "http://localhost:3000" to image_url
        RETURN 'http://localhost:3000' || image_url;
    ELSE
        -- If "Homebrew" is not found, prepend "https://bot-e" to image_url
        RETURN 'https://bot-e.com' || image_url;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION lock_row(p_row_key TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    recent_lock_count INT;
BEGIN
    -- Check if there are any records with the same question_id added within the last two minutes
    SELECT COUNT(*)
    INTO recent_lock_count
    FROM row_lock
    WHERE row_key = p_row_key
      AND added_at >= NOW() - INTERVAL '2 minutes';

    -- If there are recent locks, return FALSE
    IF recent_lock_count > 0 THEN
        RETURN FALSE;
    ELSE
        -- Insert a new record into the question_lock table
        INSERT INTO row_lock (row_key)
        VALUES (p_row_key);

        -- Return TRUE to indicate success
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql;
