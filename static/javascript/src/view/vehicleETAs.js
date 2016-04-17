define(["backbone", "underscore", "utils", "config", "templates"],
       function(B, _, $u, config, $t) {
           var StopVehiclesView = B.View.extend({
               initialize: function(options) {
                   options = options || {};
                   B.View.prototype.initialize.call(this, options);
                   this.app = options.app;

                   this.lastStamp = 0;

                   // Map of mode -> "0"/"1"
                   this.modeDirections = {bus: "1", subway: "1"};

                   // The route_ids associated with the stop should never
                   // change (we get a complete list from /routeinfo), so there
                   // should be no need to subscribe to route_id changes.
                   // this.listenTo(this.model, "change:route_ids",
                   // this._updateRoutes);
                   this.listenTo(this.app, "routeSelected",
                                 this._updateRoutes)
                       .listenTo(this.app, "routeUnselected",
                                 this._updateRoutes);
                   this._updateRoutes();
               },

               className: "vehicle-etas",

               events: {
                   "click .toggle-route": "toggleRoute",
                   "click a.all-on": "allOn",
                   "click a.change-dir": "changeDirection"
               },

               // TODO: Cache information about vehicle predictions, so that it
               // doesn't have to be recalculated once per sec.
               _updatePreds: function() {

               },

               /**
                * Store information about active and inactive routes every time
                * the route selection changes.
                */
               _updateRoutes: function() {
                   var routes =  this.app.routes,
                       self = this,
                       showSubways = false,
                       showBuses = false;

                   this._routes = _.map(this.model.get("route_ids"),
                                        function(__, route_id) {
                                            var route = routes.get(route_id);
                                            if (route) {
                                                if (routes.isSubwayRoute(route_id))
                                                    showSubways = true;
                                                else
                                                    showBuses = true;
                                            }

                                            return {
                                                id: route_id,
                                                active: !!route,
                                                shortName: routes.getRouteShortName(route_id),
                                                color: routes.getRouteColor(route_id)
                                            };
                                        });
                   this._showSubways = showSubways;
                   this._showBuses = showBuses;
               },

               // Redraw the view using the last stamp
               rerender: function() {
                   this._updateRoutes();
                   this.render(this.lastStamp);
               },

               render: function(stamp) {
                   if (!stamp) stamp = $u.stamp();

                   var stop = this.model,
                       dirs = this.modeDirections,
                       vehicles = this.app.vehicles,
                       routes = this.app.routes,
                       hasPreds = {},
                       preds;

                   var data = {
                       routes: this._routes,
                       name: stop.getName(),
                       modes: []
                   };
                   this.lastStamp = stamp;

                   // Collect all the predictions
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

                       if (pred.arr_time > threshold ||
                           pred.arr_time < stamp) return;

                       hasPreds[route_id] = true;

                       // Ignore disabled routes:
                       if (!routes.get(route_id))
                           return;

                       var subway = config.subwayPattern.exec(route_id),
                           key = subway ? "subway" : "bus";

                       // Ignore vehicles traveling in the wrong direction:
                       if (dirs[key] !== pred.direction) return;
                       pred.color = routes.getRouteColor(pred.route_id);
                       pred.briefRelTime = $u.briefRelTime(pred.arr_time - stamp);
                       pred.name = routes.getRouteShortName(pred.route_id);

                       $u.insertSorted(groupedPreds[key], pred, cmp);
                       $u.briefRelTime();
                   });

                   _.each(this._routes, function(route) {
                       route.hasPredictions = hasPreds[route.id];
                   });

                   if (this._showSubways)
                       data.modes.push({
                           name: "Subway Routes",
                           preds: groupedPreds.subway});
                   if (this._showBuses)
                       data.modes.push({
                           name: "Bus Routes",
                           preds: groupedPreds.bus});

                   var $el = this.$el;
                   $t.render("vehicleETAs", data)
                       .then(function(html) {
                           $el.html(html);
                       });

                   return this;
               },

               changeDirection: function(e) {
                   var mode = $(e.target).data("mode"),
                       dir = this.modeDirections[mode];

                   this.modeDirections[mode] = dir == "1" ? "0" : "1";
                   this.rerender();
                   e.preventDefault();
               },

               showRoute: function(e) {
                   var route_id = $(e.target).data("route");
                   this.app.addRoute(route_id);
                   // Since the route information won't be instantly
                   // available, don't bother re-rendering right away.
                   e.preventDefault();
               },

               toggleRoute: function(e) {
                   var route_id = $(e.target).attr("data-route_id");

                   if (route_id) {
                       this.app.toggleRoute(route_id);
                       this.rerender();
                   }

                   e.preventDefault();
               },

               hideRoute: function(e) {
                   var route_id = $(e.target).closest(".vehicle-pred")
                           .data("route");

                   if (route_id) {
                       this.app.toggleRoute(route_id);
                       this.rerender();
                   }

                   e.preventDefault();
               },

               allOn: function(e) {
                   var ids = $(e.target).data("routes").split(","),
                       app = this.app;

                   _.each(ids, function(id) {
                       app.addRoute(id);
                   });
                   e.preventDefault();
               }
           });

           return StopVehiclesView;
       });