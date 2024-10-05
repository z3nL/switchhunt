from django.apps import AppConfig
from django.db import connections


class AppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'
    
    def ready(self):
        # Check database connection when the app is ready
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
            print("Successfully connected to the MongoDB database!")
        except Exception as e:
            print(f"Failed to connect to the database: {e}")