# admin/main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database_client import DatabaseClient
import aiosqlite
import os

app = FastAPI()
templates = Jinja2Templates(directory="admin/templates")
db_client = DatabaseClient()

@app.get("/", response_class=HTMLResponse)
async def read_pending(request: Request):
    """
    Fetches responses that are awaiting affiliate links. 
    Only entries where 'affiliate_link' is NULL and status is 'pending' are retrieved.
    """
    try:
        async with aiosqlite.connect(db_client.db_path) as db:
            cursor = await db.execute("""
                SELECT unique_number, contact, message_text, generated_response
                FROM final_response_table
                WHERE affiliate_link IS NULL AND status = 'pending';
            """)
            rows = await cursor.fetchall()
            return templates.TemplateResponse("pending.html", {
                "request": request, 
                "responses": rows,
                "message": request.query_params.get("message"),
                "message_type": request.query_params.get("type")
            })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add_affiliate/")
async def add_affiliate(
    request: Request, 
    unique_number: int = Form(...), 
    affiliate_link: str = Form(...)
):
    """
    Adds an affiliate link to the record with the given unique_number.
    The affiliate link must start with either 'http://' or 'https://'.
    """
    # Validate the affiliate link format
    if not (affiliate_link.startswith("http://") or affiliate_link.startswith("https://")):
        # Redirect with error message
        return RedirectResponse(url="/?message=Invalid affiliate link format.&type=error", status_code=303)
    
    # Update the affiliate link in the database
    try:
        await db_client.update_affiliate_link(unique_number, affiliate_link)
        # Redirect with success message
        return RedirectResponse(url="/?message=Affiliate link added successfully.&type=success", status_code=303)
    except Exception as e:
        # Redirect with error message
        return RedirectResponse(url=f"/?message=Error adding affiliate link: {str(e)}&type=error", status_code=303)

@app.post("/delete_response/")
async def delete_response(
    request: Request,
    unique_number: int = Form(...)
):
    """
    Deletes the response with the given unique_number from the database.
    """
    try:
        await db_client.delete_pending_response(unique_number)
        # Redirect with success message
        return RedirectResponse(url="/?message=Response deleted successfully.&type=success", status_code=303)
    except Exception as e:
        # Redirect with error message
        return RedirectResponse(url=f"/?message=Error deleting response: {str(e)}&type=error", status_code=303)
