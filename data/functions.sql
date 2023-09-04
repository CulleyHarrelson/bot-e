
CREATE OR REPLACE FUNCTION proximal_question(question_id_in TEXT, session_id_in TEXT, similar_in BOOLEAN DEFAULT true)
RETURNS SETOF question
AS $$
DECLARE
    target_embedding vector(1536);
BEGIN
    SELECT embedding INTO target_embedding
    FROM question
    WHERE question_id = question_id_in;

    IF target_embedding IS NULL THEN
        RAISE EXCEPTION 'No record found for the given question_id';
    END IF;

    INSERT INTO question_vote (question_id, session_id) values (question_id_in, session_id_in);

    RETURN QUERY
    SELECT a.*
    FROM question a
    WHERE a.question_id <> question_id_in 
      AND a.question_id NOT IN (SELECT question_id FROM question_vote where session_id = session_id_in)
    ORDER BY 
      CASE WHEN similar_in THEN a.embedding <-> target_embedding ELSE target_embedding <-> a.embedding END, 
      a.question_id 
    LIMIT 1;  
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

