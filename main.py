import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import markdown
from fastapi import Body, FastAPI, File, UploadFile, status
from fastapi import Path as APIPath
from fastapi.responses import HTMLResponse, JSONResponse
from language_tool_python import LanguageTool
from language_tool_python.exceptions import LanguageToolError

from schema import SavedNotes

markdown_dir = Path.cwd() / "checked_markdown_files"
tools = {}


# Creates a directory for storing checked markdown files when api is started
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        markdown_dir.mkdir(exist_ok=True)
        tools["language_tool"] = LanguageTool("en-US")
        yield
    except LanguageToolError:
        raise LanguageToolError()
    finally:
        if tools["language_tool"]:
            tools["language_tool"].close()
            tools.clear()


app = FastAPI(title="markdown-note-api", lifespan=lifespan)


# Handles LanguageTool/grammar checker related errors
@app.exception_handler(LanguageToolError)
async def language_tool_error(request, exc: LanguageToolError):
    return JSONResponse(
        {"status": "error", "detail": str(exc)},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


@app.exception_handler(UnicodeDecodeError)
async def unicode_decode_error(request, exc: UnicodeDecodeError):
    return JSONResponse(
        {
            "status": "error",
            "detail": "Trouble decoding markdown file, try using UTF-8 compliant characters.",
        },
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def is_markdown_file(file):
    md_pattern = r".*\.(md|markdown)$"
    if re.search(md_pattern, file.filename, re.IGNORECASE):
        return True

    return False


def check_grammar(text):
    language_tool: LanguageTool = tools["language_tool"]
    error_matches = language_tool.check(text)

    g_errors = []
    for error in error_matches:
        g_error = dict()
        g_error["context"] = error.context
        g_error["message"] = error.message
        g_error["category"] = error.category
        g_error["replacements"] = error.replacements
        g_error["ruleId"] = error.rule_id

        g_errors.append(g_error)

    return g_errors


@app.get("/")
async def root():
    return JSONResponse("App is alive")


@app.post("/check", summary="checks the grammar of the uploaded markdown file")
async def grammar_checker(file: UploadFile = File(...)):
    if not is_markdown_file(file):
        return JSONResponse(
            {"status": "error", "detail": "File must be a markdown file."},
            status.HTTP_400_BAD_REQUEST,
        )

    md_content = await file.read()
    # convert from bytes to string
    try:
        md_content = md_content.decode()
    except UnicodeDecodeError:
        return JSONResponse(
            {
                "status": "error",
                "detail": "Trouble decoding markdown file, try using UTF-8 compliant characters.",
            }
        )

    errors = check_grammar(md_content)

    return JSONResponse({"grammatical_errors": errors})


@app.post("/save", summary="saves a note passed as a markdown file")
async def save(text: str = Body(..., media_type="text/markdown")):
    text_hash = abs(hash(text))
    file_path = markdown_dir / f"{text_hash}.md"

    with file_path.open("w", encoding="utf-8") as md_f:
        md_f.write(text)

    return JSONResponse({"file_name": text_hash})


@app.get("/notes", summary="lists saved markdown notes")
async def notes():
    md_notes = []
    count = 0

    for file in markdown_dir.iterdir():
        count += 1
        md_notes.append({"name": file.name})

    if md_notes:
        return SavedNotes(count=count, notes=md_notes)
    else:
        return JSONResponse({"detail": "No notes saved yet..."})


@app.get(
    "/note/{filename}", summary="returns the html version of a saved markdown note"
)
async def markdown_to_html(
    filename: Annotated[str, APIPath(title="the name of the file")],
):
    try:
        file_path = markdown_dir / f"{filename}.md"
        with file_path.open("r", encoding="utf-8") as f:
            markdown_str = f.read()
            html_str = markdown.markdown(markdown_str)

        return HTMLResponse(html_str)
    except FileNotFoundError:
        return JSONResponse({"status": "error", "detail": "File does not exist"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
