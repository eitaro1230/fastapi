import asyncio
from typing import Union

import motor.motor_asyncio
from auth_utils import AuthJwtCsrf
from bson import ObjectId
from decouple import config

from fastapi import HTTPException

MONGO_API_KEY = config("MONGO_API_KEY")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_API_KEY)
client.get_io_loop = asyncio.get_event_loop
database = client.API_DB
collection_todo = database.todo
collection_user = database.user
auth = AuthJwtCsrf()


def todo_serializer(todo) -> dict:
    """jsonデータをdict型に変換

    Args:
        todo (_type_): _description_

    Returns:
        dict: _description_
    """
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "description": todo["description"],
    }


def user_serializer(user) -> dict:
    return {"id": str(user["_id"]), "email": user["email"]}


async def db_create_todo(data: dict) -> Union[dict, bool]:
    """mongoDBにtodoを作成

    Args:
        data (dict): _description_

    Returns:
        Union[dict, bool]: 成功したら作成したtodoを返却、失敗したらFalseを返却
    """
    todo = await collection_todo.insert_one(data)
    new_todo = await collection_todo.find_one({"_id": todo.inserted_id})
    if new_todo:
        return todo_serializer(new_todo)
    return False


async def db_get_todos() -> list:
    """mongoDBからすべてのtodoを取得

    Returns:
        list: デフォルト100件を返却
    """
    todos = [
        todo_serializer(todo)
        for todo in await collection_todo.find().to_list(length=100)
    ]
    return todos


async def db_get_single_todo(id: str) -> Union[dict, bool]:
    """mongoDBからidを指定して1つのtodoを取得

    Args:
        id (str): todoのidを指定

    Returns:
        Union[dict, bool]: 成功したらtodoを返却、失敗したらFalseを返却
    """
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        return todo_serializer(todo)
    return False


async def db_update_todo(id: str, data: dict) -> Union[dict, bool]:
    """mongoDBからidを指定して1つのtodoを編集

    Args:
        id (str): _description_
        data (dict): _description_

    Returns:
        Union[dict, bool]: _description_
    """
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        updated_todo = await collection_todo.update_one(
            {"_id": ObjectId(id)}, {"$set": data}
        )
        if updated_todo.modified_count > 0:
            new_todo = await collection_todo.find_one({"_id": ObjectId(id)})
            return todo_serializer(new_todo)
    return False


async def db_delete_todo(id: str) -> bool:
    """mongoDBから1つのidを指定して1つのtodoを削除

    Args:
        id (str): _description_

    Returns:
        bool: _description_
    """
    todo = await collection_todo.find_one({"_id": ObjectId(id)})
    if todo:
        deleted_todo = await collection_todo.delete_one({"_id": ObjectId(id)})
        if deleted_todo.deleted_count > 0:
            return True
    return False


async def db_signup(data: dict) -> dict:
    email = data.get("email")
    password = data.get("password")
    overlap_user = await collection_user.find_one({"email": email})
    if overlap_user:
        raise HTTPException(status_code=400, detail="Email is already taken")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password too short")
    user = await collection_user.insert_one(
        {"email": email, "password": auth.generate_hashed_pw(password)}
    )
    new_user = await collection_user.find_one({"_id": user.inserted_id})
    return user_serializer(new_user)


async def db_login(data: dict) -> str:
    email = data.get("email")
    password = data.get("password")
    user = await collection_user.find_one({"email": email})
    if not user or not auth.verify_pw(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth.encode_jwt(user["email"])
    return token
