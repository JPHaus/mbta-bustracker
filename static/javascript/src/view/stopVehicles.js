define(["backbone", "underscore", "utils", "config"],
       function(B, _, $u, config) {
           var StopVehiclesView = B.View.extend({
               initialize: function(options) {
                   options = options || {};
                   B.View.prototype.initialize.call(this, options);
                   this.popup = options.popup;
                   this.app = options.app;

                   // this.listenTo(this.model, "childAdded", this.updatePreds)
                   //     .listenTo(this.model, "childRemoved", kVj)
                   this.lastStamp = 0;

                   // Map of route id -> "0"/"1"; determines whether the view
                   // will show predictions for vehicles with direction 0 or
                   // direction 1.
                   this.routeDirections = {};
                   // Map of route_id -> true, where true indicates that a route
                   // is toggled OFF.
                   this.routeToggles = {};

                   this.popup.setContent(this.el);
               },

               events: {
                   "click": "onClick"
               },

               // TODO: Cache information about vehicle predictions, so that it
               // doesn't have to be recalculated every frame.
               _updatePreds: function() {

               },

               render: function(stamp) {
                   if (!stamp) stamp = $u.stamp();

                   var stop = this.model,
                       dirs = this.routeDirections,
                       off = this.routeToggles,
                       html = ["<div class='stop-name'>",
                               _.escape(stop.getName()),
                               "</div>Next Vehicles ETA<hr>"],
                       vehicles = this.app.vehicles,
                       routes = this.app.routes,
                       preds;

                   this.lastStamp = stamp;

                   if (stop.isParent()) {
                       preds = $u.mapcat(stop.getChildren(),
                                         function(stop) {
                                             return stop.get("preds") || [];
                                         });
                   } else {
                       preds = stop.get("preds");
                   }

                   var groupedPreds = {
                       bus: [],
                       subway: []
                   },
                       groupNames = {bus: "Bus Routes",
                                     subway: "Subway Routes"},
                       // Ignore predictions more than 30 minutes in the future:
                       threshold = stamp + 1800000,
                       // Limit number of predictions shown:
                       max = Infinity,
                       cmp = function(predA, predB) {
                           var diff = predA.arr_time - predB.arr_time;

                           return diff < 0 ? -1 : diff > 0 ? 1 : 0;
                       };

                   _.each(preds, function(pred) {
                       var route_id = pred.route_id;

                       if (pred.arr_time > threshold) return;
                       // Ignore disabled routes:
                       if (off[route_id]) return;
                       // And vehicles going in the wrong direction:
                       if (dirs[route_id] &&
                           pred.direction !== dirs[route_id]) return;

                       var subway = config.subwayPattern.exec(route_id),
                           key = subway ? "subway" : "bus";

                       $u.insertSorted(groupedPreds[key], pred, cmp);
                   });

                   _.each(groupedPreds, function(group, gk) {
                       if (!group.length) return;

                       html.push("<div class='mode-head'>" +
                                 groupNames[gk] + "</div>");

                       _.each(group, function(pred) {
                           var route_id = pred.route_id,
                               dir = dirs[route_id] || "0",
                               dt = pred.arr_time - stamp;

                           if (pred.direction !== dir || dt <= 0)
                               return;

                           var route = routes.get(route_id),
                               color = route ? route.getColor() : "#aaa";
                           html.push(
                               "<div class='vehicle-pred' data-route='",
                               route_id, "'><a class='swatch' ",
                               "style='background-color:",
                               color, "'></a> <span class='route-name'>",
                               _.escape(pred.destination),
                               "</span> <div class='pred-time'>",
                               $u.briefRelTime(dt), "</div>");
                       });
                   });

                   if (!_.isEmpty(off)) {
                       html.push("<div class='route-toggles'>");
                       // Show links to toggle routes on:
                       _.each(off, function(_nada, route_id) {
                           html.push("<a href='#' data-route='",
                                     route_id, "' class='show-route-vehicles'>",
                                     _.escape(route_id), "</a>");
                       });
                   }

                   this.$el.html(html.join(""));

                   return this;
               },

               onClick: function(e) {
                   // Toggle a route to show outbound/inbound
                   var t = $(e.target), route_id;

                   if (t.is(".show-route-vehicles")) {
                       route_id = t.data("route");
                       delete this.routeToggles[route_id];
                       e.preventDefault();
                       return false;
                   }

                   route_id = t.closest(".vehicle-pred").data("route");

                   if (!route_id) return true;

                   if (t.is("a.swatch")) {
                       // Toggle the route on or off when the user clicks the
                       // swatch:
                       //this.app.toggleRoute(route_id);
                       this.routeToggles[route_id] = true;
                   } else {

                   }

                   e.preventDefault();

                   return false;
               }
           });

           return StopVehiclesView;
       });