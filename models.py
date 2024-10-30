import bcrypt
from database import database

class FDataBase:
    def __init__(self, db):
        self.db = db

    async def getMenu(self):
        query = "SELECT * FROM mainmenu"
        return await self.db.fetch_all(query)

    async def addPost(self, title, text, is_visible=True):
        query = """
            INSERT INTO posts (title, text, time, is_visible)
            VALUES (:title, :text, now(), :is_visible)
        """
        values = {"title": title, "text": text, "is_visible": is_visible}
        try:
            await self.db.execute(query, values)
            return True
        except Exception as e:
            print(f"Error adding post: {e}")
            return False

    async def getPostsAnonce(self):
        query = "SELECT id, title, text FROM posts WHERE is_visible = TRUE ORDER BY time DESC"
        return await self.db.fetch_all(query)

    async def getPost(self, post_id):
        query = "SELECT title, text FROM posts WHERE id = :post_id LIMIT 1"
        return await self.db.fetch_one(query, values={"post_id": post_id})

class User:
    def __init__(self, db):
        self.db = db

    async def create_user(self, username: str, password: str, role: str = "user"):
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        query = """
            INSERT INTO users (username, password_hash, role)
            VALUES (:username, :password_hash, :role)
        """
        values = {"username": username, "password_hash": password_hash, "role": role}
        try:
            await self.db.execute(query, values)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    async def authenticate_user(self, username: str, password: str):
        query = "SELECT password_hash, role FROM users WHERE username = :username"
        result = await self.db.fetch_one(query, {"username": username})
        if result and bcrypt.checkpw(password.encode(), result["password_hash"].encode()):
            return {"username": username, "role": result["role"]}
        return None

    async def get_user_role(self, username: str):
        query = "SELECT role FROM users WHERE username = :username"
        result = await self.db.fetch_one(query, {"username": username})
        return result["role"] if result else None