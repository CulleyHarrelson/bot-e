# Human Advice is Overrated

This sequence diagram is a work in progress.

![Sequence Diagram](docs/botty_flow.svg "Sequence Diagram")

## OS X homebrew packages:
- node

## OX X Installation Instructions for node.js

```bash
cd askbotty/
npm Install
npm install -g node-dev
npm start
open --url http://localhost:3000/

```

## Running docs/BottyDocs.ipynb

update python3 if necessary, then create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
pip install jupyterlab
jupyter-lab docs/BottyDocs.ipynb
```

The last command will open a jupyterlabs server.  To close the virtual python 
server use the "deactivate" command.


## Installation Issues

Currently the Foundation css files as installed by the npm are not working in layout.pug.
./node_modules/foundation-icons/foundation-icons.css does not surface the css file.  This 
is likely an issue with the "public" setting in app.py.  Currently the work around is to 

```bash
cp -r node_modules/foundation* public/stylesheets/
```
