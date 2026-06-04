# ONE Record Data Sharing

## Overview

ONE Record enables data sharing across the air cargo supply chain by treating
each business object as a web-addressable resource. Instead of exchanging flat
EDI messages, parties publish and link **logistics objects** that reference one
another, forming a connected graph of shipment data.

## Linked Data

Every logistics object has a stable URI (`@id`) and a type (`@type`) drawn from
the ONE Record ontology. Relationships between objects are expressed as links to
other URIs, so a Shipment can point to its Pieces, and a Piece can point back to
its Shipment, without duplicating data.

## Access Control and Subscriptions

Data owners expose objects through a ONE Record Server and control who may access
them. Interested parties create a Subscription to receive Notifications when an
object changes, enabling event-driven, near-real-time data sharing rather than
polling.
