from pymongo import MongoClient

# Replace the following URI with your actual connection string
uri = "mongodb+srv://Ashwanth:MRy1ZkgQSrm3NVE2@atlascluster.mongodb.net/<database>"

try:
    client = MongoClient(uri)
    db = client['ecommerce']  # Replace '<database>' with your database name
    print("Database connection successful!")
except Exception as e:
    print("Database connection failed:", str(e))
