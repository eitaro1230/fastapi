from typing import List

from auth_utils import AuthJwtCsrf
from database import (
    db_create_todo,
    db_delete_todo,
    db_get_single_todo,
    db_get_todos,
    db_update_todo,
)
from fastapi_csrf_protect import CsrfProtect
from schemas import SuccessMsg, Todo, TodoBody
from starlette.status import HTTP_201_CREATED

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder

router = APIRouter()
auth = AuthJwtCsrf()


@router.post("/api/todo", response_model=Todo)
async def create_todo(
    request: Request,
    response: Response,
    data: TodoBody,
    csrf_protect: CsrfProtect = Depends(),
):
    """todoを作成

    Args:
        request (Request): _description_
        response (Response): _description_
        data (TodoBody): _description_

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    new_token = auth.verify_csrf_update_jwt(request, csrf_protect, request.headers)
    # リクエストのjsonをdictに変換
    todo = jsonable_encoder(data)
    res = await db_create_todo(todo)
    # postなのでokは201に変換
    response.status_code = HTTP_201_CREATED
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return res
    raise HTTPException(status_code=404, detail="Create task failed")


@router.get("/api/todo", response_model=List[Todo])
async def get_todos(request: Request):
    """すべてのtodoを取得

    Returns:
        _type_: _description_
    """
    # auth.verify_jwt(request)
    res = await db_get_todos()
    return res


@router.get("/api/todo/{id}", response_model=Todo)
async def get_single_todo(id: str, request: Request, response: Response):
    """idを指定して1つのtodoを取得

    Args:
        id (str): _description_

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    new_token, _ = auth.verify_update_jwt(request)
    res = await db_get_single_todo(id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return res
    raise HTTPException(status_code=404, detail=f"Task of ID:{id} doesn't exist")


@router.put("/api/todo{id}", response_model=Todo)
async def update_todo(
    id: str,
    data: TodoBody,
    request: Request,
    response: Response,
    csrf_protect: CsrfProtect = Depends(),
):
    """idを指定して1つのtodoを編集

    Args:
        id (str): _description_
        data (TodoBody): _description_

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    new_token = auth.verify_csrf_update_jwt(request, csrf_protect, request.headers)
    todo = jsonable_encoder(data)
    res = await db_update_todo(id, todo)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return res
    raise HTTPException(status_code=404, detail="Update task failed")


@router.delete("/api/todo/{id}", response_model=SuccessMsg)
async def delete_todo(
    id: str,
    request: Request,
    response: Response,
    csrf_protect: CsrfProtect = Depends(),
):
    """idを指定して1つのtodoを削除

    Args:
        id (str): _description_

    Raises:
        HTTPException: _description_

    Returns:
        _type_: _description_
    """
    new_token = auth.verify_csrf_update_jwt(request, csrf_protect, request.headers)
    res = await db_delete_todo(id)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {new_token}",
        httponly=True,
        samesite="none",
        secure=True,
    )
    if res:
        return {"message": "Successfully deleted"}
    raise HTTPException(status_code=404, detail="Delete task failed")
