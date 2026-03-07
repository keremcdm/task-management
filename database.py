import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ADMIN_KEY = os.getenv("SUPABASE_ADMIN_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, SUPABASE_ADMIN_KEY]):
    raise ValueError("Critical Error: There are missing variables in .env file!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_ADMIN_KEY)