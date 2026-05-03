from waitress import serve
from app import app

print("🚀 Сервер запущен и доступен для всех в сети!")
serve(app, host='0.0.0.0', port=5000, threads=4)
