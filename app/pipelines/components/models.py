from pydantic import BaseModel, Field


class ImageDescription(BaseModel):
    image_description: str = Field(description="Description of input image")
