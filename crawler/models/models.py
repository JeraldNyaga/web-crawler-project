"""
Pydantic models for book data validation.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, HttpUrl
import hashlib
import json



