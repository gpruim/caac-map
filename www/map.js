Map = {};

Map.init = function() {
    $('body').load('map.svg', function() {
        $('svg').svg();
        var svg = $('svg').svg('get');

        $('rect').attr('fill', '#0099FF');

        $('#456').attr('fill', '#025127');
        $('#567').attr('class', 'selected'); // .addClass doesn't work for whatever reason
    });
};