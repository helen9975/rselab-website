---
title: Team
nav:
  order: 3
  tooltip: About our team
---

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

