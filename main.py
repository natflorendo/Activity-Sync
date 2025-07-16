# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel;

app = FastAPI()

items = []

class Item(BaseModel):
    id: int
    name: str
    description: str

@app.post("/items/")
def create_item(item: Item):
    items.append(item)
    return item

@app.get("/items/")
def read_items():
    return items

@app.get("/items/{item_id}")
def read_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item
    return HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}")
def update_item(item_id: int, updated_item: Item):
    for i, existing_item in enumerate(items):
        if existing_item.id == item_id:
            items[i] = updated_item
            return updated_item
    return HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    for i, item in enumerate(items):
        if item.id == item_id:
            deleted = items.pop(i)
            return {"deleted": deleted}
    return HTTPException(status_code=404, detail="Item not found")
