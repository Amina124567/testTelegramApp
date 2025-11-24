import os
from supabase import create_client

# Глобальная переменная
supabase = None

def init_supabase():
    global supabase
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Missing Supabase credentials")
    
    supabase = create_client(supabase_url, supabase_key)
    return supabase

# Инициализируем при импорте
try:
    supabase = init_supabase()
except ValueError:
    # Пропускаем ошибку при импорте, будем инициализировать позже
    pass