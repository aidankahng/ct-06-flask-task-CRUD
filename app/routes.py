from flask import redirect, request, render_template
from . import app, db
from .models import Task, User
from .auth import basic_auth, token_auth


# Displays the homepage index.html
@app.route("/", methods=["GET"])
def display_homepage():
    return render_template("index.html")


@app.route("/token/", methods=["GET"])
@basic_auth.login_required
def token():
    user = basic_auth.current_user()
    return user.get_token()


# Returns a list of dictionary tasks
@app.route('/tasks/', methods=["GET"])
def get_tasks():
    search = request.args.get('q')
    sel_stmt = db.select(Task)
    if search:
        sel_stmt = sel_stmt.where(Task.title.ilike('%'+ search +'%'))
    tasks = db.session.execute(sel_stmt).scalars().all()
    return [t.to_dict() for t in tasks], 200


# Post route will create new tasks given [VERIFIED USER]
@app.route('/tasks/', methods=['POST'])
@token_auth.login_required
def create_task():
    current_user = token_auth.current_user()

    if not request.is_json:
        return {'ERROR' : 'Content not a JSON'}, 400
    
    data = request.json
    # check to make sure the data is valid
    required_keys = ["title", "description"]
    missing_keys = []
    for key in required_keys:
        if key not in data:
            missing_keys.append(key)
    if missing_keys:
        return {"ERROR" : f"Keys: {', '.join(missing_keys)}" 
                + f" are missing from request"}, 400
    
    title = data.get('title')
    description = data.get('description')
    completed = data.get('completed', False)
    user_id = current_user.id

    new_task = Task(title=title, description=description, completed=completed, user_id=user_id)

    return new_task.to_dict(), 201


# Returns a task as json or error message
@app.route('/tasks/<int:task_id>/', methods=["GET"])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task:
        return task.to_dict()
    return {'ERROR' : f'Unable to find task of id: {task_id}'}, 404

# Route to edit/delete a task
@app.route('/tasks/<int:task_id>/', methods=["PUT", "DELETE"])
@token_auth.login_required
def edit_task(task_id):
    current_user = token_auth.current_user()
    task = db.session.get(Task, task_id)
    if task == None:
        return {"ERROR" : f"Task with ID:{task_id} does not exist"}, 404
    if current_user is not task.user:
        return {"ERROR" : f"This is not your task. You do not have permission to edit"}, 403
    if request.method=="PUT":
        if not request.is_json:
            return {'ERROR' : 'Content not a JSON'}, 400
        data = request.json
        task.update(**data)
        return task.to_dict(), 201
    elif request.method=="DELETE":
        task.delete()
        return {"SUCCESS" : f"Task #{task.id} has been deleted."}, 201
    else:
        return {"ERROR" : "UNCAUGHT ERROR"}, 400

    
# Route to create a new user
@app.route("/users/", methods=["POST"])
def create_user():
    if not request.is_json:
        return {'ERROR' : 'Content must be JSON'}, 400
    data = request.json
    required_fields = ["username", "email", "password"]
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
    if missing:
        return {"ERROR" : f"{', '.join(missing)} must be in request."}, 400
    
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    # create our new user
    new_user = User(username=username, email=email, password=password)
    # Message confirming user has been added successfully
    return new_user.to_dict(), 201


# Endpoint to retreive info about a specific user by id
@app.route("/users/<int:user_id>/", methods=["GET"])
def get_user_by_id(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return {"ERROR" : f"User #{user_id} not found"}, 404
    return user.to_dict(), 200

# Endpoint to update or delete a user by id
@app.route("/users/<int:user_id>/", methods=["PUT", "DELETE"])
@token_auth.login_required
def edit_user(user_id):
    current_user = token_auth.current_user()
    if current_user.id != user_id:
        return {"ERROR" : "You are not allowed to edit another user."}, 403
    if request.method=="PUT":
        if not request.is_json:
            return {"ERROR" : "Content must be JSON"}, 400
        data = request.json
        allowed_changes = ["username", "email", "password"]
        changes_in_request = []
        for field in allowed_changes:
            if field in data:
                changes_in_request.append(field)
        current_user.update(**data)
        return [{"Changed Fields" : changes_in_request},current_user.to_dict()], 201
    elif request.method=="DELETE":
        current_user.delete()
        return {"SUCCESS" : "Your account and tasks have been deleted"}, 201

# Endpoint /me redirects to current user's user page
@app.route("/me", methods=["GET"])
@token_auth.login_required
def get_current_user():
    current_user = token_auth.current_user()
    user_id = current_user.id
    return redirect(f"/users/{user_id}/", code=302)