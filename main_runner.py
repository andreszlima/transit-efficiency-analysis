import os
from dotenv import load_dotenv

# Load .env file
load_dotenv('scripts/.env')

os.system('python3 loader/get_realtime.py')
os.system('python3 scripts/diff_times.py')