from typing import List, Optional, Literal, Union
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, RootModel
from enum import Enum
import json

# Define models
class CountryEntry(BaseModel):
    id: str
    name: str
    country: str

class Operation(str, Enum):
    GET_ENTRY = "get_entry"
    SEARCH = "search"
    SAME_COUNTRY = "same_country"

class BaseRequest(BaseModel):
    operation: Operation

class GetEntryRequest(BaseRequest):
    operation: Literal[Operation.GET_ENTRY]
    entry_id: str
    search_query: Optional[str] = None
    entry1_id: Optional[str] = None
    entry2_id: Optional[str] = None

class SearchRequest(BaseRequest):
    operation: Literal[Operation.SEARCH]
    search_query: str
    entry_id: Optional[str] = None
    entry1_id: Optional[str] = None
    entry2_id: Optional[str] = None

class SameCountryRequest(BaseRequest):
    operation: Literal[Operation.SAME_COUNTRY]
    entry1_id: str
    entry2_id: str
    entry_id: Optional[str] = None
    search_query: Optional[str] = None

# Use RootModel for the discriminated union
CountryDataRequest = RootModel[Union[GetEntryRequest, SearchRequest, SameCountryRequest]]

# In-memory storage (replace with a database in production)
entries: List[CountryEntry] = [
    CountryEntry(id='US-NYC', name='New York', country='USA'),
    CountryEntry(id='GB-LON', name='London', country='UK'),
    CountryEntry(id='FR-PAR', name='Paris', country='France'),
    CountryEntry(id='US-LAX', name='Los Angeles', country='USA'),
    CountryEntry(id='DE-HAM', name='Hamburg', country='Germany'),
    CountryEntry(id='DE-HRB', name='Hamburg', country='Germany')
]

# Create FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/country-data")
async def country_data(request: Request):
    try:
        # Log raw request body
        body = await request.body()
        print(f"Raw request body: {body.decode()}")
        
        # Parse and validate the request
        try:
            data = await request.json()
            print(f"Parsed JSON data: {json.dumps(data, indent=2)}")
            
            # Convert to our model
            validated_data = CountryDataRequest.model_validate(data)
            print(f"Validated data: {validated_data.model_dump_json(indent=2)}")
            
            data = validated_data.root
        except Exception as e:
            print(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")

        if isinstance(data, GetEntryRequest):
            entry = next((e for e in entries if e.id == data.entry_id), None)
            if not entry:
                raise HTTPException(status_code=404, detail="Entry not found")
            return {"data": entry}

        elif isinstance(data, SearchRequest):
            search_results = [
                e for e in entries
                if data.search_query.lower() in e.name.lower() or
                   data.search_query.lower() in e.country.lower()
            ]
            return {"data": search_results}

        elif isinstance(data, SameCountryRequest):
            entry1 = next((e for e in entries if e.id == data.entry1_id), None)
            entry2 = next((e for e in entries if e.id == data.entry2_id), None)
            
            if not entry1 or not entry2:
                raise HTTPException(status_code=404, detail="One or both entries not found")
            
            return {
                "data": {
                    "same_country": entry1.country == entry2.country,
                    "entry1_country": entry1.country,
                    "entry2_country": entry2.country
                }
            }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 