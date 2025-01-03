import numpy as np


def ObjFun(position, UAV):
    path = np.vstack((UAV["S"], position.reshape(-1, UAV["PointDim"]), UAV["G"]))

    # Calculate total distance
    distances = np.linalg.norm(path[1:] - path[:-1], axis=1)
    total_distance = np.sum(distances)

    # Check for collisions
    # NOTE: calculate the number of points inside the no-fly zones
    # collision_penalty = check_collisions(path, UAV["NoFlyZones"])

    # NOTE: calculate the distance of points inside the no-fly zones
    collision_penalty = calculate_no_fly_zones_distance(path, UAV["NoFlyZones"])

    # Objective function: heavily penalize collisions, but prioritize distance minimization
    # NOTE: not calculate the height penalty
    w1 = 0.2
    w2 = 100
    fitness = w1 * total_distance + w2 * collision_penalty
    return fitness


def calculate_no_fly_zones_distance(path, no_fly_zones):
    # check collisions
    result = 0
    for point in path:
        for zone in no_fly_zones:
            _is, distance = is_point_in_no_fly_zone(point, zone)
            if _is:
                result += distance
            # result += distance # distance whit all no fly zones
    return result


def is_point_in_no_fly_zone(point, zone):
    distance_threshold = 0.2  # setting safe distance with the no fly zone
    x, y, height, radius = zone
    center = np.array([x, y, 0])  # Cylinder base center

    # Calculate distance from point to cylinder center in XY plane
    distance_xy = np.linalg.norm(point[:2] - center[:2])

    # Check if point is within cylinder radius and height
    safe_distance = radius + distance_threshold
    if distance_xy <= safe_distance and 0 <= point[2] <= height:
        return True, distance_xy  # inside
    return False, distance_xy  # outside


def check_collisions(path, no_fly_zones):
    collision_count = 0
    for i in range(len(path) - 1):
        start = path[i]
        end = path[i + 1]
        for zone in no_fly_zones:
            if line_cylinder_intersection(start, end, zone):
                collision_count += 1
                break  # Count only one collision per path segment
    return collision_count


def line_cylinder_intersection(start, end, cylinder):
    x, y, height, radius = cylinder
    center = np.array([x, y, 0])  # Cylinder base center

    # Vector from start to end
    d = end - start

    # Vector from cylinder base center to start point
    f = start - center

    # Coefficients of quadratic equation
    a = np.dot(d[:2], d[:2])
    b = 2 * np.dot(f[:2], d[:2])
    c = np.dot(f[:2], f[:2]) - radius**2

    # Handle case where line is (nearly) vertical in XY plane
    if abs(a) < 1e-6:
        # Check if the line is within the cylinder's radius
        if c <= 0:
            # Line is inside the cylinder, check if it's within the height
            z_min = min(start[2], end[2])
            z_max = max(start[2], end[2])
            if z_min <= height and z_max >= 0:
                return True
        return False

    discriminant = b**2 - 4 * a * c

    if discriminant < 0:
        # No intersection with the infinite cylinder
        return False

    # Calculate the two intersection points with the infinite cylinder
    sqrt_disc = np.sqrt(discriminant)
    t1 = (-b + sqrt_disc) / (2 * a)
    t2 = (-b - sqrt_disc) / (2 * a)

    # Check if intersection points are within the line segment
    if not (0 <= t1 <= 1 or 0 <= t2 <= 1):
        return False

    # Calculate the z-coordinates of the intersection points
    z1 = start[2] + t1 * d[2]
    z2 = start[2] + t2 * d[2]

    # Check if either intersection point is within the cylinder's height
    epsilon = 1e-6  # Small tolerance value
    if (-epsilon <= z1 <= height + epsilon) or (-epsilon <= z2 <= height + epsilon):
        return True

    # Check for intersection with top and bottom faces
    if d[2] != 0:
        t_bottom = -start[2] / d[2]
        t_top = (height - start[2]) / d[2]

        if 0 <= t_bottom <= 1:
            point = start + t_bottom * d
            if np.linalg.norm(point[:2] - center[:2]) <= radius:
                return True

        if 0 <= t_top <= 1:
            point = start + t_top * d
            if np.linalg.norm(point[:2] - center[:2]) <= radius:
                return True

    return False
