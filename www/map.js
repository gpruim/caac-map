Map = {};

Map.init = function() {
    $('body').load('map.svg', function() {
        $('svg').svg();
        var svg = $('svg').svg('get');
    });
};
