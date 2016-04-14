define([], function() {
    return {
        defaultRoutes: [],
        defaultRouteStyle: {
            opacity: 0.5,
            weight: 4
        },
        // If the route_id matches this pattern, the route is considered a
        // subway:
        subwayPattern: /^Red|Orange|Green-|Blue|Mattapan/,
        routeStyles: {
            "Red": {color: "red"},
            "Orange": {color: "orange"},
            "Green-B": {color: "green",
                    opacity: 0.2},
            "Green-C": {color: "green",
                    opacity: 0.2},
            "Green-D": {color: "green",
                    opacity: 0.2},
            "Green-E": {color: "green",
                    opacity: 0.2},
            "Blue": {color: "blue"}
        },
        routeNicknames: {
            "Red": "Red",
            "Blue": "Blue",
            "Orange": "Orange",
            "Green-B": "B",
            "Green-C": "C",
            "Green-D": "D",
            "Green-E": "E",
            "Mattapan": "MT",
            // Silver Line Waterfront
            "746": "SLW"
        },
        colors: ["salmon", "#6CB31B", "teal", "gold", "orchid", "darkgoldenrod", "deepskyblue", "deeppink", "sienna", "burlywood"]
    };
});
