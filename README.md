# \# WellsWatch

# 

# WellsWatch is a Python library for accessing groundwater-status predictions published on Zenodo and visualizing red and non-red monitoring wells across Greece.

# 

# !\[WellsWatch groundwater status map](docs/wellswatch\_2025.png)

# 

# \## Main features

# 

# \* Retrieve groundwater-status predictions directly from Zenodo.

# \* Select prediction data by year and date.

# \* Display red and non-red monitoring wells on a map of Greece.

# \* Save the generated map as a high-resolution image.

# \* Load prediction files locally from Excel or CSV.

# 

# \## Installation

# 

# ```bash

# pip install wellswatch

# ```

# 

# \## Quick start

# 

# ```python

# from wellswatch import show\_map

# 

# show\_map(2025)

# ```

# 

# This retrieves the corresponding prediction file from Zenodo and displays the wells on a map of Greece.

# 

# \## Save a map

# 

# ```python

# from wellswatch import show\_map

# 

# show\_map(

# &#x20;   2025,

# &#x20;   save\_path="wellswatch\_2025.png",

# )

# ```

# 

# \## Load prediction data from Zenodo

# 

# ```python

# from wellswatch import load\_prediction\_from\_zenodo

# 

# data = load\_prediction\_from\_zenodo(2025)

# 

# print(data.head())

# print(data\["realtime\_pred\_class\_name"].value\_counts())

# ```

# 

# \## Load a local prediction file

# 

# ```python

# from wellswatch import load\_prediction\_file

# 

# data = load\_prediction\_file(

# &#x20;   "pred\_2025\_08\_01\_with\_predictions\_01.xlsx"

# )

# ```

# 

# \## Expected columns

# 

# Prediction files must contain:

# 

# \* `row\_id`

# \* `station\_code`

# \* `lon`

# \* `lat`

# \* `realtime\_pred\_class\_name`

# \* `realtime\_pred\_red\_probability`

# 

# The prediction date is extracted automatically from the filename.

# 

# \## Data source

# 

# The groundwater-status prediction files are publicly available through Zenodo record `20427364`.

# 

# \## License

# 

# WellsWatch is distributed under the MIT License.

# 

