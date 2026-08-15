---
title: Team
nav:
  order: 3
  tooltip: About our team
---

{% comment %}
  every photo in images/outings is picked up automatically, so adding one to
  that folder is all it takes to put it in the strip. the duration scales with
  the number of photos so the band always drifts at the same speed
{% endcomment %}
{% assign outings = site.static_files | where_exp: "file", "file.path contains '/images/outings/'" | sort: "path" %}
{% if outings.size > 0 %}

{% include section.html size="full" %}

<div class="outings" role="group" aria-label="Photos from lab outings and retreats" style="--outings-duration: {{ outings.size | times: 8 }}s">
  <div class="outings-track">
    {% for photo in outings %}
      <img src="{{ photo.path | relative_url }}" alt="Lab outing">
    {% endfor %}
    {% comment %} second copy makes the loop seamless; hidden from screen readers {% endcomment %}
    {% for photo in outings %}
      <img src="{{ photo.path | relative_url }}" alt="" aria-hidden="true">
    {% endfor %}
  </div>
</div>

{% include section.html %}

{% endif %}

# Team


## Faculty, Postdocs, and PhD Students

<div class="team-grid-wrapper">
  <div class="team-grid">

    {% assign faculty = site.members | where: "role", "Faculty" | sort: "lastname" %}
    {% assign postdocs = site.members | where: "role", "Postdoc" | sort: "lastname" %}
    {% assign students = site.members | where_exp: "item", "item.role != 'Faculty' and item.role != 'Postdoc' and item.role != 'Undergrad' and item.role != 'alumni'" | sort: "lastname" %}
    {% assign team = faculty | concat: postdocs | concat: students %}

    {% for member in team %}
      {% include portrait.html 
        name=member.name
        role=member.role
        image=member.image
        research=member.research
        links=member.links
      %}
    {% endfor %}

  </div>
</div>


{% assign undergrads = site.members | where: "role", "Undergrad" %}
{% if undergrads.size > 0 %}

## Undergrad Students

<div class="team-grid-wrapper">
  {% include list.html data="members" component="portrait" filter="role == 'Undergrad'" grid=true %}
</div>

{% endif %}

## Alumni

{% assign senior = site.data.alumni | where_exp: "item", "item.degree == 'Postdoc' or item.degree == 'PhD'" %}
{% assign junior = site.data.alumni | where_exp: "item", "item.degree == 'MS' or item.degree == 'Undergrad'" %}
{% comment %}
  anything with a missing or unrecognised degree, so that adding an entry
  without one lists them here rather than dropping them off the page
{% endcomment %}
{% assign other = site.data.alumni | where_exp: "item", "item.degree != 'Postdoc' and item.degree != 'PhD' and item.degree != 'MS' and item.degree != 'Undergrad'" %}

{% if senior.size > 0 %}

### Postdocs and PhD Students
{:.center}

<ul class="alumni-list">
  {% for alumni in senior %}
    <li>{{ alumni.name }}</li>
  {% endfor %}
</ul>

{% endif %}

{% if junior.size > 0 %}

### Masters and Undergraduates
{:.center}

<ul class="alumni-list">
  {% for alumni in junior %}
    <li>{{ alumni.name }}</li>
  {% endfor %}
</ul>

{% endif %}

{% if other.size > 0 %}

<ul class="alumni-list">
  {% for alumni in other %}
    <li>{{ alumni.name }}</li>
  {% endfor %}
</ul>

{% endif %}

