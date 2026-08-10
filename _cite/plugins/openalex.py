import os
import re
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from util import *


# openalex api
endpoint = "https://api.openalex.org/works"

# max page size openalex allows
per_page = 200

# safety cap on pagination (per_page * max_pages works)
max_pages = 25

# only fetch the fields we actually use, to keep responses small
select = ",".join(
    [
        "id",
        "doi",
        "ids",
        "display_name",
        "type",
        "publication_date",
        "authorships",
        "primary_location",
        "best_oa_location",
    ]
)

# openalex "field" ids worth defaulting a name search to, so that an
# unrelated researcher who happens to share a name doesn't drag in their work
default_fields = [17, 22]  # computer science, engineering

# entry keys that configure this plugin, and so shouldn't be copied onto sources
config_keys = {
    "author",
    "name-search",
    "fields",
    "from-year",
    "to-year",
    "types",
    "exclude-types",
    "require-doi",
    "require-coauthor",
    "lead-author",
    "dedupe-versions",
}


def name_tokens(name):
    """
    reduce a name to comparable lowercase tokens, dropping nicknames in
    parentheses, punctuation, and single-letter middle initials
    """

    name = re.sub(r"\([^)]*\)", " ", name or "")
    name = re.sub(r"[^A-Za-z\s-]", " ", name).lower()
    return [t for t in name.split() if len(t) > 1]


def names_match(a, b):
    """
    compare two token lists, tolerating the ways openalex mangles names
    """

    if not a or not b:
        return False

    # openalex sometimes inverts to "Family, Given", so compare unordered
    if {a[0], a[-1]} == {b[0], b[-1]}:
        return True

    # ...and sometimes truncates a surname, e.g. "Marius Memme" for "Memmel"
    if a[0] == b[0]:
        long, short = sorted([a[-1], b[-1]], key=len, reverse=True)
        if len(short) >= 4 and long.startswith(short):
            return True

    return False


def load_roster():
    """
    every name associated with the lab: current members, alumni, and the
    supplementary list in allowed_authors.yaml (which is also where publishing
    names that differ from the site's spelling belong)
    """

    names = []

    for path in Path.cwd().glob("_members/*.md"):
        text = path.read_text(encoding="utf8")
        match = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
        if not match:
            continue
        found = re.search(r"^name:\s*(.+)$", match.group(1), re.MULTILINE)
        if found:
            names.append(found.group(1).strip())

    for path in ["_data/alumni.yaml", "_data/allowed_authors.yaml"]:
        if not Path(path).is_file():
            continue
        for entry in load_data(path) or []:
            name = entry.get("name", "") if isinstance(entry, dict) else entry
            if isinstance(name, str) and name.strip():
                # alumni are stored as "Name (Degree, Year, Where)". strip only
                # the trailing group, so a nickname earlier in the name survives
                # e.g. "Qiuyu (Zoey) Chen (PhD, 2024)" -> "Qiuyu (Zoey) Chen"
                names.append(re.sub(r"\s*\([^()]*\)\s*$", "", name).strip())

    return [t for t in (name_tokens(n) for n in names) if t]


