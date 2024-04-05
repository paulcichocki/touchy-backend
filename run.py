# run.py
from app import create_app
import os
from dotenv import load_dotenv
load_dotenv()

app = create_app()
app.app_context().push()

if __name__ == '__main__':
    if os.getenv('DEBUG_MODE') == 'True':
        app.run(host='0.0.0.0', debug=True)
    else:
        app.run(host='0.0.0.0')
