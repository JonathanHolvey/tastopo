# TasTopo

*Generate printable topographic maps for anywhere in Tasmania.*

The Tasmanian Government's [ListMap service](https://maps.thelist.tas.gov.au) provides an online map viewer that can display a wealth of publicly accessible geospatial data covering the whole of Tasmania. It allows users to generate maps as printable PDFs, but lacks fine-grained controls.

TasTopo is a command-line tool that provides an alternative way to create printable maps using ListMap data. It uses the ListMap ArcGIS API to fetch an image of the map area required, before wrapping it in a minimal SVG template and exporting it as a PDF file.

![Example map](./example.svg)

## Features

- Location searchable by name or geo URI
- Continuously variable scale ratio
- Dynamic sheet sizing from A5 to A0
- Landscape or portrait orientation
- Minimal design to maximise map area
- SVG and PDF export formats
- Enhanced hillshade overlay

## Installation

TasTopo requires Python 3 and can be installed using Pip:

```bash
python3 -m pip install tastopo
```

## Usage

```
tastopo generate [options] <location>
```

To generate a map, provide either the name of a place, or its coordinates as a [geo URI](https://en.wikipedia.org/wiki/Geo_URI_scheme) for the `<location>` argument, as well as any options required. Valid locations include:

- `kettering`
- `'kunyani / Mount Wellington'`
- `'geo:-43.643611,146.8275'`

### Layout options

- `--scale`: Specify the scale of the printed map (defaults to 25000)
- `--title`: Set the title on the map sheet, instead of the location name
- `--paper`: Specify the paper size for printing (defaults to A4)
- `--portrait`: Orientate the map in portrait, rather than landscape

For details of all the available options run `tastopo --help`.

### Example

A PDF version of the the map image shown above can be generated using the following command:

```bash
tastopo generate --paper a5 --scale 28000 kettering
```

## License and copyright

TasTopo is released under the [MIT license](./LICENSE.txt).

Mapping data is sourced from Land Tasmania's ListMap service, under the Creative Commons 3.0 Australia license. Topographic and hillshade grey map layers from www.thelist.tas.gov.au &copy; State of Tasmania.
