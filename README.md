# Exam Depository

This is a sample backend project for collecting student exam answers. 

You can play with the API in production at https://exam-depository.fly.dev/docs
For demonstration purposes, you can obtain the API key from the appropriate route, see the documentation at the link above.

Any files you upload to the service will be stored in the EU and automatically deleted 3 days after upload.


## How to run for local development

1. Rename the .envrc-example to .envrc and specify values for environment variables
2. Load environment variables use `direnv allow` in the project's directory
3. Make sure that you have python and poetry installed with `asdf install`
3. Install project dependencies with `make deps`
4. Start PostgreSQL container with `make postgres_up`
5. Migrate database with `make migrate_up`
6. Run tests with `make tests`, run server with `make server`


## Deployment

A push to the `master` branch will automatically deploy the version of the app to Fly.io via the Github workflow.


## Architecture Canvas

### Value proposition

The application persists students exam submissions and serves the submitted files for examiners to review the answers.


### Key Stakeholder

Authenticated examainers and unauthenticated students.


### Core Functions

* Creates students and issues appropriate upload code to accept submissions
* Persists uploaded submission file and issues appropriate verification code
* Limits the size of a submission file to a maximum of 3MB
* Supports resubmission up to 5 times per student, automatically deletes previously persisted file
* Serves the earlier uploaded file for verification by verification code (no authorisation required)


### Quality Requirements

* Scalability to handle peak loads
* Cost-effective performance maintenance strategies
* Good security practices to protect data and prevent unauthorised actions


### Business Context

* The application persists files on AWS S3 compatible data storage (Cloudflare R2)
* Uses PostgreSQL database to store list of students and submissions


### Core Decisions

+ Using Fly.io to host the application on free tier plan
+ Use CI/CD pipeline with GitHub Actions for deployment
- API key available through endpoint route


### Technologies

* Language: Python
* Web API: FastAPI, uvicorn
* Persistance: SQLAlchemy, boto3
* PostgreSQL, R2 for data storage
* Github Actions for deployment
* Fly.io for hosting


### Components/Modules

* Schema:

```
+-------------+    +------------+
| Application |----| PostgreSQL |
+-------------+    +------------+
           |       +---------------+
           --------| Cloudflare R2 |
                   +---------------+
```

* Main  Routes:

| Method | Path | Purpose | Authentication? |
| ------ | ---- | ------- | -------------- |
| GET | /strudents | Shows list of students and their submissions | Yes |
| POST | /student | Creates a student | Yes |
| POST | /submissions/{upload_code} | Uploads a submission file | No |
| GET | /verifications/{verification_code}/download_url | Returns an URL to download the submission file | No |

### Risks and Missing Information

* No route to bulk add student records with a CSV file, which can be added as needed
* The application exposes the API key through one of the routes that should be removed for production

## Copyright

Copyright © 2024 Ivan Rublev.

This project is licensed under the [MIT license](https://github.com/IvanRublev/Domo/blob/master/LICENSE.md).
