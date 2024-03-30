import secrets
from . import db
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # Relationships
    user = db.relationship('User', back_populates='tasks')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.save()
    
    def __repr__(self) -> str:
        return f"<Task {self.id} | title='{self.title}' description='{self.description}'>"

    def to_dict(self):
        return {
            "id" : self.id,
            "title" : self.title,
            "description" : self.description,
            "completed" : self.completed,
            "createdAt" : self.created_at,
            "user_id" : self.user_id
        }
    
    def update(self, **kwargs):
        allowed_fields = {"title", "description"}
        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(self, key, value)
        self.save()

    # Method to add and save entry to database
    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False) # Will need to be hashed
    date_created = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    # For authentication
    token = db.Column(db.String, index=True, unique=True)
    token_expiration = db.Column(db.DateTime(timezone=True))
    # Relationships
    tasks = db.relationship('Task', back_populates='user')

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.set_password(kwargs.get('password', ''))

    def __repr__(self):
        return f"<User {self.id}|username={self.username}, email={self.email}>"
    
    def set_password(self, plaintext_password):
        self.password = generate_password_hash(plaintext_password)
        self.save()

    def check_password(self, plaintext_password):
        return check_password_hash(self.password, plaintext_password)

    def to_dict(self):
        return {
            "id" : self.id,
            "username" : self.username,
            "email" : self.email,
            "dateCreated" : self.date_created,
            "tasks" : [t.to_dict() for t in self.tasks]
        }
    
    def get_token(self):
        now = datetime.now(timezone.utc)
        if self.token and (self.token_expiration > now + timedelta(minutes = 1)):
            return {"token" : self.token}
        self.token = secrets.token_hex(16)
        self.token_expiration = now + timedelta(days=7)
        self.save()
        return {
            "token" : self.token,
            "tokenExpiration" : self.token_expiration
        }
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    def update(self, **kwargs):
        other_fields = ["username", "email"]
        if "password" in kwargs:
            self.set_password(kwargs.get("password", ""))
        for key, value in kwargs.items():
            if key in other_fields:
                setattr(self, key, value)
        self.save()
        
    # This will delete the user along will all of their associated tasks
    def delete(self):
        for t in self.tasks:
            t.delete()
        db.session.delete(self)
        db.session.commit()