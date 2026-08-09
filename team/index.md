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

    {% assign faculty = site.members | where: "role", "Faculty" %}
    {% assign students = site.members | where_exp: "item", "item.role != 'Faculty' and item.role != 'Undergrad' and item.role != 'alumni'" | sort: "lastname" %}
    {% assign team = faculty | concat: students %}

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


## Undergrad Students

<div class="team-grid-wrapper">
  {% include list.html data="members" component="portrait" filter="role == 'Undergrad'" grid=true %}
</div>

## Alumni

<ul class="alumni-list">
  {% for alumni in site.data.alumni %}
    <li>{{ alumni.name }}</li>
  {% endfor %}
</ul>

