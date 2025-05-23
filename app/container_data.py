from typing import List, Optional, Literal, Union
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field, RootModel
from enum import Enum
import json

# Define models
class ContainerType(str, Enum):
    HH42 = "HH42"
    HH24 = "HH24"
    HH12 = "HH12"

class ContainerCount(BaseModel):
    type: ContainerType
    count: int = Field(ge=0, description="Number of containers (must be >= 0)")

class ContainerRequest(BaseModel):
    containers: List[ContainerCount]

# Create FastAPI app
app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/container-check")
async def container_check(request: Request):
    try:
        # Log raw request body
        body = await request.body()
        print(f"Raw request body: {body.decode()}")
        
        # Parse and validate the request
        try:
            data = await request.json()
            print(f"Parsed JSON data: {json.dumps(data, indent=2)}")
            
            # Convert to our model
            validated_data = ContainerRequest.model_validate(data)
            print(f"Validated data: {validated_data.model_dump_json(indent=2)}")
            
        except Exception as e:
            print(f"Validation error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")

        # Check if we have at least one container type with count > 0
        has_containers = any(container.count > 0 for container in validated_data.containers)
        
        # Validate container types
        container_types = {container.type for container in validated_data.containers}
        valid_types = {ContainerType.HH42, ContainerType.HH24, ContainerType.HH12}
        invalid_types = container_types - valid_types
        
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid container types: {', '.join(invalid_types)}. Valid types are: {', '.join(valid_types)}"
            )
        
        if not has_containers:
            raise HTTPException(
                status_code=400,
                detail="At least one container type must have a count greater than 0"
            )

        # Calculate totals
        totals = {
            container.type: container.count
            for container in validated_data.containers
        }
        
        # Add missing container types with count 0
        for container_type in valid_types:
            if container_type not in totals:
                totals[container_type] = 0

        return {
            "data": {
                "valid": True,
                "message": "Container configuration is valid",
                "totals": totals,
                "has_containers": has_containers
            }
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 