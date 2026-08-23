"""
Thin wrapper around the Neo4j driver, reading connection info from .env.
"""
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


def get_driver():
    uri = os.environ["NEO4J_URI"]
    username = os.environ["NEO4J_USERNAME"]
    password = os.environ["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(username, password))


def verify_connection():
    driver = get_driver()
    driver.verify_connectivity()
    driver.close()
    print("Neo4j connection OK")