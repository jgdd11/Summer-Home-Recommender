from typing import List, Optional
import json
from datetime import date, timedelta, datetime


class Property:
    def __init__(self,
                 id: int,
                 location: str,
                 type: str,
                 price: float,
                 capacity: int,
                 environment: str,
                 features: List[str],
                 tags: List[str],
                 booked: List[date] = None):
        self.id = id
        self.location = location
        self.type = type
        self.price = price
        self.capacity = capacity
        self.environment = environment
        self.features = features
        self.tags = tags
        self.booked = booked or []

    # easy for printing, and debugging
    def __repr__(self):
        return (f"Property(id={self.id}, location='{self.location}', "
                f"type='{self.type}', price={self.price}, capacity={self.capacity}, "
                f"environment='{self.environment}', features={self.features}, "
                f"tags={self.tags}, booked={self.booked})")
   
  
    def to_dict(self):
        """Convert to dict for JSON serialization."""
        return {
            "id": self.id,
            "location": self.location,
            "type": self.type,
            "price": self.price,
            "capacity": self.capacity,
            "environment": self.environment,
            "features": self.features,
            "tags": self.tags,
            "booked": [d.isoformat() for d in self.booked]
        }

    @classmethod
    def from_dict(cls, data):
        """Create Property instance from dict (JSON load)."""
        booked_dates = [datetime.fromisoformat(d).date() for d in data.get("booked", [])]
        return cls(
            id=data["id"],
            location=data["location"],
            type=data["type"],
            price=data["price"],
            capacity=data["capacity"],
            environment=data["environment"],
            features=data.get("features", []),
            tags=data.get("tags", []),
            booked=booked_dates
        )

    def add_dates(self, start_date: date, end_date: date):
        """Add all dates from start_date to end_date to self.booked."""
        for i in range((end_date - start_date).days):
            day = start_date + timedelta(days=i)
            if day not in self.booked:
                self.booked.append(day)
        print(f"Booked dates added: {[start_date + timedelta(days=i) for i in range((end_date - start_date).days)]}")

    def delete_dates(self, start_date: date, end_date: date):
        """Remove all dates in the given range from self.booked."""
        dates_to_remove = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
        removed_dates = [d for d in dates_to_remove if d in self.booked]
        self.booked = [d for d in self.booked if d not in dates_to_remove]

        if removed_dates:
            print(f"Booked dates removed: {removed_dates}")
        else:
            print("No matching booked dates to remove.")


class PropertiesController:
    def __init__(self):
        self.json_file = "properties.json"
        self.properties = self.load_properties()

    # load all properties from json_file which store record of all properties
    def load_properties(self) -> List[Property]:
        try:
            with open(self.json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [Property.from_dict(p) for p in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    # get all properties in a list
    def get_all(self) -> List[Property]:
        return self.properties

    # select properties based on id
    def find_by_id(self, property_id: int) -> Optional[Property]:
        for prop in self.properties:
            if prop.id == property_id:
                return prop
        return None
        
    # save properties into the json file
    def save_properties(self):
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump([prop.to_dict() for prop in self.properties], f, indent=4)
