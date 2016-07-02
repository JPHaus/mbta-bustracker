define(["backbone", "utils", "leaflet", "path-utils"],
       function(B, $u, L, $p) {
           var VehicleModel = B.Model.extend({
               defaults: {
                   _selected: false
               },

               getRoute: function() {
                   var route_id = this.get("route_id");
                   return this.collection.app.routes.get(route_id);
               },

               getLatLng: function() {
                   return L.latLng(this.get("lat"), this.get("lon"));
               },

               summary: function() {
                   var vehicle = this.attributes;

                   return ["vehicle id: ", vehicle.id, "<br/> ",
                           vehicle.type == "subway" ? vehicle.route :
                           ((vehicle.direction == "1" ? "Inbound " : "Outbound ") + "Route " + vehicle.route),
                           vehicle.type,
                           "heading",
                           $u.readableHeading(vehicle.heading),
                           "toward",
                           vehicle.destination
                          ].join(" ");
               },

               /**
                * Calculates the vehicle's current position and rotation (in
                * radians) based on the vehicle's timepoints array.
                */
               getCurrentPosition: function(stamp) {
                   if (!stamp) stamp = $u.stamp();

                   var attrs = this.attributes,
                       pos = $p.calculateTimepointPosition(attrs.timepoints, stamp);

                   return [pos[0] || L.latLng(attrs.lat, attrs.lon),
                           pos[1] || $u.headingToRads(attrs.heading)];

               }
           });

           return VehicleModel;
       });
