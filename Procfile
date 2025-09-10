web: gunicorn --bind 0.0.0.0:$PORT --workers 4 --timeout 120 app:app
worker: python -m tasks.cleanup_tasks
release: python init_db.py

