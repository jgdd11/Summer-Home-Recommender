from typing import List, Optional
import json
from datetime import date, timedelta


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
                 booked: List[dict]):
        self.id = id
        self.location = location
        self.type = type
        self.price = price
        self.capacity = capacity
        self.environment = environment
        self.features = features
        self.tags = tags
        self.booked = booked

    def __repr__(self):
        return (f"Property(id={self.id}, location='{self.location}', "
                f"type='{self.type}', price={self.price}, capacity={self.capacity}"
                f"environment='{self.environment}', features={self.features}, "
                f"tags={self.tags}, booked={self.booked})")

    @classmethod
    def to_dict(self):
        return {
            "id": self.id,
            "location": self.location,
            "type": self.type,
            "price": self.price,
            "capacity": self.capacity,
            "environment": self.environment,
            "features": self.features,
            "tags": self.tags,
            # convert each date to ISO string
            "booked": [d.isoformat() for d in self.booked]
        }
    
    def add_dates(self, start_date: date, end_date: date):
        """Add all dates from start_date to end_date to self.booked."""
        for i in range((end_date - start_date).days + 1):
            day = start_date + timedelta(days=i)
            if day not in self.booked:
                self.booked.append(day)
        print(f"Booked dates added: {[start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]}")

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
    
    def load_properties(self):
        try:
            with open(self.json_file, "r") as f:
                data = json.load(f)
                return [Property(**p) for p in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_all(self) -> List[Property]:
        return self.properties

    def find_by_id(self, property_id: int) -> Optional[Property]:
        for prop in self.properties:
            if prop.id == property_id:
                return prop
        return None

    def save_properties(self):
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump([prop.to_dict() for prop in self.properties], f, indent=4)

