type QueryInput = Pick<URLSearchParams, "get"> | null | undefined;

type QueryOverrides = {
  projectId?: string | null;
  sf_token?: string | null;
};

const ALLOWED_QUERY_KEYS = ["projectId", "sf_token"] as const;

export function getAllowedQueryParams(
  searchParams: QueryInput,
  overrides: QueryOverrides = {}
): URLSearchParams {
  const nextParams = new URLSearchParams();

  ALLOWED_QUERY_KEYS.forEach((key) => {
    const value = searchParams?.get(key);
    if (value) {
      nextParams.set(key, value);
    }
  });

  Object.entries(overrides).forEach(([key, value]) => {
    if (!ALLOWED_QUERY_KEYS.includes(key as (typeof ALLOWED_QUERY_KEYS)[number])) {
      return;
    }

    if (value) {
      nextParams.set(key, value);
    } else {
      nextParams.delete(key);
    }
  });

  return nextParams;
}

export function buildAllowedQueryHref(
  pathname: string,
  searchParams: QueryInput,
  overrides: QueryOverrides = {}
): string {
  const params = getAllowedQueryParams(searchParams, overrides);
  const queryString = params.toString();

  return queryString ? `${pathname}?${queryString}` : pathname;
}
