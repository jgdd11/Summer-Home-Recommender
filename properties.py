from typing import List
import json


class Property:
    def __init__(self,
                 id: int,
                 location: str,
                 type: str,
                 price: float,
                 capacity: int,
                 features: List[str],
                 tags: List[str]):
        self.id = id
        self.location = location
        self.type = type
        self.price = price
        self.capacity = capacity
        self.features = features
        self.tags = tags

    # easy for printing, and debugging
    def __repr__(self):
        return (f"Property(id={self.id}, location='{self.location}', "
                f"type='{self.type}', price={self.price}, capacity={self.capacity}, "
                f"features={self.features}, tags={self.tags})")

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id"),
            location=data.get("location"),
            type=data.get("type"),
            price=data.get("price"),
            capacity=data.get("capacity"),
            features=data.get("features", []),
            tags=data.get("tags", [])
        )

    # convert property object into a python dictionary
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "location": self.location,
            "type": self.type,
            "price": self.price,
            "capacity": self.capacity,
            "features": self.features,
            "tags": self.tags
        }


class PropertiesController:
    def __init__(self, json_file: str):
        self.json_file = json_file
        self.properties: List[Property] = []

    # load all properties from json_file which store record of all properties
    def load_properties(self):
        with open(self.json_file, "r") as f:
            data = json.load(f)
            self.properties = [Property.from_dict(item) for item in data]

    def update_properties(self):
        pass

    # get all properties in a list
    def get_all(self) -> List[Property]:
        return self.properties

    # select properties based on id
    def find_by_id(self, property_id: int) -> Property | None:
        for prop in self.properties:
            if prop.id == property_id:
                return prop
        # if cannot find corresponding id, return None
        return None
