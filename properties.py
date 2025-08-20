from typing import List, Optional
import json


class Property:
    def __init__(self,
                 id: int,
                 location: str,
                 type: str,
                 price_per_night: float,
                 environment: str,
                 features: List[str],
                 tags: List[str],
                 booked: List[dict]):
        self.id = id
        self.location = location
        self.type = type
        self.price_per_night = price_per_night
        self.environment = environment
        self.features = features
        self.tags = tags
        self.booked = booked

    def __repr__(self):
        return (f"Property(id={self.id}, location='{self.location}', "
                f"type='{self.type}', price_per_night={self.price_per_night}, "
                f"environment='{self.environment}', features={self.features}, "
                f"tags={self.tags}, booked={self.booked})")

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            location=data.get("location"),
            type=data.get("type"),
            price_per_night=data.get("price_per_night"),
            environment=data.get("environment"),
            features=data.get("features", []),
            tags=data.get("tags", []),
            booked=data.get("booked", [])
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location": self.location,
            "type": self.type,
            "price_per_night": self.price_per_night,
            "environment": self.environment,
            "features": self.features,
            "tags": self.tags,
            "booked": self.booked
        }


class PropertiesController:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.properties: List[Property] = []
    
    def load_properties(self):
        with open(self.json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.properties = [Property.from_dict(item) for item in data]

    def get_all(self) -> List[Property]:
        return self.properties

    def find_by_id(self, property_id: int) -> Optional[Property]:
        for prop in self.properties:
            if prop.id == property_id:
                return prop
        return None
