curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "system",
        "content": ""
      },
      {
        "role": "user",
        "content": "I am in my mid-20s, and my best friend and I were very close. At the start of this year, we were in a car crash. I survived with a few broken bones. She was the driver and died on the scene. Everyone was devastated. My question relates to her material belongings. As I understand it, her grieving parents are slowly going through\u00a0her possessions. Am I, as someone who spent years in a very tight friendship with this\u00a0woman,\u00a0entitled to go through her possessions, as well? I\u2019m chiefly interested in gifts and trinkets that I gave her that would have sentimental value. I also lent her a book that would be nice to have returned.\u00a0It would mean a lot to me if I could have some of her things (or at least have some of my things back).\u00a0How do I gently broach the subject of her belongings with her family? Do I wait and risk having all the things I value thrown out? Should I just let it go, and know that I had and lost a good friend? \u2014I Lost Someone, Too Dear Lost,<br/>I wish I knew what book you\u2019d lent your late friend, because I would be happy to order a copy for you myself, rather than have you assault these grief-stricken people and tell them there\u2019s a volume on their daughter\u2019s shelf that actually belongs to you. No, you do not have standing to rummage through her things. You\u2019ve lost a friend and been through a terrible trauma, so I am trying to be generous about your unseemly desire to regift to yourself the items you gave this young woman. I\u2019m assuming you two actually exchanged presents over the years, so what you have by way of remembrance are the things she gave you. You certainly could pay a call on her parents to see how they\u2019re doing. Keep in mind the pain you might evoke\u2014after all, you lived and their daughter died. If they offer that they\u2019d like you to have something of hers as a memento, try to restrain the impulse to load a moving box worth of stuff. If they don\u2019t, be grateful that you survived a deadly accident, which is the ultimate gift. "
      }
    ]
  }'

