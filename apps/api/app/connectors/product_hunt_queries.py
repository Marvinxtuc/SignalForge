from __future__ import annotations

from typing import Any


PRODUCT_HUNT_GRAPHQL_ENDPOINT = "https://api.producthunt.com/v2/api/graphql"
PRODUCT_HUNT_GRAPHQL_URL = PRODUCT_HUNT_GRAPHQL_ENDPOINT
DEFAULT_POSTS_FIRST = 25
DEFAULT_COMMENTS_FIRST = 5
MAX_POSTS_FIRST = 100
MAX_COMMENTS_FIRST = 25


def build_posts_search_query(
    *,
    keywords: list[str],
    first: int | None = None,
    comments_first: int | None = None,
) -> dict[str, Any]:
    normalized_first = _bounded_int(
        first,
        default=DEFAULT_POSTS_FIRST,
        minimum=1,
        maximum=MAX_POSTS_FIRST,
    )
    normalized_comments_first = _bounded_int(
        comments_first,
        default=DEFAULT_COMMENTS_FIRST,
        minimum=0,
        maximum=MAX_COMMENTS_FIRST,
    )
    return {
        "query": """
query SignalForgeProductHuntPosts($first: Int!, $commentsFirst: Int!) {
  posts(first: $first) {
    edges {
      node {
        id
        slug
        name
        tagline
        description
        url
        website
        votesCount
        commentsCount
        createdAt
        user {
          id
          username
          name
        }
        comments(first: $commentsFirst) {
          edges {
            node {
              id
              body
              url
              createdAt
              user {
                id
                username
                name
              }
            }
          }
        }
      }
    }
  }
}
""".strip(),
        "variables": {
            "first": normalized_first,
            "commentsFirst": normalized_comments_first,
        },
    }


def build_product_lookup_query(
    *,
    slug: str,
    comments_first: int | None = None,
) -> dict[str, Any]:
    normalized_comments_first = _bounded_int(
        comments_first,
        default=DEFAULT_COMMENTS_FIRST,
        minimum=0,
        maximum=MAX_COMMENTS_FIRST,
    )

    return {
        "query": """
query SignalForgeProductHuntProduct($slug: String!, $commentsFirst: Int!) {
  product(slug: $slug) {
    id
    slug
    name
    tagline
    description
    url
    website
    posts(first: 10) {
      edges {
        node {
          id
          slug
          name
          tagline
          description
          url
          votesCount
          commentsCount
          createdAt
          comments(first: $commentsFirst) {
            edges {
              node {
                id
                body
                url
                createdAt
              }
            }
          }
        }
      }
    }
  }
}
""".strip(),
        "variables": {
            "slug": slug.strip(),
            "commentsFirst": normalized_comments_first,
        },
    }


def _bounded_int(
    value: int | None,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    if value is None:
        return default
    return min(max(value, minimum), maximum)


build_product_hunt_posts_query = build_posts_search_query
build_product_hunt_product_query = build_product_lookup_query


__all__ = [
    "PRODUCT_HUNT_GRAPHQL_ENDPOINT",
    "PRODUCT_HUNT_GRAPHQL_URL",
    "build_product_hunt_posts_query",
    "build_product_hunt_product_query",
    "build_posts_search_query",
    "build_product_lookup_query",
]
