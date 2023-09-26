import bote
import json
import asyncio


async def main():
    question = await bote.post_question("the quick brown fox jumped over the lazy dog")
    comments = await question_comments(question["question_id"])
    print(comments)  # You can use the result as needed


async def question_comments(question_id):
    # TODO: moderate this
    conn = await bote.db_connect2()

    if not bote.validate_key(question_id):
        return json.dumps([])

    query = """
        SELECT
            question_id,
            comment,
            session_id,
            parent_comment_id,
            comment_id,
            TO_CHAR(added_at, 'YYYY-MM-DD HH:MI AM') AS added_at
        FROM question_comment
        WHERE question_id = $1
        ORDER BY added_at DESC
        LIMIT 100
        """

    async with conn.transaction():
        comments = await conn.fetch(query, question_id)

    if not comments:
        return json.dumps([])

    json_response = json.dumps(comments, default=custom_json_serializer)
    return json_response


if __name__ == "__main__":
    asyncio.run(main())
