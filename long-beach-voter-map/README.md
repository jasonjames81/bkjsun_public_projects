# Long Beach Voter Map

A single-page interactive voter map for Long Beach. Each census block group is
shaded by Democratic minus Republican margin, measured either on registration or
on who actually voted.

Covers two elections, selectable in the map:

| | Registered | Voted | Turnout |
|---|---|---|---|
| **2024 General** | 271,988 | 172,611 | 63.5% |
| **2026 Primary** | 279,984 | 105,934 | 37.8% |

A primary and a general are not comparable turnout populations, so the two are
separate views rather than one overwriting the other.

**[View the live map →](https://jasonjames81.github.io/bkjsun_public_projects/long-beach-voter-map/)**

Data: [Statewide Database](https://statewidedatabase.org/election.html) (UC
Berkeley), Los Angeles County (037), by 2020 census block, aggregated to block
group. Built with `generate_map_v5.py`.
