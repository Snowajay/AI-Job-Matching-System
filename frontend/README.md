# AI-Powered Job Matching System - Frontend

This folder contains the React frontend for the AI-Powered Job Matching System.

The frontend allows a candidate to:

- Create and update a candidate profile
- Enter skills
- Enter education
- Enter work experience
- View available jobs
- Find ranked job matches

## Technologies

The frontend uses:

- React
- Vite
- JavaScript
- CSS

The frontend communicates with our FastAPI backend.

## Running the Frontend

Open a terminal and move into the frontend directory:

cd frontend

Install the required packages:

npm install

Start the development server:

npm run dev

Vite will display the local address for the frontend.

## Backend

The FastAPI backend must also be running for the API features to work.

The frontend currently expects the backend at:

http://127.0.0.1:8000

## Current API Features

The frontend communicates with the following backend features:

- Candidate profiles
- Job listings
- Job matching

## Alpha Version

This project is currently an Alpha version.

The candidate ID is temporarily set to:

test-candidate

A future version can replace this with the ID of the authenticated user.