odoo.define('web_kanban_graph.widget', function (require) {
		"use strict";
		var AbstractField = require('web.AbstractField');
		var field_registry = require('web.field_registry');
		var utils = require('web.utils');
/**
 * Kanban widgets: Graph
 * Bar Chart
 */
var KanbanGraphWidget = AbstractField.extend({
    className: "o_kanban_bar_graph",
    cssLibs: [
        '/web/static/lib/nvd3/nv.d3.css'
    ],
    jsLibs: [
        '/web/static/lib/nvd3/d3.v3.js',
        '/web/static/lib/nvd3/nv.d3.js',
        '/web/static/src/js/libs/nvd3.js'
    ],
    start: function() {
        var self = this;
        var field_value = JSON.parse(self.value);
        var id_dict = _.pluck(field_value, 'id');
        nv.utils.windowResize(this._onResize);
        this.$el.append($("<svg id='chart_"+id_dict+"' class='oe_graph'>"));
        this.svg = '#chart_'+id_dict;
        self.bar(field_value);
    },
    bar: function (data) {
        var self = this;
        nv.addGraph(function () {
        	var xlabels = [],
            series = [],
            label, serie, value;
        var values = {};
        for (var i = 0; i < data[0]['values'].length; i++) {
            label = data[0]['values'][i].labels[0];
            serie = data[0]['values'][i].labels[1];
            value = data[0]['values'][i].value;
            if ((!xlabels.length) || (xlabels[xlabels.length-1] !== label)) {
                xlabels.push(label);
            }
            series.push(data[0]['values'][i].labels[1]);
            if (!(serie in values)) {values[serie] = {};}
            values[serie][label] = data[0]['values'][i].value;
        }
        series = _.uniq(series);
        data = [];
        var current_serie, j;
        for (i = 0; i < series.length; i++) {
            current_serie = {values: [], key: series[i]};
            for (j = 0; j < xlabels.length; j++) {
                current_serie.values.push({
                    x: xlabels[j],
                    y: values[series[i]][xlabels[j]] || 0,
                });
            }
            data.push(current_serie);
        }
        var chart = nv.models.multiBarChart()
            .color(['#0039e6', '#ff3333', '#FA8072']);

        chart.options({
          margin: {left: 83, bottom: 50, top: 10, right: 0},
          delay: 100,
          transition: 10,
          showLegend: true,
          showXAxis: true,
          showYAxis: true,
          rightAlignYAxis: false,
          stacked: false,
          reduceXTicks: false,
          rotateLabels: -20,
          showControls: false
        });
        chart.yAxis.tickFormat(d3.format('.2f'));
        d3.select(self.svg)
                .datum(data)
                .call(chart);
            nv.utils.windowResize(chart.update);
            return chart;
        });
    },
});
field_registry.add("kanban_graph", KanbanGraphWidget);


/**
 * Kanban widgets: Graph
 * Line Chart
 */
var KanbanLineGraphWidget = AbstractField.extend({
    className: "o_kanban_line_graph",
    cssLibs: [
        '/web/static/lib/nvd3/nv.d3.css'
    ],
    jsLibs: [
        '/web/static/lib/nvd3/d3.v3.js',
        '/web/static/lib/nvd3/nv.d3.js',
        '/web/static/src/js/libs/nvd3.js'
    ],
    start: function() {
        var self = this;
        var field_value = JSON.parse(self.value);
        var id_dict = _.pluck(field_value, 'id');
        nv.utils.windowResize(this._onResize);
        this.$el.append($("<svg id='chart_line"+id_dict+"' class='oe_graph'>"));
        this.svg = '#chart_line'+id_dict;
        self.line(field_value);
    },
    line: function (data) {
        var self = this;
        nv.addGraph(function () {
        	var line_data = [];
            var data_dict = {};
            var tick = -1;
            var tickLabels = [];
            var serie, tickLabel;
            var identity = function (p) {return p;};
            var tickValues = [];
            var tickFormat;
            for (var i = 0; i < data[0]['values'].length; i++) {
                if (data[0]['values'][i].labels[0] !== tickLabel) {
                    tickLabel = data[0]['values'][i].labels[0];
                    tickValues.push(tick);
                    tickLabels.push(tickLabel);
                    tick++;
                }
                serie = data[0]['values'][i].labels[1];
                if (!data_dict[serie]) {
                    data_dict[serie] = {
                        values: [],
                        key: serie,
                    };
                }
                data_dict[serie].values.push({
                    x: tick, y: data[0]['values'][i].value,
                });
                line_data = _.map(data_dict, identity);
            }
            tickFormat = function (d) {return tickLabels[d];};
            data = line_data;

            var chart = nv.models.lineChart()
            .color(['#0039e6', '#ff3333', '#FA8072']);

            chart.options({
	          margin: {left: 60, bottom: 50, top: 10, right: 0},
	          useInteractiveGuideline: true,
	          showLegend: true,
	          showXAxis: true,
	          showYAxis: true
	        });

            chart.xAxis.tickValues(tickValues)
            .tickFormat(tickFormat)
            .rotateLabels(-20);
            chart.yAxis.tickFormat(d3.format('.2%'));

            d3.select(self.svg)
                .datum(data)
                .call(chart);
            nv.utils.windowResize(chart.update);
            return chart;
        });
    },
});
field_registry.add("kanban_line_graph", KanbanLineGraphWidget);

});
