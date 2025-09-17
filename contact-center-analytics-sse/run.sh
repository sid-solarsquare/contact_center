#!/bin/bash
uvicorn backend.api:app --reload &
cd frontend && python -m http.server
