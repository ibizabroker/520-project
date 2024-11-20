# social_media.py

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from models import (
    User,
    Recipe,
    SocialMedia,
    Bookmark,
    Comment,
)
from database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_current_user(request: Request, db: Session):
    if 'user_id' not in request.session:
        raise HTTPException(status_code=401, detail="Unauthorized")
    user = db.query(User).filter(User.UserID == request.session['user_id']).first()
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

# Define Pydantic models for request bodies
class RecipeIDRequest(BaseModel):
    recipe_id: str

class SMIDRequest(BaseModel):
    smid: str

class CommentRequest(BaseModel):
    smid: str
    comment_text: str

@router.post("/add_post")
def add_post_on_social_media(
    request_body: RecipeIDRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    recipe_id = request_body.recipe_id
    recipe = db.query(Recipe).filter(Recipe.RecipeID == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if recipe.UserID != user.UserID:
        raise HTTPException(status_code=403, detail="Permission denied")
    recipe.Visibility = True

    # Create a SocialMedia entry if it doesn't exist
    social_media_entry = db.query(SocialMedia).filter(SocialMedia.RecipeID == recipe_id).first()
    if not social_media_entry:
        social_media_entry = SocialMedia(RecipeID=recipe_id)
        db.add(social_media_entry)

    db.commit()
    return {
        "message": "Recipe visibility updated to public and added to social media",
        "SMID": social_media_entry.SMID
    }

@router.get("/posts")
def fetch_posts(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    # Get all public recipes
    recipes = db.query(Recipe).filter(Recipe.Visibility == True).all()

    # Include social media data
    posts = []
    for recipe in recipes:
        social_media_entry = db.query(SocialMedia).filter(SocialMedia.RecipeID == recipe.RecipeID).first()
        posts.append({
            "SMID": social_media_entry.SMID if social_media_entry else None,
            "RecipeID": recipe.RecipeID,
            "RecipeName": recipe.RecipeName,
            "RecipeContent": recipe.RecipeContent,
            "UserID": recipe.UserID,
            "Likes": social_media_entry.Likes if social_media_entry else 0
        })
    return posts

@router.post("/like_post")
def like_post(
    request_body: SMIDRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    smid = request_body.smid
    social_media_entry = db.query(SocialMedia).filter(SocialMedia.SMID == smid).first()
    if not social_media_entry:
        raise HTTPException(status_code=404, detail="Post not found on social media")
    social_media_entry.Likes += 1
    db.commit()
    return {"message": "Post liked successfully"}

@router.post("/unlike_post")
def unlike_post(
    request_body: SMIDRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    smid = request_body.smid
    social_media_entry = db.query(SocialMedia).filter(SocialMedia.SMID == smid).first()
    if not social_media_entry:
        raise HTTPException(status_code=404, detail="Post not found on social media")
    if social_media_entry.Likes > 0:
        social_media_entry.Likes -= 1
        db.commit()
        return {"message": "Post unliked successfully"}
    else:
        return {"message": "Cannot unlike, likes count is already zero"}

@router.post("/add_bookmark")
def add_bookmark(
    request_body: RecipeIDRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    recipe_id = request_body.recipe_id
    new_bookmark = Bookmark(UserID=user.UserID, RecipeID=recipe_id)
    db.add(new_bookmark)
    db.commit()
    return {"message": "Bookmark added successfully"}

@router.get("/bookmarks")
def fetch_bookmarks(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    bookmarks = db.query(Bookmark).filter(Bookmark.UserID == user.UserID).all()
    recipes = []
    for bookmark in bookmarks:
        recipe = db.query(Recipe).filter(Recipe.RecipeID == bookmark.RecipeID).first()
        if recipe:
            recipes.append({
                "RecipeID": recipe.RecipeID,
                "RecipeName": recipe.RecipeName,
                "RecipeContent": recipe.RecipeContent,
                "UserID": recipe.UserID,
                "Visibility": recipe.Visibility
            })
    return recipes

@router.post("/add_comment")
def add_comment(
    request_body: CommentRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    smid = request_body.smid
    comment_text = request_body.comment_text
    new_comment = Comment(
        SMID=smid,
        UserID=user.UserID,
        CommentText=comment_text
    )
    db.add(new_comment)
    db.commit()
    return {"message": "Comment added successfully"}

@router.get("/comments/{smid}")
def fetch_comments(smid: str, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    comments = db.query(Comment).filter(Comment.smid == smid).all()
    comments_with_user_info = []
    for comment in comments:
        commenter = db.query(User).filter(User.UserID == comment.UserID).first()
        comments_with_user_info.append({
            "CommentText": comment.CommentText,
            "UserID": commenter.UserID,
            "UserName": commenter.Name
        })
    return comments_with_user_info
