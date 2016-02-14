define([], function() {
    var $u = {
        directions: ["north", "northeast", "east", "southeast",
                     "south", "southwest", "west", "northwest",
                     "north"],
        directionsShort: ["N", "NE", "E", "SE", "S", "SW", "W", "NW", "N"],
        
        readableHeading: function(heading) {
            return this.directions[Math.round(heading%360/45)];
        },

        readableHeadingShort: function(heading) {
            return this.directionsShort[Math.round(heading%360/45)];
        },

        makeTransformFn: null,

        vehicleSummary: function(vehicle) {
            return [
                "An",
                vehicle["direction"] == "1" ? "outbound" : "inbound",
                vehicle["type"] == "subway" ? vehicle["route"] :
                    ("Route " + vehicle["route"]),
                vehicle["type"],
                "heading",
                $u.readableHeading(vehicle["heading"]),
                "toward",
                vehicle["destination"]
            ].join(" ");
        }
    };

    return $u;
});