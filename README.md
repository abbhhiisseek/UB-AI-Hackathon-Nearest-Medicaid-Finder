# AI-Powered Closest Medicaid Finder

## Inspiration
Finding the right insurance and doctors can be a daunting task. By integrating AI into the process, we aimed to simplify this challenge. Users will be matched with in-network doctors and understand complex policies easily just by typing their questions.

## What We Learned
- **AI Integration**: We learned how to work with Langchain and Google Gemini API to generate structured outputs from natural language inputs.
- **FastAPI**: This framework helped us build web services efficiently.
- **NY Gov Health Data API**: This API helped us retrieve large volumes of live doctor data.
- **Cloud Deployment**: Using Google Cloud, we gained insight into deploying scalable applications and working with real-time APIs like Google Geocoding and Distance Matrix APIs.
- **Handling Data**: Implementing pagination taught us how to handle large datasets more efficiently for a better user experience.

## How We Built It
- **Frontend**: Built with HTML, CSS, and JavaScript to collect user symptoms and display relevant doctors in paginated views.
- **Backend**: FastAPI handles user input and integrates with the Google Gemini API for symptom analysis.
- **AI-Driven Symptom Analysis**: The Langchain template structures user input into prompts for AI to analyze and suggest medical services or specialties.
- **Distance Calculation**: Using the Google Distance Matrix API, the platform calculates the distance between doctors' offices and the user's location and orders results by proximity.
- **New York Health Data Integration**: Leveraged the New York State Department of Health.
- **Deployment**: The project was deployed on Google App Engine for better scalability and flexibility.

## Challenges We Faced
- **Structuring AI Outputs**: Ensuring AI-generated JSON was consistent required tuning and refining prompts.
- **Cloud Deployment Issues**: Debugging deployment on GCP was tricky, especially with configuring gunicorn and uvicorn.
- **Geolocation Data**: Handling incomplete address data for geolocation and distance calculation was a major challenge.
- **Pagination**: Implementing smooth pagination for large datasets was critical to maintain a clean and responsive UI.

## Conclusion
This project combines the power of AI and cloud technologies to simplify the process of finding the right in-network doctors and understanding complex policy documents easily. There are multiple scopes for improvement, including implementing corrective and adaptive RAG for insurance simplification.

## Built With
- gemini-api
- google-cloud
- google-distance-matrix
- google-geocoding
- health.data.ny.gov-api
- langchain

## Try it out
[mapit-163714.uc.r.appspot.com](http://mapit-163714.uc.r.appspot.com)
