import os
import hashlib
import json
import redis
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=2,
    decode_responses=True,
    socket_timeout=2,
    socket_connect_timeout=2,
)

EMBEDDING_TTL = 60 * 60 * 24 * 7
ANSWER_TTL = 60 * 60


# for cache invalidation on document changes

def get_doc_version(doc_id: str | None) -> str:
    if doc_id is None:
        return "0"
    try:
        version = redis_client.get(f"docver:{doc_id}")
        return version if version else "0"
    except redis.RedisError:
        return "1"


def bump_doc_version(doc_id: str) -> None:
    try:
        redis_client.incr(f"docver:{doc_id}")
    except redis.RedisError as e:
        print(f"Redis version bump failed: {e}")


def make_key(prefix:str, value:str):
    normalised = value.strip().lower()
    digest = hashlib.sha256(normalised.encode()).hexdigest()
    return f"{prefix}:{digest[:32]}"


# Embedding Cache Section
def get_cached_embedding(text:str):
    key = make_key("embed", text)
    try:
        raw = redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except redis.RedisError as e:
        print(f"Redis read failed: {e}")
        return None
    
def set_cached_embedding(text:str, vector: list[float]):
    key = make_key("embed", text)
    try:
        redis_client.set(key, json.dumps(vector), ex=EMBEDDING_TTL)
    except redis.RedisError as e:
        print(f"Redis write failed: {e}")
        
        
# Caching Answer section

def make_answer_key(question: str, n_results: int, max_distance: float, doc_id) -> str:
    payload = json.dumps(
        {
            "question": question.strip().lower(),
            "n_results": n_results,
            "max_distance": max_distance,
            "doc_id": doc_id,
            "version": get_doc_version(doc_id),
        },
        sort_keys=True,
    )
    return make_key("answer", payload)


def get_cached_answer(question: str, n_results: int, max_distance: float, doc_id) -> dict | None:
    key = make_answer_key(question, n_results, max_distance, doc_id)
    try:
        raw = redis_client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except redis.RedisError as e:
        print(f"Redis read failed: {e}")
        return None


def set_cached_answer(question: str, n_results: int, max_distance: float, result: dict, doc_id) -> None:
    key = make_answer_key(question, n_results, max_distance, doc_id)
    try:
        redis_client.set(key, json.dumps(result), ex=ANSWER_TTL)
    except redis.RedisError as e:
        print(f"Redis write failed: {e}")