from server import app

if __name__ == "__main__":
    import uvicorn
    # If running main.py directly, we can still point uvicorn to server:app
    # or main:app if we want to be consistent.
    # But since the logic is in server.py, pointing to server:app is safer for reload.
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
