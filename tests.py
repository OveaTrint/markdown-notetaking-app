import io

import markdown
import pytest
from fastapi.testclient import TestClient
from starlette import status

from main import app

client = TestClient(app)

MD_content = b"""
  Project Kickoff: Website Redesign

## 1. Overview & Objectives
This document outlines the core requirements for the **2026 website redesign**. Our main goal is to improve the user experience while introducing a cleaner visual hierarchy. 
*Note: This project has a hard deadline.*

---

## 2. Key Requirements

### Core Features
*   **Responsive Layout:** Must work on mobile, tablet, and desktop.
*   **Dark Mode:** A native toggle for system-wide preferences.
*   **Speed Optimization:** Pages must load in under *1.5 seconds*.

### Phase 1 Tasks
1.  Finalize the wireframes.
2.  Select the updated color palette.
3.  Set up the staging repository on [GitHub](https://github.com).

---

## 3. Reference Material

### Priority Levels

| Feature | Urgency | Assignee |
| :--- | :---: | :--- |
| Mobile Navigation | High | Sarah |
| User Profile Page | Medium | Alex |
| Footer Links | Low | Unassigned |

### Code Snippet for Theme Toggle
```javascript
// Function to switch site themes
function toggleTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
}
```

> [!NOTE]
> Ensure all image assets are fully optimized using modern WebP formats before uploading them to the server.
"""
MD_content_str = MD_content.decode()

error_responses = {
    "Invalid Markdown": {"status": "error", "detail": "File must be a markdown file."},
    "Decode Error": {
        "status": "error",
        "detail": "Trouble decoding markdown file, try using UTF-8 compliant characters.",
    },
    "No File": {"status": "error", "detail": "File does not exist"},
}


@pytest.fixture
def temp_markdown_file(tmp_path, monkeypatch):
    """Changes Markdown directory from markdown_dir to tmp_path for testing"""
    monkeypatch.setattr("main.markdown_dir", tmp_path)

    return tmp_path


@pytest.fixture
def mock_language_tool(mocker):
    """Mocks the language tool grammar checker"""
    mock_tool = mocker.MagicMock()
    mock_tool.check.return_value = []
    mocker.patch.dict("main.tools", {"language_tool": mock_tool})

    return mock_tool


def test_check_endpoint_rejects_non_markdown_files():
    file_content = b""
    file_name = "idk.txt"
    content_type = "text/plain"

    mock_file = io.BytesIO(file_content)
    response = client.post(
        "/check", files={"file": (file_name, mock_file, content_type)}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == error_responses["Invalid Markdown"]


def test_check_endpoint_accepts_markdown_file(mock_language_tool):
    file_name = "README.md"
    content_type = "text/markdown"
    mock_file = io.BytesIO(b"Idk")

    response = client.post(
        "/check", files={"file": (file_name, mock_file, content_type)}
    )

    mock_language_tool.check.assert_called_once()
    assert response.status_code == status.HTTP_200_OK
    assert response.json() != error_responses["Invalid Markdown"]


def test_check_endpoint_returns_an_error_with_no_file(mock_language_tool):
    response = client.post("/check")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_save_endpoint_with_valid_input(temp_markdown_file):
    MD_content_hash = abs(hash(MD_content_str))

    response = client.post("/save", content=MD_content_str)

    assert len(list(temp_markdown_file.iterdir())) == 1
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"file_name": MD_content_hash}


def test_save_endpoint_with_empty_input(temp_markdown_file):
    content = ""
    response = client.post("/save", content=content)

    assert len(list(temp_markdown_file.iterdir())) == 0
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_save_endpoint_with_non_utf8_characters(temp_markdown_file):
    # Invalid utf-8 text
    content = b"\xff"

    response = client.post("/save", content=content)

    assert len(list(temp_markdown_file.iterdir())) == 0
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == error_responses["Decode Error"]


def test_note_endpoint_with_no_saved_notes(temp_markdown_file):
    response = client.get("/notes")

    assert response.json() == {"detail": "No notes saved yet..."}
    assert response.status_code == status.HTTP_200_OK


def test_note_endpoint_with_saved_notes(temp_markdown_file):
    # Create a fake file in the tmp_dir
    filename = "random.MD"
    md = temp_markdown_file / filename
    md.write_text("Random text")

    notes = {"name": filename}
    count = 1

    response = client.get("/notes")

    assert response.json() == {"count": count, "notes": [notes]}
    assert response.status_code == status.HTTP_200_OK


def test_notes_filename_endpoint_returns_html_with_saved_file(temp_markdown_file):
    filename = "README"
    md_file = temp_markdown_file / f"{filename}.md"
    md_file.write_text(MD_content_str)

    with open(md_file) as f:
        md = f.read()
        html_md = markdown.markdown(md)

    response = client.get(f"note/{filename}")

    assert response.status_code == status.HTTP_200_OK
    assert response.text == html_md


def test_notes_filename_endpoint_with_empty_markdown_file(temp_markdown_file):
    filename = "Random"

    md_file = temp_markdown_file / f"{filename}.md"
    md_file.write_text("")

    response = client.get(f"note/{filename}")
    assert response.status_code == status.HTTP_200_OK
    assert response.text == ""


def test_notes_filename_endpoint_returns_an_error_with_a_file_that_does_not_exist(
    temp_markdown_file,
):
    filename = "README"

    response = client.get(f"note/{filename}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == error_responses["No File"]
