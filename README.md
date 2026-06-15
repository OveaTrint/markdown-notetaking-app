# Markdown REST API With FastAPI

## An API written with FastAPI that performs operations on Markdown files and Markdown texts.

This project is a RESTful API developed that performs the following operations:

* Checks the grammar of a Markdown and returns the grammatical errors, if any
* Saves a Markdown note passed as a text
* Lists all saved Markdown notes
* Displays a Markdown note in HTML format.

This project was inspired by [roadmap.sh](https://roadmap.sh/projects/markdown-note-taking-app)

### Endpoints

* `/check`
    * Method: `POST`
    * **Description**: Checks the grammar of your Markdown file and returns the related errors. Only accepts Markdown
      files as Input.
* `/save`
    * Method: `POST`
    * **Description**: Saves a text passed as a Markdown file

* `/notes`
    * Method: `GET`
    * **Description**: Lists all the saved notes

* `/note/{filename}`
    * Method: `GET`
    * **Description**: Displays the requested Markdown File in an HTML format

### How to Install

Make sure you have uv installed on your PC.

* Clone the repository
    * ```bash
        git clone https://github.com/OveaTrint/markdown-notetaking-app.git 
        cd markdown-notetaking-app/
        ```

* Sync the dependencies
    * ```bash
        uv sync
        ```

* Start the server
    * ```bash
        uvicorn main:app --reload
        ```
* Start making requests
    * ```bash
        // check the grammar of a Markdown file
        curl -X POST -F "file=@/path/to/Markdown" localhost:8000/check
        
        //save a note
        curl -X POST -d "Hello, World" localhost:8000/save
      
        // lists all saved notes
        curl localhost:8000/notes
      
        // Display a saved note in HTML format
        curl localhost:8000/note/filename
        ```

## Tests

This project also includes tests that test the functionality of each endpoint.
