define(["jquery", "utils"], function($, $u) {
    var defaultOptions = {
        tickInterval: 100
    };

    /**
     * @param {Object} [options]
     * @param {number} options.tickInterval The delay between updates
     */
    function Animation(options) {
        if (!this instanceof Animation)
            return new Animation(options);

        this.options = $.extend(defaultOptions, options);
        this.objects = [];

        return this;
    };

    $.extend(Animation.prototype, {
        addObject: function(object) {
            this.objects.push(object);
        },

        removeObject: function(object) {
            var idx = this.objects.indexOf(object);

            if (idx > -1) {
                this.objects.splice(idx, 1);
            }
        },

        _lastRun: 0,
        _ticks: 0,

        runTick: function() {
            var now = new Date().getTime(),
                dt = now - this._lastRun;
            $.each(this.objects, function(i, thing) {
                thing.tick(dt, now);
            });
            this._lastRun = now;
            this._ticks++;
        },

        start: function() {
            this._lastRun = new Date().getTime();

            this._interval = setInterval($u.bind(this.runTick, this),
                                         this.options.tickInterval);
        },

        stop: function() {
            return clearInterval(this._interval);
        }
    });

    return Animation;
});