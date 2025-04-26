from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import json
from typing import Optional, List
import uuid
import uvicorn
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# File to store user data
USER_FILE = "credentials.json"


# Pydantic model for user data
class User(BaseModel):
    name: str
    password: str
    studies: str


# Function to read users from JSON file
def read_users() -> List[dict]:
    if not os.path.exists(USER_FILE):
        return []
    try:
        with open(USER_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


# Function to write users to JSON file
def write_users(users: List[dict]):
    with open(USER_FILE, "w") as file:
        json.dump(users, file, indent=4)


# Function to check if user already exists
def user_exists(name: str) -> bool:
    users = read_users()
    return any(user["name"] == name for user in users)


# Function to verify user credentials
def verify_user(name: str, password: str) -> Optional[dict]:
    users = read_users()
    for user in users:
        if user["name"] == name and user["password"] == password:
            return user
    return None


# Create templates directory if it doesn't exist
if not os.path.exists("templates"):
    os.makedirs("templates")

# HTML template for signup page
with open("templates/signup.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sign Up</title>
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h2 { text-align: center; }
            form { display: flex; flex-direction: column; gap: 10px; }
            input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            button { padding: 10px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #218838; }
            .error { color: red; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Sign Up</h2>
            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}
            <form action="/signup" method="post">
                <input type="text" name="name" placeholder="Name" required>
                <input type="password" name="password" placeholder="Password" required>
                <input type="text" name="studies" placeholder="Studies" required>
                <button type="submit">Sign Up</button>
            </form>
        </div>
    </body>
    </html>
    """)

# HTML template for login page
with open("templates/login.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
            h2 { text-align: center; }
            form { display: flex; flex-direction: column; gap: 10px; }
            input { padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
            button { padding: 10px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            .error { color: red; text-align: center; }
            .success { color: green; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Login</h2>
            {% if success %}
                <p class="success">{{ success }}</p>
            {% endif %}
            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}
            <form action="/login" method="post">
                <input type="text" name="name" placeholder="Name" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """)

# HTML template for success page
with open("templates/success.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Success</title>
        <style>
            body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f0f0f0; }
            .container { background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; }
            h2 { text-align: center; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Login Successful!</h2>
            <p>Welcome, {{ name }}!</p>
            <p>Your studies: {{ studies }}</p>
            <a href="/login">Back to Login</a>
        </div>
    </body>
    </html>
    """)


@app.get("/", response_class=HTMLResponse)
async def get_signup(request: Request):
    try:
        return templates.TemplateResponse("signup.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering signup page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/signup")
async def signup(name: str = Form(...), password: str = Form(...), studies: str = Form(...)):
    try:
        if user_exists(name):
            return templates.TemplateResponse("signup.html", {"request": {}, "error": "User already exists!"})

        # Store user data in JSON file
        user = {"name": name, "password": password, "studies": studies}
        users = read_users()
        users.append(user)
        write_users(users)

        # Redirect to login page with success message
        response = RedirectResponse(url="/login", status_code=303)
        return response
    except Exception as e:
        logger.error(f"Error during signup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    try:
        return templates.TemplateResponse("login.html",
                                          {"request": request, "success": "Sign up successful! Please login."})
    except Exception as e:
        logger.error(f"Error rendering login page: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/login")
async def login(request: Request, name: str = Form(...), password: str = Form(...)):
    try:
        user = verify_user(name, password)
        if user:
            return templates.TemplateResponse("success.html",
                                              {"request": request, "name": user["name"], "studies": user["studies"]})
        else:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid name or password!"})
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


"""if _name_ == "_main_":
    parser = argparse.ArgumentParser(description="Run FastAPI application")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    args = parser.parse_args()

    uvicorn.run(app, host="0.0.0.0", port=args.port)"""