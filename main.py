import os
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List
from database import supabase, supabase_admin
import schemas

app = FastAPI(title="Task Management API")

ADMIN_EMAILS = [email.strip() for email in os.getenv("ADMIN_EMAILS", "").split(",") if email.strip()]

def get_current_user(access_token: str = Header(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Token not provided")
    try:
        user_response = supabase.auth.get_user(access_token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user_response.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.get("/")
def read_root():
    return {"message": "Task Management API is running!"}


class UserCredentials(BaseModel):
    email: str
    password: str


@app.post("/register")
def register_user(credentials: UserCredentials):
    supabase.auth.sign_up({"email": credentials.email, "password": credentials.password})
    return {"message": "User registered successfully!"}


@app.post("/login")
def login_user(credentials: UserCredentials):
    response = supabase.auth.sign_in_with_password({"email": credentials.email, "password": credentials.password})
    return {"access_token": response.session.access_token}


@app.post("/tasks/", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, current_user=Depends(get_current_user)):
    task_data = task.model_dump(mode='json')
    task_data["user_id"] = current_user.id

    response = supabase.table("tasks").insert(task_data).execute()
    if response.data:
        return response.data[0]
    raise HTTPException(status_code=400, detail="Database error")


@app.get("/tasks/", response_model=List[schemas.TaskResponse])
def get_tasks(current_user=Depends(get_current_user)):
    if current_user.email in ADMIN_EMAILS:
        response = supabase_admin.table("tasks").select("*").execute()
    else:
        response = supabase.table("tasks").select("*").eq("user_id", current_user.id).execute()
    return response.data


@app.put("/tasks/{task_id}", response_model=schemas.TaskResponse)
def update_task(task_id: str, task: schemas.TaskUpdate, current_user=Depends(get_current_user)):
    task_data = task.model_dump(exclude_unset=True, mode='json')
    if not task_data:
        raise HTTPException(status_code=400, detail="No data provided to update")

    if current_user.email in ADMIN_EMAILS:
        query = supabase_admin.table("tasks").update(task_data).eq("id", task_id)
    else:
        query = supabase.table("tasks").update(task_data).eq("id", task_id).eq("user_id", current_user.id)

    response = query.execute()
    if response.data:
        return response.data[0]
    raise HTTPException(status_code=404, detail="Task not found or unauthorized")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str, current_user=Depends(get_current_user)):
    if current_user.email in ADMIN_EMAILS:
        query = supabase_admin.table("tasks").delete().eq("id", task_id)
    else:
        query = supabase.table("tasks").delete().eq("id", task_id).eq("user_id", current_user.id)

    response = query.execute()
    if response.data:
        return {"message": "Task deleted"}
    raise HTTPException(status_code=404, detail="Task not found or unauthorized")