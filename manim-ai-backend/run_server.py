import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        # Exclude generated scenes and media from the reload watcher
        reload_excludes=["temp_scenes/*", "media/*", "media/videos/*"]
    )
