# Human Advice is Overrated

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

## TODO:

- [reCAPTCHA](https://developers.google.com/recaptcha/docs/versions)
- Finish About Page
- Finish TOS
- Build Server
    - Flask/Gunicorn
    - Varnish
    - Node.js
    - Postgresql
        - pgVector
        - backups
    - bot-e Daemon
    - email server
- Transfer domain
- Add LLC stuff
- Newsletter signup 



## FreeBSD services:

- Email Server
- Postgresql
- Bot-e Daemon
- Flask/Gunicorn API
- Node.js Server
- Varnish Cache

## Postgresql setup

- install Postgresql
- install pgVector
- execute data/schema.sql
- execute data/functions.sql

