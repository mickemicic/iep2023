from datetime import timedelta
import os

# databaseUrl = os.environ["DATABASE_URL"]

class Configuration:
   # SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://root:root@{databaseUrl}/store"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:root@/store"
    JSON_SORT_KEYS = False                      # za output polja kada vracam jsonify
    JWT_SECRET_KEY = "JWT_SECRET_KEY"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
