# Start here

1. Extract this ZIP once. Do not zip it again.
2. Open the extracted `placement-tracker` folder in VS Code.
3. Click Terminal → New Terminal.
4. Run `py seed_demo.py` if you want fictional demo applications.
5. Run `py server.py` and open http://127.0.0.1:8001.
6. Click New application, add an opportunity and save it.
7. Edit its stage, then open Stage history to see the change.
8. Run `py -m unittest discover -v` in a second terminal.

## GitHub

Create a public repository named `placement-application-tracker`. Upload the CONTENTS of this folder directly into the repository root, including `.github` and `.gitignore`. Do not upload the outer folder, ZIP, `__pycache__` or `applications.db` files. The CI file already assumes the source files are at the root.

If you upload an outer folder instead, the workflow needs moving to the repository's root `.github/workflows/ci.yml` and a working-directory setting pointing to the source folder.

Record a screenshot of the running app, upload it as `demo.png` beside README.md, and add `![Application tracker dashboard](demo.png)` below the README opening description.

## Make this your own work

Use it for your actual placement search. Write down what is annoying or missing, then implement a feature that addresses it. Start with a follow-up date: it differs from a closing deadline and helps you decide when to contact a company. Be able to explain the validation, database transaction and stale-edit protection before mentioning them in an interview.

Do not invent origin stories, adoption numbers or claims that all code was written unaided. A repository name cannot hide AI involvement. Meaningful development and understanding are the evidence you can contribute.
