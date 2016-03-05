/*
* @Author: Stefan Lehmann
* @Date:   2016
* @Last Modified by:   Stefan Lehmann
* @Last Modified time: 2016
*/

var socket = null
var curent_data = null;

var data = {
  'time': [],
  'temp': [],
  'setpoint': [],
  'power': []
};


// function relayout_graph() {
//   var small = $(window).width() < 700;
//     if (small) {
//         var update = {margin: {t: 50, l: 30, r: 0, b: 80}};
//     }
//     else {
//         var update = {margin: {t: 50, l: 50, r: 50, b: 50}};
//     }
//     Plotly.relayout(graph, update);
//   };


// Setpoint handling
$(document).ready(function() {

  // show setpoint ok and cancel button when user change setpoint
  $('#setpoint').keydown(function() {
    $('#setpoint-cancel').fadeIn('slow');
  });

  // cancel user input
  $('#setpoint-cancel').click(function() {
    $('#setpoint').val(current_data.temp_setpoint);
    $(this).fadeOut('slow');
  });
});


$(document).ready(function() {
  // Socket data
  socket = io.connect('http://' + document.domain + ':' + location.port);

  // diagram init
  var graph = $('#graph').get(0);
  var graph_data = {{ graph_data | tojson }}

  data.time = graph_data.time;
  data.temp = graph_data.temp;
  data.setpoint = graph_data.temp_setpoint;
  data.power = graph_data.power;

  var trace_temp = {
    x: data.time,
    y: data.temp,
    name: "Temperatur"
  };

  var trace_setpoint = {
    x: data.time,
    y: data.setpoint,
    name: "Sollwert"
  };

  var trace_power = {
    x: data.time,
    y: data.power,
    opacity: 0.3,
    name: "Heizleistung"
  };

  // init plot

  var layout = {
    margin: {
        l: 60,
        r: 0,
        b: 50,
        t: 0,
        pad: 4
    },
    height: 400,
    yaxis: {
      title: '°C',
      range: [0, 100]
    },
    legend: {
      x: 0.02,
      y: 1.02,
      traceorder: 'normal',
      font: {
        family: 'sans-serif',
        size: 12,
        color: '#000'
      },
      bordercolor: '#FFFFFF',
      borderwidth: 2
    }
  };

  Plotly.plot(
    graph,
    [trace_temp, trace_setpoint, trace_power],
    layout,
    {
      displayModeBar: false,
      staticPlot: true
    }
  );

  // socket action
  socket.on('process_data', function(curr_data) {

    current_data = curr_data;

    // Add data to graph
    data.time.push(curr_data.time);
    data.temp.push(curr_data.temp);
    data.setpoint.push(curr_data.temp_setpoint);
    data.power.push(curr_data.power)

    Plotly.redraw(graph);

    // Show current Temp in gauge
    $('#power').text(curr_data.power.toFixed(0) + "%")
    $('#gauge').jqxLinearGauge('value', curr_data.temp);
  });

  // reset graph button
  $('#btn-reset-graph').click(function() {
    socket.emit('reset_graph');
    $.each(data, function(index, item) {
      item.length = 0;
    });

    Plotly.redraw(graph);
  });

  // resize plotly with window
  $(window).resize(function() {
    Plotly.Plots.resize(graph);
  });

  // image size and gauge initialisation
  $('#img-animation').one('load', function() {
    var width = $('#img-animation').width();
    var height = $('#img-animation').height();

    // gauge init
    $('#gauge').jqxLinearGauge({
        max: 100,
        min: 0,
        background: { visible: false},
        pointer: { size: '5%' },
        colorScheme: 'scheme03',
        ticksMajor: { size: '10%', interval: 10 },
        ticksMinor: { size: '5%', interval: 2.5, style: { 'stroke-width': 1, stroke: '#aaaaaa'} },
        value: 0,
        width: 70,
        height: height,
        labels: { interval: 10, formatValue: function (value, position) {
          if (position === 'far') {
              return value;
          }
          else if (position === 'near') {
            if (value == 100) {
                return '°C';
            }
          }
        },
        ranges: [
          { startValue: 20, endValue: 45, style: { fill: '#FFA200', stroke: '#FFA200' }}
        ],
        showRanges: true
      }
    });

    // gauge position
    $('#gauge').css('top', 0 + 'px');
    $('#gauge').css('left', width + 'px');

    // position of power label
    $('#power').css('top', (height / 2.4) + 'px');
    $('#power').css('left', (width / 3.0) + 'px');
  }).each(function() {
      if(this.complete) {
        $(this).load();
      }
  });
});