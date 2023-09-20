# Human Advice is Overrated


## MVP TODO:

- Finish Privacy Policy 
- change image_url to use full domain
- Build Server
    - pm2
    - Gunicorn
        - aiohttp
    - Postgresql 
        - backups
    - bot-e Daemon
        - asyncio
        - logging
        - Supervisor
- Transfer domain
    - Oct 4
- Add LLC stuff
- Email Marketing
    - capture email addresses?
- review ai image/video tools:
    - https://cloudinary.com/products/programmable_media
    - https://imagekit.io/
    - https://imgix.com/
    - https://elevenlabs.io/

Backlog:
    - Flutter App
    - Varnish
    - Websockets streaming response
    - Create Social Media Presence
        - Instagram
        - LinkedIn
        - TikTok
        - Facebook
    - Email Marketing

Advice Request Message Flow:

![Sequence Diagram](docs/bot-e_flow.png "Sequence Diagram")

Mind Map
![mindmap](docs/mindmap.png "mindmap")

```
mindmap
  root((bot-e))
    APIs
        OpenAI
        Stability.ai
        reCAPTCHA
        YouTube
        Instagram
        TikTok
    Social Networks
        Reels
            Instagram
            TikTok
            YouTube
        Image Meme
            Instagram
            Facebook
            YouTube
            TikTok
        LinkedIn
    Flutter
        iOS
        Android
        Web App
        Desktop Apps
    FreeBSD Server Farm
        Postgresql
            pgVector
            full text search
        bot-e Daemond
            asyncpg
            Prompt Engineering
                advice
            Image Generation
        Varnish Cache
            nginx
                gunicorn
                    aiohttp
                        Get Question
                        Vote
                        Similarity search
                        Full-Text Search
                        New Comment
                        New Question
                            OpenAI
                                Moderation
                                Embedding
                Node.js Web server
                    express.js
                        Pug Templates
                            Foundation CSS
```


## Postgresql setup

- install Postgresql
- install pgVector
```
createdb bot-e
```
- execute data/schema.sql
- execute data/functions.sql

## Website setup

The code anticipates the development version of node.js is running on port 3000
use npm to install the packages in bot-e/web/packages.json and use npm start
to start the dev server. a symbolic link is required

```
ln -s images/questions web/public/images/questions
```

## API setup

The express app expects an api server at localhost:6464 
Setup commands:

```
cd bot-e
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python api.py
# when testing gunicorn 
# gunicorn -b localhost:6464 --reload api:app
```

## Bot-E Daemon

In development, a long-running python process is needed to 
execute the api calls when question new records are inserted into the database. 
To start this process run these commands:

```
cd bot-e
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./bote.py
```


