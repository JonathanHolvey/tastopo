def centroid(points):
    """Calculate the centroid of a polygon defined by a list of vertex coordinates.
    Formula from Bourke (1997) http://paulbourke.net/geometry/polygonmesh"""
    p = points
    index = range(len(points) - 1)
    # Calculate the area, then coordinates of the centroid
    a = sum(p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1] for i in index) / 2
    x = sum((p[i][0] + p[i + 1][0]) * (p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1]) for i in index) / (6 * a)
    y = sum((p[i][1] + p[i + 1][1]) * (p[i][0] * p[i + 1][1] - p[i + 1][0] * p[i][1]) for i in index) / (6 * a)

    return x, y