def main(entry):
    """
    receives single list entry from openalex data file
    returns list of sources to cite
    """

    # get author ids from entry, tolerating a single id and full openalex urls
    authors = get_safe(entry, "author", None) or []
    if not isinstance(authors, list):
        authors = [authors]
    ids = [str(a).strip().rstrip("/").split("/")[-1] for a in authors]
    ids = [i for i in ids if i]

    # optional free-text author name to search for
    name_search = str(get_safe(entry, "name-search", "") or "").strip()

    if not ids and not name_search:
        raise Exception('No "author" or "name-search" key')

    # optional filters
    from_year = get_safe(entry, "from-year", None)
    to_year = get_safe(entry, "to-year", None)
    types = get_safe(entry, "types", None)
    exclude_types = get_safe(entry, "exclude-types", None) or []
    require_doi = get_safe(entry, "require-doi", False) == True
    require_coauthor = get_safe(entry, "require-coauthor", False) == True
    lead_author = name_tokens(get_safe(entry, "lead-author", "") or "")
    dedupe_versions = get_safe(entry, "dedupe-versions", True) != False

    if require_coauthor and not lead_author:
        raise Exception('"require-coauthor" needs a "lead-author" to check against')

    # date range applies to every query (type filtering is done locally)
    common = []
    if from_year:
        common.append(f"from_publication_date:{from_year}-01-01")
    if to_year:
        common.append(f"to_publication_date:{to_year}-12-31")

    # identify ourselves to get into openalex's faster "polite pool"
    email = os.environ.get("OPENALEX_EMAIL", "")

    def build(filters):
        params = {
            "filter": ",".join(filters + common),
            "per-page": per_page,
            "select": select,
        }
        if email:
            params["mailto"] = email
        return f"{endpoint}?{urlencode(params)}"

    # openalex regularly splits one researcher across several author records,
    # and brand new papers often land on a freshly created one. So query every
    # known id at once, and optionally sweep by raw author name to catch works
    # sitting on a record we haven't been told about yet.
    urls = []
    if ids:
        urls.append(build([f"author.id:{'|'.join(ids)}"]))
    if name_search:
        filters = [f"raw_author_name.search:{name_search}"]
        fields = get_safe(entry, "fields", default_fields)
        if fields:
            filters.append(
                "primary_topic.field.id:" + "|".join(f"fields/{f}" for f in fields)
            )
        urls.append(build(filters))

    # query api
    @log_cache
    @cache.memoize(name=__file__, expire=1 * (60 * 60 * 24))
    def query(url):
        works = []
        cursor = "*"
        for _ in range(max_pages):
            request = Request(url=f"{url}&cursor={cursor}", headers={"Accept": "application/json"})
            response = json.loads(urlopen(request).read())
            results = get_safe(response, "results", [])
            if not results:
                break
            works += results
            cursor = get_safe(response, "meta.next_cursor", None)
            if not cursor:
                break
        return works

    # run every query and merge, keyed by openalex work id to drop the overlap
    merged = {}
    for url in urls:
        for work in query(url):
            merged[get_safe(work, "id", "")] = work
    works = list(merged.values())

    # filter by work type
    if types:
        works = [w for w in works if get_safe(w, "type", "") in types]
    if exclude_types:
        works = [w for w in works if get_safe(w, "type", "") not in exclude_types]

    # the lead author may hold appointments outside the lab, so optionally keep
    # only work they did with someone else from the lab
    if require_coauthor:
        roster = load_roster()
        before = len(works)
        works = [w for w in works if lab_work(w, lead_author, roster)]
        log(
            f"Dropped {before - len(works)} work(s) without a lab co-author",
            indent=3,
        )

    # openalex indexes a preprint and its published version as separate works,
    # so collapse them down to the most "final" version of each title
    if dedupe_versions:
        works = dedupe(works)

    # list of sources to return
    sources = []

    # fields from entry to copy onto every source (e.g. shared tags)
    shared = {k: v for k, v in entry.items() if k not in config_keys}

    for work in works:
        source = to_source(work)

        # skip works Manubot can't cite, if asked to
        if require_doi and not get_safe(source, "id", ""):
            continue

        # copy fields from entry to source
        source.update(shared)

        sources.append(source)

    return sources


def lab_work(work, lead_author, roster):
    """
    true if the lead author appears alongside at least one other lab name
    """

    authors = [
        name_tokens(get_safe(a, "author.display_name", ""))
        for a in get_safe(work, "authorships", []) or []
    ]
    authors = [a for a in authors if a]

    if not any(names_match(a, lead_author) for a in authors):
        return False

    return any(
        names_match(a, member)
        for a in authors
        if not names_match(a, lead_author)
        for member in roster
        if not names_match(member, lead_author)
    )


def to_source(work):
    """
    convert an openalex work into a source to cite
    """

    # prefer a Manubot-citeable id, so Manubot can generate a full citation
    doi = get_safe(work, "doi", "") or ""
    if doi:
        # openalex returns dois as urls, and dois are case-insensitive
        return {"id": "doi:" + doi.replace("https://doi.org/", "").strip().lower()}

    pmid = get_safe(work, "ids.pmid", "") or ""
    if pmid:
        return {"id": "pubmed:" + pmid.strip().rstrip("/").split("/")[-1]}

    # no id Manubot can use, so keep the citation details openalex gave us
    source = {}

    title = get_safe(work, "display_name", "")
    if title:
        source["title"] = title

    authors = [
        get_safe(a, "author.display_name", "")
        for a in get_safe(work, "authorships", []) or []
    ]
    authors = [a for a in authors if a]
    if authors:
        source["authors"] = authors

    publisher = get_safe(work, "primary_location.source.display_name", "")
    if publisher:
        source["publisher"] = publisher

    date = get_safe(work, "publication_date", "")
    if date:
        source["date"] = format_date(date)

    link = (
        get_safe(work, "primary_location.landing_page_url", "")
        or get_safe(work, "best_oa_location.pdf_url", "")
        or get_safe(work, "id", "")
    )
    if link:
        source["link"] = link

    return source


def dedupe(works):
    """
    collapse preprint/published versions of the same work, keeping the best one
    """

    def key(work):
        # normalize title down to bare alphanumerics for comparison
        return re.sub(r"[^a-z0-9]", "", (get_safe(work, "display_name", "") or "").lower())

    def rank(work):
        # lower sorts first: prefer published over preprint, and having a doi
        return (
            1 if get_safe(work, "type", "") == "preprint" else 0,
            0 if get_safe(work, "doi", "") else 1,
        )

    groups = {}
    for work in works:
        _key = key(work)
        # can't compare untitled works, so always keep them
        if not _key:
            groups[get_safe(work, "id", "")] = work
            continue
        if _key not in groups or rank(work) < rank(groups[_key]):
            groups[_key] = work

    collapsed = len(works) - len(groups)
    if collapsed > 0:
        log(f"Collapsed {collapsed} duplicate preprint/published version(s)", indent=3)

    return list(groups.values())
