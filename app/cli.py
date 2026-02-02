import typer
from app.database import create_db_and_tables, get_session, drop_all
from app.models import User
from fastapi import Depends
from sqlmodel import select
from sqlalchemy.exc import IntegrityError

cli = typer.Typer()

@cli.command()
def initialize():
    """
    Deletes all existing data and recreates the database tables with a default 'bob' user.
    """
    with get_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables
        bob = User(username = 'bob', email = 'bob@mail.com', password = 'bobpass') # Create a new user (in memory)
        db.add(bob) # Tell the database about this new data
        db.commit() # Tell the database persist the data
        db.refresh(bob) # Update the user (we use this to get the ID from the db)
        print("Database Initialized")

@cli.command()
def get_user(username: str = typer.Option(..., help="The username of this user")):
    """
    Fetches a specific user from the database.
    """
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found!')
            return
        print(user)

@cli.command()
def get_all_users():
    """
    Retrieves and displays a list of every user currently in the database.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        if not all_users:
            print("No users found")
        else:
            for user in all_users:
                print(user)


@cli.command()
def change_email(username: str = typer.Option(..., help="The username of this user"), new_email: str = typer.Option(..., help="The new email of this user")):
    """
    Updates the email address of an existing user.
    """
    with get_session() as db: # Get a connection to the database
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to update email.')
            return
        user.email = new_email
        db.add(user)
        db.commit()
        print(f"Updated {user.username}'s email to {user.email}")

@cli.command()
def create_user(username: str = typer.Option(..., help="The username of the new user"), email: str = typer.Option(..., help="The email of the new user"), password: str = typer.Option(..., help="The password of the new user")):
    """
    Adds a new, unexisting user to the database.
    """
    with get_session() as db: # Get a connection to the database
        newuser = User(username=username, email=email, password=password)
        try:
            db.add(newuser)
            db.commit()
        except IntegrityError as e:
            db.rollback() #let the database undo any previous steps of a transaction
            #print(e.orig) #optionally print the error raised by the database
            print("Username or email already taken!") #give the user a useful message
        else:
            print(newuser) # print the newly created user

@cli.command()
def delete_user(username: str = typer.Option(..., help="The username of the deleted user")):
    """
    Removes a user from the database based on their username.
    """
    with get_session() as db:
        user = db.exec(select(User).where(User.username == username)).first()
        if not user:
            print(f'{username} not found! Unable to delete user.')
            return
        db.delete(user)
        db.commit()
        print(f'{username} deleted')

from sqlmodel import select, or_, col

@cli.command()
def find_user(key: str = typer.Option(..., help="The user to be found")):
    """
    Searches for users using a partial match on either their username or email.
    """
    with get_session() as db:
        term = select(User).where(
            or_(
                col(User.username).contains(key),
                col(User.email).contains(key)
            )
        )
        users = db.exec(term).all() 
        if not users:
            print(f"'{key}' not found!")
            return
        
        for user in users:
            print(user)

@cli.command()
def list_users(limit: int= typer.Option(10, help="The maximum number of users to display"), offset: int = typer.Option(0, help="The starting index")):
    """
    Displays the first 10 users.
    """
    with get_session() as db:
        all_users = db.exec(select(User)).all()
        for i in range(len(all_users)):
            if i < limit:
                user = all_users[i]
                print(user)
    

if __name__ == "__main__":
    cli()