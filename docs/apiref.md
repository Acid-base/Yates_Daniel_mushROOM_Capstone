API Reference
Endpoints
The Mushroom App API provides the following endpoints:

/mushrooms: Get a list of all mushrooms.
/mushrooms/:id: Get a single mushroom by its ID.
/mushrooms/search: Search for mushrooms by name, description, or habitat.
Parameters
The following parameters are supported by the Mushroom App API:

id: The ID of the mushroom.
name: The name of the mushroom.
description: The description of the mushroom.
habitat: The habitat of the mushroom.
Responses
The Mushroom App API returns JSON responses. The following properties are included in the response body:

id: The ID of the mushroom.
name: The name of the mushroom.
description: The description of the mushroom.
habitat: The habitat of the mushroom.
edibility: The edibility of the mushroom.
toxicity: The toxicity of the mushroom.