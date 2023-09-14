# Human Advice is Overrated


## MVP TODO:

- Finish TOS
- finish comments
    - do not refresh page
- change image_url to use full domain
- Build Server
    - Node.js DONE
    - nginx
        -SSL certificate
    - Postgresql - DONE
        - pgVector - DONE
        - backups
    - Python 3.9 
        - openAI - stuck on gcc12
        - Flask/Gunicorn
        - bot-e Daemon
            - logging
            - Supervisor
- Transfer domain
    - Oct 4
- Add LLC stuff
- Email Marketing
    - capture email addresses?

Backlog:
    - Flutter App
    - Varnish
    - Email Marketing
    - Create Social Media Presence
        - Instagram
        - LinkedIn
        - TikTok
        - Facebook

Advice Request Message Flow:

![Sequence Diagram](docs/bot-e_flow.png "Sequence Diagram")

Mind Map
![mindmap](docs/mindmap.png "mindmap")

```
mindmap
  root((bot-e))
    Flutter
        iOS
        Android
        Web App
        Desktop Apps
    FreeBSD
        Email Server
            Newsletter
        Postgresql
            pgVector
            full text search
        bot-e Daemond
            Prompt Engineering
                advice
        Varnish Cache
            Flask/Gunicorn API
                Flutter/MVP Endpoint
                    Browse/Search
                New Question
                    OpenAI
                        Moderation
                        Embedding
            Node.js Web server
                MVP bot-e App
                Marketing
                Advice column
```


## Postgresql setup

- install Postgresql
- install pgVector
- execute data/schema.sql
- execute data/functions.sql

